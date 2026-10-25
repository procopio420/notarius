from uuid import uuid4
from unittest.mock import patch
from rest_framework.test import APITestCase
from tests import test_ficha_estruturada as base
from apps.processos.models import Atendimento, RevisaoDadoAtendimento


class RedacaoEstruturadaTests(APITestCase):
    setUp = base.FichaEstruturadaTests.setUp
    create_case = base.FichaEstruturadaTests.create_case
    get = base.FichaEstruturadaTests.get
    post = base.FichaEstruturadaTests.post
    obj = base.FichaEstruturadaTests.obj
    field = base.FichaEstruturadaTests.field
    save_template = base.FichaEstruturadaTests.save_template
    generate_draft = base.FichaEstruturadaTests.generate_draft

    def position(self, key='parte1', tipo='pessoa', **links):
        return {'chave': key, 'rotulo': f'POSIÇÃO FICTÍCIA {key}', 'tipo': tipo, 'vinculos': links}

    def confirmed(self, case, obj, key='nome', value='PESSOA FICTÍCIA', **kw):
        r, _ = self.field(case, obj, key, value, situacao='confirmado', confirmar=True, conferir_fonte=True, **kw)
        self.assertEqual(r.status_code, 201, r.data)
        return r

    def template(self, case, positions=None, text='EXEMPLO FICTÍCIO\n{{parte1.nome}}', **kw):
        r = self.save_template(case, corpo=text, representacao='', observacoes='', registros_minuta=positions or [self.position()], **kw)
        self.assertEqual(r.status_code, 201, r.data)
        return r

    def binding(self, case, registers, exclusions=None, **kw):
        url = f'/api/v1/atendimentos/{case}/vinculacao-minuta/'
        current = self.client.get(url).data
        payload = {'client_id': str(uuid4()), 'modelo_id': current['modelo_id'], 'versao_esperada': current['versao'],
                   'escopo_assinatura': current['escopo_assinatura'], 'registros': registers,
                   'exclusoes': exclusions or [], 'motivo': 'REVISÃO HUMANA FICTÍCIA DA VINCULAÇÃO', 'conferir': True, **kw}
        return self.client.post(url, payload, format='json'), payload

    def ready(self):
        case = self.create_case(); person = self.obj(case)
        self.confirmed(case, person); self.template(case)
        self.assertEqual(self.binding(case, {'parte1': person})[0].status_code, 201)
        return case, person

    def draft(self, case):
        response = self.generate_draft(case); self.assertEqual(response.status_code, 200, response.data)
        return response.data['versoes'][0]

    def test_literal_multiple_people_and_property_payment_are_not_mixed(self):
        case = self.create_case(); a = self.obj(case); b = self.obj(case); home = self.obj(case, 'imovel'); deal = self.obj(case, 'negociacao', imovel_id=home)
        self.confirmed(case, a, value='  PESSOA A FICTÍCIA  '); self.confirmed(case, b, value='PESSOA B FICTÍCIA')
        self.confirmed(case, home, 'descricao', 'IMÓVEL FICTÍCIO'); self.confirmed(case, deal, 'preco', 'R$ 100.000,00')
        self.confirmed(case, deal, 'situacao_pagamento', 'previsto')
        positions = [self.position('parte1'), self.position('parte2'), self.position('bem', 'imovel'), self.position('negocio', 'negociacao', imovel='bem')]
        text = 'FICTÍCIO\n{{parte1.nome}}\n{{parte2.nome}}\n{{bem.descricao}}\n{{negocio.preco}}\nSituação informada: {{negocio.situacao_pagamento}}\n{{parte1.nome}}'
        self.template(case, positions, text)
        self.assertEqual(self.binding(case, {'parte1': a, 'parte2': b, 'bem': home, 'negocio': deal})[0].status_code, 201)
        with patch('openai.OpenAI') as provider:
            draft = self.draft(case)
        provider.assert_not_called()
        self.assertIn('  PESSOA A FICTÍCIA  \nPESSOA B FICTÍCIA\nIMÓVEL FICTÍCIO\nR$ 100.000,00\nSituação informada: previsto', draft['corpo'])
        self.assertNotIn('pagamento realizado', draft['corpo'].lower())
        self.assertEqual(draft['dados']['parte1.nome']['objeto_id'], a)
        self.assertEqual(len(draft['dados']['parte1.nome']['ocorrencias']), 2)
        for data in draft['dados'].values():
            self.assertTrue(data['origem']['mensagem_id']); self.assertTrue(data['confirmacao'])
            for occurrence in data['ocorrencias']:
                self.assertEqual(draft['corpo'][occurrence['inicio']:occurrence['fim']], data['valor'])

    def test_missing_unconfirmed_manual_doubt_and_unknown_value_block_generation(self):
        case = self.create_case(); person = self.obj(case); self.template(case)
        self.assertEqual(self.binding(case, {'parte1': person})[0].status_code, 201)
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.field(case, person, 'nome', 'PESSOA FICTÍCIA')
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.confirmed(case, person, versao_esperada=1)
        self.draft(case)
        response = self.client.post(f'/api/v1/atendimentos/{case}/pendencias-ficha/', {'operacao': 'abrir', 'client_id': str(uuid4()), 'objeto_id': person, 'campo': 'nome', 'pergunta': 'DÚVIDA FICTÍCIA', 'justificativa': 'Verificar homônimo fictício'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.generate_draft(case).status_code, 400)

    def test_wrong_role_person_and_wrong_property_bindings_are_rejected(self):
        case = self.create_case(); a = self.obj(case); b = self.obj(case); role = self.obj(case, 'papel', pessoa_a_id=a)
        self.confirmed(case, a); self.confirmed(case, b, value='OUTRA PESSOA FICTÍCIA'); self.confirmed(case, role, 'tipo_papel', 'vendedor')
        self.template(case, [self.position(), self.position('papel1', 'papel', pessoa_a='parte1')], '{{parte1.nome}} · {{papel1.tipo_papel}}')
        self.assertEqual(self.binding(case, {'parte1': b, 'papel1': role}, [{'objeto_id': a, 'motivo': 'TESTE'}])[0].status_code, 400)
        self.assertEqual(self.binding(case, {'parte1': a, 'papel1': role}, [{'objeto_id': b, 'motivo': 'Não participa deste texto fictício'}])[0].status_code, 201)

    def test_exclusions_require_reason_and_reopen_when_excluded_record_changes(self):
        case, person = self.ready(); extra = self.obj(case); self.confirmed(case, extra)
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertEqual(self.binding(case, {'parte1': person})[0].status_code, 400)
        self.assertEqual(self.binding(case, {'parte1': person}, [{'objeto_id': extra, 'motivo': 'Fora deste texto fictício, por decisão humana'}])[0].status_code, 201)
        self.draft(case)
        self.confirmed(case, extra, value='EXTRA FICTÍCIO ALTERADO', versao_esperada=1)
        self.assertFalse(self.client.get(f'/api/v1/atendimentos/{case}/vinculacao-minuta/').data['atual'])
        self.assertEqual(self.generate_draft(case).status_code, 400)

    def test_stale_binding_and_idempotence_and_history(self):
        case, person = self.ready()
        first, payload = self.binding(case, {'parte1': person})
        self.assertEqual(first.status_code, 201)
        url = f'/api/v1/atendimentos/{case}/vinculacao-minuta/'
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 200)
        self.assertEqual(self.client.post(url, {**payload, 'client_id': str(uuid4())}, format='json').status_code, 409)
        self.assertEqual(len(self.client.get(url).data['historico']), 2)
        self.assertEqual(self.binding(case, {'parte1': person}, conferir=False)[0].status_code, 400)

    def test_old_draft_review_and_export_invalidated_by_field_change(self):
        case, person = self.ready(); old = self.draft(case)
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{case}/minutas/{old['id']}/exportar/", {'formato': 'docx'}).status_code, 409)
        self.confirmed(case, person, value='PESSOA CORRIGIDA FICTÍCIA', versao_esperada=1)
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{case}/minutas/{old['id']}/exportar/", {'formato': 'pdf'}).status_code, 409)
        new = self.draft(case)
        self.assertEqual(new['versao'], 2)
        self.assertEqual(new['dados']['parte1.nome']['valor'], 'PESSOA CORRIGIDA FICTÍCIA')

    def test_model_change_requires_new_binding_and_fixed_facts_are_not_evidence(self):
        case, person = self.ready(); self.draft(case)
        self.template(case, text='FICTÍCIO: receberam {{parte1.nome}}', expected=1)
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertEqual(self.binding(case, {'parte1': person})[0].status_code, 201)
        response = self.generate_draft(case); self.assertEqual(response.status_code, 400)
        self.assertIn('modelo contém', str(response.data))

    def test_unknown_mixed_and_unbound_template_markers_rejected(self):
        case = self.create_case()
        for text in ['{{parte1.campo_inventado}}', '{{parte1.nome}} {{vendedores}}', '{{parte_desconhecida.nome}}']:
            response = self.save_template(case, corpo=text, representacao='', observacoes='', registros_minuta=[self.position()])
            self.assertEqual(response.status_code, 400, response.data)

    def test_large_repeated_fill_is_blocked_without_truncating_or_saving(self):
        case = self.create_case(); person = self.obj(case)
        self.confirmed(case, person, value='FICTICIO' + 'X' * 9992)
        self.template(case, text='FICTÍCIO\n' + '{{parte1.nome}}\n' * 16)
        self.assertEqual(self.binding(case, {'parte1': person})[0].status_code, 201)
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertFalse(Atendimento.objects.get(pk=case).minutas_preparadas.exists())

    def test_other_case_and_tenant_cannot_supply_records_or_read_binding(self):
        case, person = self.ready(); other = self.create_case(); self.template(other)
        self.assertEqual(self.binding(other, {'parte1': person})[0].status_code, 400)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{case}/vinculacao-minuta/').status_code, 403)

    def test_edit_preserves_base_sources_without_claiming_insert_offsets_in_edited_text(self):
        case, _ = self.ready(); draft = self.draft(case)
        response = self.client.post(f'/api/v1/atendimentos/{case}/editar-minuta/', {'client_id': str(uuid4()), 'minuta_id': draft['id'], 'versao_esperada': draft['versao'], 'corpo': 'EDIÇÃO HUMANA FICTÍCIA\n' + draft['corpo'], 'motivo': 'Revisão fictícia de redação'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        edited = self.client.get(f'/api/v1/atendimentos/{case}/minuta-preparada/').data['versoes'][0]
        self.assertFalse(edited['ocorrencias_correspondem_texto'])
        self.assertEqual(edited['dados'], draft['dados'])

    def test_export_same_saved_text_only_after_explicit_final_review(self):
        from io import BytesIO
        from docx import Document
        from pypdf import PdfReader
        case, _ = self.ready(); draft = self.draft(case)
        response = self.client.post(f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/revisar/", {
            'versao_esperada': draft['versao'], 'motivo': 'REVISÃO FINAL FICTÍCIA, SEM VALIDADE PROFISSIONAL',
            'conferi_texto': True, 'conferi_dados': True, 'conferi_fontes': True}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        url = f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/exportar/"
        word = self.client.get(url, {'formato': 'docx'}); self.assertEqual(word.status_code, 200)
        paragraphs = [p.text for p in Document(BytesIO(word.content)).paragraphs]
        self.assertEqual('\n'.join(paragraphs[3:]), draft['corpo'])
        pdf = self.client.get(url, {'formato': 'pdf'}); self.assertEqual(pdf.status_code, 200)
        text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages)
        self.assertIn('PESSOA FICTÍCIA', text)
        self.assertNotIn('{{', text)

    def test_library_carries_positions_without_case_record_ids(self):
        case, person = self.ready()
        model = Atendimento.objects.get(pk=case).modelos_minuta.first()
        response = self.client.post(f'/api/v1/atendimentos/{case}/publicar-modelo/', {
            'modelo_id': str(model.id), 'nome': 'PADRÃO FICTÍCIO ESTRUTURADO', 'confirmar_sem_dados': True}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        library = self.client.get('/api/v1/atendimentos/biblioteca-modelos/').data['modelos'][0]
        self.assertEqual(library['registros_minuta'], [self.position()])
        self.assertNotIn(person, str(library))
        other = self.create_case()
        self.assertEqual(self.binding(other, {'parte1': person})[0].status_code, 400)

    def test_replaced_document_reading_blocks_saved_draft_and_its_revisions(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.processos.models import PaginaAnexoAtendimento, AnexoAtendimento
        case = self.create_case(); person = self.obj(case)
        text = 'PESSOA FICTÍCIA DOCUMENTAL'
        uploaded = self.client.post(f'/api/v1/atendimentos/{case}/anexos/', {'arquivo': SimpleUploadedFile('fonte-ficticia.txt', text.encode())}, format='multipart')
        self.assertEqual(uploaded.status_code, 201)
        page = PaginaAnexoAtendimento.objects.get(anexo_id=uploaded.data['id'])
        revision = self.confirmed(case, person, value=text, origem='documento', pagina_id=str(page.id), leitura_versao=1, trecho_origem=text)
        url = f'/api/v1/atendimentos/{case}/pendencias-ficha/'
        issues = self.client.post(url, {'operacao': 'atualizar'}, format='json').data['pendencias']
        issue = next(p for p in issues if p['tipo'] == 'pagina')
        reviewed = self.client.post(url, {'operacao': 'resolver', 'client_id': str(uuid4()), 'pendencia_id': issue['id'],
            'assinatura': issue['assinatura'], 'versao_esperada': issue['versao'], 'acao': 'vincular',
            'revisoes_ids': revision.data['revisoes'], 'confirmei_revisao': True, 'justificativa': 'REVISÃO FICTÍCIA DA FONTE'}, format='json')
        self.assertEqual(reviewed.status_code, 201, reviewed.data)
        self.template(case); self.assertEqual(self.binding(case, {'parte1': person})[0].status_code, 201)
        old = self.draft(case)
        self.assertEqual(old['dados']['parte1.nome']['origem']['leitura_versao'], 1)
        AnexoAtendimento.objects.filter(id=uploaded.data['id']).update(leitura_versao=2)
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{case}/minutas/{old['id']}/exportar/", {'formato': 'docx'}).status_code, 409)


from rest_framework.test import APITransactionTestCase
from django.db import connection, close_old_connections
from threading import Event, Thread


class ConcorrenciaVinculacaoTests(APITransactionTestCase):
    setUp = RedacaoEstruturadaTests.setUp
    create_case = RedacaoEstruturadaTests.create_case
    get = RedacaoEstruturadaTests.get
    post = RedacaoEstruturadaTests.post
    obj = RedacaoEstruturadaTests.obj
    field = RedacaoEstruturadaTests.field
    confirmed = RedacaoEstruturadaTests.confirmed
    save_template = RedacaoEstruturadaTests.save_template
    position = RedacaoEstruturadaTests.position
    template = RedacaoEstruturadaTests.template

    def test_overlapping_writers_keep_one_binding_version(self):
        from apps.processos import redacao_estruturada as service
        from apps.processos.ficha_estruturada import FichaAlterada
        if connection.vendor != 'sqlite':
            self.skipTest('Concorrência SQLite; PostgreSQL exige seu ambiente próprio.')
        case = self.create_case(); person = self.obj(case); self.confirmed(case, person); self.template(case)
        record = Atendimento.objects.get(pk=case); state = service.consultar(record)
        data = {'client_id': str(uuid4()), 'modelo_id': state['modelo_id'], 'versao_esperada': 0,
                'escopo_assinatura': state['escopo_assinatura'], 'registros': {'parte1': person},
                'exclusoes': [], 'motivo': 'CONCORRÊNCIA FICTÍCIA', 'conferir': True}
        entered, release = Event(), Event(); outcome = []
        original = service.conferir_vinculos
        def hold(*args):
            entered.set()
            if not release.wait(10):
                raise RuntimeError('Escritor fictício não liberado.')
            return original(*args)
        def worker():
            close_old_connections()
            try:
                outcome.append(service.salvar(record, self.user, data))
            except Exception as e:
                outcome.append(e)
            finally:
                close_old_connections()
        with patch.object(service, 'conferir_vinculos', side_effect=hold):
            thread = Thread(target=worker); thread.start()
            try:
                self.assertTrue(entered.wait(10))
                with self.assertRaises(FichaAlterada):
                    service.salvar(record, self.user, {**data, 'client_id': str(uuid4())})
            finally:
                release.set(); thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertIsInstance(outcome[0], tuple, outcome)
        self.assertEqual(record.vinculacoes_minuta.count(), 1)
