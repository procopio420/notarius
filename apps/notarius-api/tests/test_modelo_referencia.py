from uuid import uuid4
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from apps.processos.ficha import TOKEN
from apps.processos.modelo_referencia import BASE_REFERENCIA
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
        self.assertEqual(response.data['referencia']['modelo'], BASE_REFERENCIA)
        self.assertFalse(response.data['referencia']['aprovado'])
        self.assertTrue(all(s['leitura'] and s['trecho'] for s in response.data['referencia']['fontes']))
        self.assertFalse(ModeloAtendimento.objects.exists())
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        hidden = Atendimento.objects.create(tenant=self.other, criado_por=self.user, titulo='Outro')
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{hidden.id}/modelo-minuta/').status_code, 404)

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
        self.assertIn('10.- TEXTO FICTÍCIO CONFERIDO PARA encerramento', draft['corpo'])
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

    def test_fictitious_document_to_confirmed_reference_draft(self):
        from pathlib import Path
        fixture = Path(__file__).resolve().parents[3] / 'docs/teste-escrevente/04-estrutura-referencia-ficticia.txt'
        case = self.create_case()
        self.assertEqual(self.select_reference(case).status_code, 201)
        upload = self.client.post(f'/api/v1/atendimentos/{case}/anexos/',
            {'arquivo': SimpleUploadedFile(fixture.name, fixture.read_bytes())}, format='multipart')
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
            self.assertIn(source['trecho'], fixture.read_text(encoding='utf-8'))
            self.assertEqual(self.answer(case, key, source['valor'])[0].status_code, 201)
        self.assertFalse(self.report(case)['bloqueado'])
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.select_reference(case, approved=True, expected=1)
        response = self.generate_draft(case)
        self.assertEqual(response.status_code, 200)
        self.assertIn('TEXTO FICTÍCIO DE TESTE PARA tributo', response.data['versoes'][0]['corpo'])
