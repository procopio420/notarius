from uuid import uuid4
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from apps.processos.ficha import TOKEN
from apps.processos.modelo_referencia import BASE_REFERENCIA as BASE_FIEL, BASE_REFERENCIA_V3 as BASE_REFERENCIA
from apps.processos.models import Atendimento, ModeloAtendimento, RevisaoDadoAtendimento
from tests import test_atendimentos as helpers

class ModeloReferenciaTests(APITestCase):
    setUp = helpers.AtendimentoTests.setUp
    create_case = helpers.AtendimentoTests.create_case
    ready_for_draft = helpers.AtendimentoTests.ready_for_draft
    report = helpers.AtendimentoTests.report
    answer = helpers.AtendimentoTests.answer
    save_template = helpers.AtendimentoTests.save_template
    generate_draft = helpers.AtendimentoTests.generate_draft

    def select_reference(self, case, approved=False, expected=0):
        return self.save_template(case, approved=approved, expected=expected, **BASE_REFERENCIA)

    def fill_reference(self, case):
        for key in TOKEN.findall(BASE_REFERENCIA['corpo']):
            if any(q['chave'] == key for q in self.report(case)['pendencias']):
                response, _ = self.answer(case, key, f'TEXTO FICTÍCIO CONFERIDO PARA {key}')
                self.assertEqual(response.status_code, 201)

    def test_reference_is_available_without_writing_or_inheriting_approval(self):
        case = self.create_case()
        response = self.client.get(f'/api/v1/atendimentos/{case}/modelo-minuta/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['referencia']['modelo'], BASE_FIEL)
        self.assertFalse(response.data['referencia']['aprovado'])
        self.assertTrue(all(s['leitura'] and s['trecho'] for s in response.data['referencia']['fontes']))
        self.assertEqual([s['pagina'] for s in response.data['referencia']['fontes']], [1, 2, 3, 4])
        self.assertFalse(ModeloAtendimento.objects.exists())
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        hidden = Atendimento.objects.create(tenant=self.other, criado_por=self.user, titulo='Outro')
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{hidden.id}/modelo-minuta/').status_code, 404)

    def test_assisted_reference_replaces_values_and_keeps_statements_pending(self):
        from collections import defaultdict
        from apps.processos.minuta_assistida import MARCADOR, adicionar, redigir
        from apps.processos.modelo_escritura_fiel import CONFERENCIAS, CORPO, ROTULOS, chave_campo

        source = {'texto': 'Nome da compradora: Lídia de Teste', 'pagina_id': 'teste', 'leitura_versao': 1, 'canal': 'texto'}
        candidates = defaultdict(list)
        field = chave_campo('Nome da compradora')
        adicionar(candidates, field, 'Lídia de Teste', source, source['texto'])
        body, values, metadata = redigir([source], candidates, [], {})

        def expected(match):
            key = match[1]
            if key == field:
                return 'Lídia de Teste'
            return f'{MARCADOR}{ROTULOS[key]}]' + (' ' if key in CONFERENCIAS else '')

        self.assertEqual(body, TOKEN.sub(expected, CORPO))
        self.assertEqual(body.count('Lídia de Teste'), 3)
        self.assertEqual(set(values), {field})
        self.assertIn(chave_campo('Conferência da quitação e da transmissão'),
                      {item['campo'] for item in metadata['pendencias']})

    def test_assisted_reference_reads_labelled_conflicts_without_inference(self):
        from unittest.mock import patch

        from apps.processos import minuta_assistida
        from apps.processos.modelo_escritura_fiel import chave_campo

        case = self.create_case()
        anexos = f'/api/v1/atendimentos/{case}/anexos/'
        for name, text in (
            ('contrato.txt', f'{minuta_assistida.AVISO_SIMULACAO}\nPreço da venda: R$ 380.000,00'),
            ('proposta.txt', 'Preço da venda: R$ 395.000,00'),
            ('matricula.txt', 'A matrícula do imóvel é DEMO-174.'),
        ):
            resposta = self.client.post(anexos,
                {'arquivo': SimpleUploadedFile(name, text.encode())}, format='multipart')
            self.assertEqual(resposta.status_code, 201)
        matricula = chave_campo('Matrícula do imóvel')
        row = {'campo': minuta_assistida.CAMPOS_EXTRAIVEIS.index(matricula), 'fonte': 3,
               'trecho': 'A matrícula do imóvel é DEMO-174.', 'valor': 'DEMO-174'}
        with patch.object(minuta_assistida, 'provedor', return_value='local'), \
             patch.object(minuta_assistida, 'extrair', return_value=[row]) as extract:
            _, dados, resultado = minuta_assistida.preparar(Atendimento.objects.get(pk=case))
        self.assertEqual(extract.call_count, 1)
        self.assertEqual(extract.call_args.args[1], [{'fonte': 3, 'texto': row['trecho']}])
        self.assertEqual(dados[matricula]['origem']['arquivo'], 'matricula.txt')
        preco = chave_campo('Preço da venda')
        divergencia = next(item for item in resultado['pendencias'] if item['campo'] == preco)
        self.assertNotIn(preco, dados)
        self.assertEqual({item['valor'] for item in divergencia['alternativas']}, {'R$ 380.000,00', 'R$ 395.000,00'})

    def test_draft_model_activates_its_fields_and_never_fills_missing_blocks(self):
        case = self.ready_for_draft()
        self.assertEqual(self.select_reference(case).status_code, 201)
        questions = {q['chave'] for q in self.report(case)['pendencias']}
        self.assertTrue({'tributo', 'certidoes', 'consultas', 'quitacao', 'representacao'} <= questions)
        fields = self.client.get(f'/api/v1/atendimentos/{case}/ficha/').data['campos']
        self.assertTrue(next(f for f in fields if f['chave'] == 'consultas')['obrigatorio'])
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.fill_reference(case)
        self.assertFalse(self.report(case)['bloqueado'])
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertEqual(self.select_reference(case, approved=True, expected=1).status_code, 201)
        result = self.generate_draft(case)
        self.assertEqual(result.status_code, 200)
        draft = result.data['versoes'][0]
        self.assertNotIn('{{', draft['corpo'])
        self.assertEqual(draft['corpo'].count('TEXTO FICTÍCIO CONFERIDO PARA representacao'), 1)
        self.assertIn('ASSIM, justos e contratados, TEXTO FICTÍCIO CONFERIDO PARA encerramento', draft['corpo'])
        for key in TOKEN.findall(BASE_REFERENCIA['corpo']):
            self.assertEqual(draft['dados'][key]['situacao'], 'confirmado')
            self.assertTrue(draft['dados'][key]['origem']['mensagem_id'])
        self.assertNotIn('NEGATIVO', draft['corpo'])
        self.assertNotIn('Lei', draft['corpo'])

    def test_new_consultation_evidence_reopens_field_and_preserves_reading_source(self):
        case = self.ready_for_draft()
        self.select_reference(case, approved=True)
        self.fill_reference(case)
        self.assertEqual(self.generate_draft(case).status_code, 200)
        upload = self.client.post(f'/api/v1/atendimentos/{case}/anexos/',
            {'arquivo': SimpleUploadedFile('consulta-ficticia.txt', b'Consultas: RESULTADO FICTICIO DIVERGENTE')}, format='multipart')
        self.assertEqual(upload.status_code, 201)
        question = next(q for q in self.report(case)['pendencias'] if q['chave'] == 'consultas')
        self.assertEqual(question['tipo'], 'divergencia')
        source = next(c for c in question['candidatos'] if c['origem'] == 'documento')
        self.assertEqual(source['leitura_versao'], 1)
        self.assertEqual(source['pagina'], 1)
        self.assertEqual(source['trecho'], 'Consultas: RESULTADO FICTICIO DIVERGENTE')
        self.assertEqual(self.generate_draft(case).status_code, 400)
        state = self.client.get(f'/api/v1/atendimentos/{case}/minuta-preparada/').data
        self.assertTrue(state['versoes'][0]['desatualizada'])

    def test_simulated_new_blocks_keep_message_identity_without_confirmation(self):
        case = self.create_case()
        sent = self.client.post(f'/api/v1/atendimentos/{case}/mensagens/',
            {'texto':'Tributo: DADO FICTÍCIO\nConsultas: RESULTADO NÃO CONFERIDO', 'client_id':str(uuid4())}, format='json')
        response = self.client.post(f'/api/v1/atendimentos/{case}/interpretar-mensagem/',
            {'mensagem_id':sent.data['id']}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p['campo'] for p in response.data['propostas']], ['tributo', 'consultas'])
        for proposal in response.data['propostas']:
            self.assertEqual(proposal['origem']['mensagem_id'], sent.data['id'])
            self.assertEqual(proposal['origem']['trecho'], proposal['trecho'])
            self.assertFalse(proposal['confirmado'])
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())

    def test_extra_marker_added_to_model_creates_required_question(self):
        case = self.ready_for_draft()
        self.save_template(case)
        self.assertEqual(self.generate_draft(case).status_code, 200)
        from apps.processos.redacao import BASE
        self.assertEqual(self.save_template(case, expected=1, corpo=BASE['corpo']+'\n{{tributo}}').status_code, 201)
        self.assertIn('tributo', [q['chave'] for q in self.report(case)['pendencias']])
        self.assertEqual(self.generate_draft(case).status_code, 400)

    def reference_case_with_confirmed_fictitious_document(self):
        from pathlib import Path
        fixture = Path(__file__).resolve().parents[3] / 'docs/teste-escrevente/04-estrutura-referencia-ficticia.txt'
        case = self.create_case()
        self.assertEqual(self.select_reference(case).status_code, 201)
        content = fixture.read_text(encoding='utf-8')
        upload = self.client.post(f'/api/v1/atendimentos/{case}/anexos/',
            {'arquivo': SimpleUploadedFile(fixture.name, content.encode('utf-8'))}, format='multipart')
        self.assertEqual(upload.status_code, 201)
        from tests.fontes_ficticias import organizar
        organizar(self, case, upload.data['paginas'][0]['id'])
        self.assertEqual(self.answer(case, 'anexo:' + upload.data['id'])[0].status_code, 201)
        for key in TOKEN.findall(BASE_REFERENCIA['corpo']):
            question = next(q for q in self.report(case)['pendencias'] if q['chave'] == key)
            source = question['candidatos'][0]
            self.assertEqual(source['origem'], 'documento')
            self.assertEqual(source['anexo_id'], upload.data['id'])
            self.assertEqual(source['situacao'], 'extraido')
            self.assertIn(source['trecho'], content)
            response = self.client.post(f'/api/v1/atendimentos/{case}/responder/', {
                'chave': key, 'assinatura': question['assinatura'], 'versao_esperada': question['versao'],
                'client_id': str(uuid4()), 'valor': source['valor'], 'confirmar': True,
                'justificativa': 'Conferência fictícia explícita para teste',
                'fonte_documental': {
                    'pagina_id': source['id'], 'trecho': source['trecho'], 'canal': source['canal'],
                    'organizacao_versao': source['organizacao_versao'],
                },
            }, format='json')
            self.assertEqual(response.status_code, 201, response.data)
        self.assertFalse(self.report(case)['bloqueado'])
        return case

    def test_fictitious_document_to_confirmed_reference_draft(self):
        case = self.reference_case_with_confirmed_fictitious_document()
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.select_reference(case, approved=True, expected=1)
        response = self.generate_draft(case)
        self.assertEqual(response.status_code, 200)
        draft = response.data['versoes'][0]
        self.assertIn('MINUTA PARA CONFERÊNCIA — EXEMPLO FICTÍCIO', draft['corpo'])
        self.assertIn('OUTORGANTES: Álvaro Mendes do Vale', draft['corpo'])
        self.assertIn('OUTORGADA: Beatriz Nunes de Castro', draft['corpo'])
        self.assertIn('pelo preço certo e ajustado de R$ 120.000,00 (cento e vinte mil reais)', draft['corpo'])
        self.assertIn('R$ 40.000,00 na assinatura e R$ 80.000,00 em 21 de dezembro de 2026', draft['corpo'])
        self.assertIn('O vendedor dará quitação após o efetivo recebimento do preço integral.', draft['corpo'])
        self.assertIn('FIC-ITBI-01', draft['corpo'])
        self.assertIn('10. – Por fim, requerem as partes', draft['corpo'])
        body = draft['corpo'].split('SAIBAM quantos esta pública escritura virem que, ', 1)[1]
        anchors = ['1 - DO IMÓVEL', '2. - Assim', '6. – O IMPOSTO', '7. –', '8. –', '9. –',
                   '10. – Por fim', 'R$ 900,00 de emolumentos', 'ASSIM, justos e contratados']
        self.assertEqual([body.index(anchor) for anchor in anchors], sorted(body.index(anchor) for anchor in anchors))
        self.assertNotIn('\n', body)
        self.assertEqual(draft['campos_inseridos'], TOKEN.findall(BASE_REFERENCIA['corpo']))
        for key in draft['campos_inseridos']:
            origin = draft['dados'][key]['origem']
            self.assertTrue(origin['anexo_id'])
            self.assertEqual(origin['pagina'], 1)
            self.assertIn(draft['dados'][key]['valor'], origin['trecho'])
        self.assertNotIn('{{', draft['corpo'])
