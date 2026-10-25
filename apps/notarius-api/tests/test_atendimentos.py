from uuid import uuid4
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.tenancy.models import Tenant
from apps.profiles.models import UserProfile
from apps.processos.models import Atendimento, MensagemAtendimento
from apps.processos.models import RevisaoDadoAtendimento, AnexoAtendimento


def pdf_fixture(blank_page=False, encrypted=False):
    writer = PdfWriter()
    page = writer.add_blank_page(width=595, height=842)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = writer._add_object(DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})}))
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 50 750 Td (DOCUMENTO FICTICIO - Preco informado: 100000) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    if blank_page:
        writer.add_blank_page(width=595, height=842)
    if encrypted:
        writer.encrypt('test-only')
    result = BytesIO()
    writer.write(result)
    return result.getvalue()


class AtendimentoTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('qa_atendimento', password='test-only')
        self.tenant = Tenant.objects.create(nome='Cartório QA', uf='RJ')
        self.other = Tenant.objects.create(nome='Outro cartório QA', uf='SP')
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.tenants.add(self.tenant)
        profile.default_tenant = self.tenant
        profile.save()
        self.client.force_authenticate(self.user)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))

    def create_case(self):
        response = self.client.post('/api/v1/atendimentos/', {'titulo': 'Caso fictício'}, format='json')
        self.assertEqual(response.status_code, 201)
        return response.data['id']

    def test_case_and_messages_persist_and_retry_is_idempotent(self):
        case_id = self.create_case()
        url = f'/api/v1/atendimentos/{case_id}/mensagens/'
        payload = {'texto': 'Informação fictícia\nSegunda linha', 'client_id': str(uuid4())}
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 201)
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 200)
        self.assertEqual(MensagemAtendimento.objects.count(), 1)
        self.assertEqual(self.client.get(url).data[0]['texto'], payload['texto'])
        message = MensagemAtendimento.objects.get()
        self.assertEqual(message.autor, self.user)
        self.assertEqual(message.tenant, self.tenant)
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{case_id}/').status_code, 200)
        self.assertEqual(len(self.client.get('/api/v1/atendimentos/').data), 1)
        payload['texto'] = 'Outro conteúdo usando o mesmo identificador'
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 400)

    def test_rejects_blank_and_oversized_content(self):
        self.assertEqual(self.client.post('/api/v1/atendimentos/', {'titulo': '  '}, format='json').status_code, 400)
        case_id = self.create_case()
        url = f'/api/v1/atendimentos/{case_id}/mensagens/'
        for text in ['  ', 'x' * 10001]:
            self.assertEqual(self.client.post(url, {'texto': text, 'client_id': str(uuid4())}, format='json').status_code, 400)
        self.assertEqual(MensagemAtendimento.objects.count(), 0)

    def test_cannot_read_or_write_another_tenant(self):
        hidden = Atendimento.objects.create(tenant=self.other, criado_por=self.user, titulo='Isolado')
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{hidden.id}/').status_code, 404)
        self.assertEqual(self.client.post(f'/api/v1/atendimentos/{hidden.id}/mensagens/',
            {'texto': 'Não salvar', 'client_id': str(uuid4())}, format='json').status_code, 404)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertEqual(self.client.get('/api/v1/atendimentos/').status_code, 403)
        self.assertEqual(self.client.post('/api/v1/atendimentos/', {'titulo': 'Não criar'}, format='json').status_code, 403)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertIn(self.client.get('/api/v1/atendimentos/').status_code, [401, 403])

    def test_ficha_preserves_revisions_and_message_provenance(self):
        case_id = self.create_case()
        msg = self.client.post(f'/api/v1/atendimentos/{case_id}/mensagens/',
            {'texto': 'Valor fictício informado: 100', 'client_id': str(uuid4())}, format='json').data
        url = f'/api/v1/atendimentos/{case_id}/ficha/'
        initial = self.client.get(url)
        self.assertEqual(initial.status_code, 200)
        self.assertEqual(len(initial.data['campos']), 7)
        self.assertTrue(all(c['atual'] is None for c in initial.data['campos']))
        data = {'chave': 'preco', 'valor': '100', 'situacao': 'informado',
                'mensagem_id': msg['id'], 'justificativa': 'Transcrito da conversa', 'versao_esperada': 0}
        first = self.client.post(url, data, format='json')
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.data['origem']['trecho'], 'Valor fictício informado: 100')
        data.update(valor='200', situacao='confirmado', mensagem_id=None,
                    justificativa='Correção confirmada pela escrevente', versao_esperada=1)
        self.assertEqual(self.client.post(url, data, format='json').status_code, 201)
        field = next(c for c in self.client.get(url).data['campos'] if c['chave'] == 'preco')
        self.assertEqual(field['atual']['valor'], '200')
        self.assertEqual(field['atual']['situacao'], 'confirmado')
        self.assertEqual([r['valor'] for r in field['historico']], ['200', '100'])
        self.assertEqual(field['historico'][1]['origem']['mensagem_id'], msg['id'])

    def test_ficha_rejects_stale_updates_and_invalid_confirmation(self):
        case_id = self.create_case()
        url = f'/api/v1/atendimentos/{case_id}/ficha/'
        data = {'chave': 'preco', 'valor': '', 'situacao': 'confirmado',
                'justificativa': 'Teste', 'versao_esperada': 0}
        self.assertEqual(self.client.post(url, data, format='json').status_code, 400)
        data['valor'] = '100'
        self.assertEqual(self.client.post(url, data, format='json').status_code, 201)
        data['valor'] = '200'
        self.assertEqual(self.client.post(url, data, format='json').status_code, 409)
        field = next(c for c in self.client.get(url).data['campos'] if c['chave'] == 'preco')
        self.assertEqual(field['atual']['valor'], '100')
        self.assertEqual(len(field['historico']), 1)

    def test_ficha_rejects_source_from_another_case(self):
        first, second = self.create_case(), self.create_case()
        msg = self.client.post(f'/api/v1/atendimentos/{first}/mensagens/',
            {'texto': 'Outro atendimento', 'client_id': str(uuid4())}, format='json').data
        response = self.client.post(f'/api/v1/atendimentos/{second}/ficha/',
            {'chave': 'imovel', 'valor': 'Teste', 'situacao': 'informado',
             'mensagem_id': msg['id'], 'justificativa': 'Teste', 'versao_esperada': 0}, format='json')
        self.assertEqual(response.status_code, 400)
        hidden = Atendimento.objects.create(tenant=self.other, criado_por=self.user, titulo='Isolado')
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{hidden.id}/ficha/').status_code, 404)

    def test_pdf_upload_extracts_pages_without_confirming_fields(self):
        case = self.create_case()
        content = pdf_fixture(blank_page=True)
        url = f'/api/v1/atendimentos/{case}/anexos/'
        upload = lambda: self.client.post(url, {'arquivo': SimpleUploadedFile('teste.pdf', content, 'application/pdf')}, format='multipart')
        response = upload()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['situacao'], 'revisao')
        self.assertIn('Preco informado', response.data['paginas'][0]['texto'])
        self.assertEqual(response.data['paginas'][1]['situacao'], 'revisao')
        self.assertEqual(response.data['paginas'][1]['texto'], '')
        self.assertEqual(upload().status_code, 200)
        self.assertEqual(AnexoAtendimento.objects.count(), 1)
        self.assertEqual(RevisaoDadoAtendimento.objects.count(), 0)
        downloaded = self.client.get(f"{url}{response.data['id']}/download/")
        self.assertEqual(downloaded.content, content)
        self.assertEqual(downloaded['Cache-Control'], 'no-store')
        self.assertNotIn('conteudo', self.client.get(url).data[0])

    def test_corrupt_and_encrypted_pdf_remain_pending(self):
        case = self.create_case()
        url = f'/api/v1/atendimentos/{case}/anexos/'
        for content in [b'%PDF-1.4\nbroken', pdf_fixture(encrypted=True)]:
            r = self.client.post(url, {'arquivo': SimpleUploadedFile('pendente.pdf', content)}, format='multipart')
            self.assertEqual(r.status_code, 201)
            self.assertEqual(r.data['situacao'], 'revisao')
            self.assertEqual(r.data['paginas'], [])

    def test_txt_origin_must_be_literal_and_belong_to_case(self):
        case = self.create_case()
        url = f'/api/v1/atendimentos/{case}/anexos/'
        upload = self.client.post(url, {'arquivo': SimpleUploadedFile('teste.txt', b'TESTE FICTICIO\nPreco: 100000')}, format='multipart')
        self.assertEqual(upload.status_code, 201)
        data = {'chave': 'preco', 'valor': '100000', 'situacao': 'informado',
                'organizacao_versao': 0,
                'pagina_id': upload.data['paginas'][0]['id'], 'trecho_origem': 'Preco: 100000',
                'justificativa': 'Transcrito literalmente para teste', 'versao_esperada': 0}
        ficha = f'/api/v1/atendimentos/{case}/ficha/'
        response = self.client.post(ficha, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['origem']['tipo'], 'documento')
        self.assertEqual(response.data['origem']['arquivo'], 'teste.txt')
        self.assertEqual(response.data['origem']['pagina'], 1)
        data.update(trecho_origem='Texto inventado', versao_esperada=1)
        self.assertEqual(self.client.post(ficha, data, format='json').status_code, 400)
        other_case = self.create_case()
        data.update(trecho_origem='Preco: 100000', versao_esperada=0)
        self.assertEqual(self.client.post(f'/api/v1/atendimentos/{other_case}/ficha/', data, format='json').status_code, 400)

    def test_upload_rejects_wrong_format_size_and_invalid_text(self):
        case = self.create_case()
        url = f'/api/v1/atendimentos/{case}/anexos/'
        for name, content in [('fake.pdf', b'not pdf'), ('arquivo.exe', b'not allowed'), ('invalid.txt', b'\xff\xfe'), ('empty.txt', b''), ('large.txt', b'x' * (10 * 1024 * 1024 + 1))]:
            response = self.client.post(url, {'arquivo': SimpleUploadedFile(name, content)}, format='multipart')
            self.assertEqual(response.status_code, 400)
        self.assertEqual(AnexoAtendimento.objects.count(), 0)

    def test_anexos_are_scoped_and_empty_image_stays_uncertain(self):
        import base64
        png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')
        case = self.create_case()
        url = f'/api/v1/atendimentos/{case}/anexos/'
        response = self.client.post(url, {'arquivo': SimpleUploadedFile('scan.png', png)}, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['situacao'], 'revisao')
        self.assertEqual(len(response.data['paginas']), 1)
        self.assertEqual(response.data['paginas'][0]['texto'], '')
        self.assertEqual(response.data['paginas'][0]['situacao'], 'revisao')
        other_case = self.create_case()
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{other_case}/anexos/{response.data['id']}/download/").status_code, 404)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.get(f"{url}{response.data['id']}/download/").status_code, 403)

    def report(self, case):
        return self.client.get(f'/api/v1/atendimentos/{case}/conferencia/').data

    def answer(self, case, key, value='', confirm=True):
        question = next(q for q in self.report(case)['pendencias'] if q['chave'] == key)
        payload = {'chave': key, 'assinatura': question['assinatura'], 'versao_esperada': question['versao'],
                   'client_id': str(uuid4()), 'valor': value, 'confirmar': confirm, 'justificativa': 'Conferência fictícia explícita para teste'}
        return self.client.post(f'/api/v1/atendimentos/{case}/responder/', payload, format='json'), payload

    def test_conference_blocks_missing_data_and_saves_unconfirmed_answer(self):
        case = self.create_case()
        self.assertTrue(self.report(case)['bloqueado'])
        self.assertEqual(self.client.post(f'/api/v1/atendimentos/{case}/verificar-redacao/').status_code, 409)
        answer, payload = self.answer(case, 'vendedores', 'Pessoa fictícia', False)
        self.assertEqual(answer.status_code, 201)
        self.assertIn('vendedores', [q['chave'] for q in self.report(case)['pendencias']])
        self.assertEqual(self.client.post(f'/api/v1/atendimentos/{case}/responder/', payload, format='json').status_code, 200)
        self.assertEqual(MensagemAtendimento.objects.count(), 1)
        self.assertEqual(RevisaoDadoAtendimento.objects.get().situacao, 'informado')

    def test_conflict_has_sources_and_requires_new_decision_when_evidence_changes(self):
        case = self.create_case()
        for value in ['100.000,00', '200.000,00']:
            self.client.post(f'/api/v1/atendimentos/{case}/anexos/',
                {'arquivo': SimpleUploadedFile(f'{value}.txt', f'Preço: R$ {value}'.encode())}, format='multipart')
        question = next(q for q in self.report(case)['pendencias'] if q['chave'] == 'preco')
        self.assertEqual(question['tipo'], 'divergencia')
        self.assertEqual(len(question['candidatos']), 2)
        self.assertTrue(all(c['arquivo'] and c['pagina'] == 1 for c in question['candidatos']))
        response, old = self.answer(case, 'preco', 'R$ 100.000,00')
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('preco', [q['chave'] for q in self.report(case)['pendencias']])
        self.client.post(f'/api/v1/atendimentos/{case}/mensagens/',
            {'texto': 'Preço: R$ 300.000,00', 'client_id': str(uuid4())}, format='json')
        self.assertIn('preco', [q['chave'] for q in self.report(case)['pendencias']])
        old['client_id'] = str(uuid4())
        self.assertEqual(self.client.post(f'/api/v1/atendimentos/{case}/responder/', old, format='json').status_code, 409)

    def test_all_initial_checks_require_document_review_and_confirmations(self):
        case = self.create_case()
        upload = self.client.post(f'/api/v1/atendimentos/{case}/anexos/',
            {'arquivo': SimpleUploadedFile('ficticio.txt', b'Documento ficticio sem interpretacao automatica')}, format='multipart')
        key = f"anexo:{upload.data['id']}"
        from tests.fontes_ficticias import organizar
        organizar(self, case, upload.data['paginas'][0]['id'])
        self.assertEqual(self.answer(case, key, confirm=False)[0].status_code, 400)
        self.assertEqual(self.answer(case, key)[0].status_code, 201)
        for field in ['vendedores', 'compradores', 'imovel', 'preco', 'pagamento']:
            self.assertEqual(self.answer(case, field, 'Informação fictícia confirmada')[0].status_code, 201)
        self.assertFalse(self.report(case)['bloqueado'])
        self.assertEqual(self.client.post(f'/api/v1/atendimentos/{case}/verificar-redacao/').status_code, 200)

    def test_money_comparison_does_not_treat_format_as_difference(self):
        from apps.processos.conferencia import comparar
        self.assertEqual(comparar('preco', 'R$ 100.000,00'), comparar('preco', '100000'))
        self.assertNotEqual(comparar('preco', '100.000,00'), comparar('preco', '200.000,00'))

    def test_conference_does_not_interpret_free_text_or_leak_other_case(self):
        case = self.create_case()
        self.client.post(f'/api/v1/atendimentos/{case}/mensagens/',
            {'texto': 'Não sei qual é o preço, não confirme nada.', 'client_id': str(uuid4())}, format='json')
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        self.assertTrue(all(not q['candidatos'] for q in self.report(case)['pendencias']))
        hidden = Atendimento.objects.create(tenant=self.other, criado_por=self.user, titulo='Isolado')
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{hidden.id}/conferencia/').status_code, 404)

    def test_unknown_answer_cannot_be_confirmed(self):
        case = self.create_case()
        response, _ = self.answer(case, 'preco', 'não sei', True)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(MensagemAtendimento.objects.exists())
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        self.assertIn('preco', [q['chave'] for q in self.report(case)['pendencias']])

    def ready_for_draft(self):
        case = self.create_case()
        upload = self.client.post(f'/api/v1/atendimentos/{case}/anexos/',
            {'arquivo': SimpleUploadedFile('teste.txt', b'Documento inteiramente ficticio para teste')}, format='multipart')
        self.answer(case, f"anexo:{upload.data['id']}")
        from tests.fontes_ficticias import organizar
        organizar(self, case, upload.data['paginas'][0]['id'])
        for key, value in {'vendedores': 'VENDEDOR FICTICIO', 'compradores': 'COMPRADOR FICTICIO',
                           'imovel': 'IMOVEL FICTICIO', 'preco': '100000', 'pagamento': 'CONDICAO FICTICIA'}.items():
            self.assertEqual(self.answer(case, key, value)[0].status_code, 201)
        return case

    def save_template(self, case, approved=True, expected=0, **overrides):
        from apps.processos.redacao import BASE
        payload = {**BASE, 'aprovado': approved, 'justificativa': 'MODELO FICTICIO APENAS PARA TESTE', 'versao_esperada': expected, **overrides}
        return self.client.post(f'/api/v1/atendimentos/{case}/modelo-minuta/', payload, format='json')

    def generate_draft(self, case):
        url = f'/api/v1/atendimentos/{case}/minuta-preparada/'
        fingerprint = self.client.get(url).data['assinatura']
        return self.client.post(url, {'assinatura_esperada': fingerprint}, format='json')

    def test_draft_cannot_bypass_pending_questions_or_template_approval(self):
        empty = self.create_case()
        self.assertEqual(self.save_template(empty).status_code, 201)
        self.assertEqual(self.generate_draft(empty).status_code, 400)
        ready = self.ready_for_draft()
        self.assertEqual(self.generate_draft(ready).status_code, 400)
        self.assertEqual(self.save_template(ready, approved=False).status_code, 201)
        self.assertEqual(self.generate_draft(ready).status_code, 400)

    def test_draft_is_literal_versioned_and_idempotent(self):
        case = self.ready_for_draft()
        self.assertEqual(self.save_template(case).status_code, 201)
        response = self.generate_draft(case)
        self.assertEqual(response.status_code, 200)
        first = response.data['versoes'][0]
        self.assertIn('VENDEDOR FICTICIO', first['corpo'])
        self.assertIn('100000', first['corpo'])
        self.assertNotIn('{{', first['corpo'])
        self.assertNotIn('REPRESENTAÇÃO', first['corpo'])
        self.assertFalse(first['desatualizada'])
        again = self.generate_draft(case)
        self.assertEqual(len(again.data['versoes']), 1)
        self.assertEqual(again.data['versoes'][0]['id'], first['id'])

    def test_new_template_revokes_approval_and_marks_old_draft_stale(self):
        case = self.ready_for_draft()
        self.save_template(case)
        self.generate_draft(case)
        self.assertEqual(self.save_template(case, approved=False, expected=1).status_code, 201)
        url = f'/api/v1/atendimentos/{case}/minuta-preparada/'
        state = self.client.get(url).data
        self.assertFalse(state['pronto'])
        self.assertTrue(state['versoes'][0]['desatualizada'])
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertEqual(self.save_template(case, expected=1).status_code, 409)

    def test_template_rejects_unknown_or_missing_markers(self):
        case = self.create_case()
        self.assertEqual(self.save_template(case, corpo='{{nome_inventado}}').status_code, 400)
        self.assertEqual(self.save_template(case, corpo='Sem os campos necessários').status_code, 400)

    def test_new_message_invalidates_draft_and_stale_generation_is_rejected(self):
        case = self.ready_for_draft()
        self.save_template(case)
        result = self.generate_draft(case)
        old = result.data['assinatura']
        self.client.post(f'/api/v1/atendimentos/{case}/mensagens/',
            {'texto': 'Preço: 200000', 'client_id': str(uuid4())}, format='json')
        url = f'/api/v1/atendimentos/{case}/minuta-preparada/'
        self.assertTrue(self.client.get(url).data['versoes'][0]['desatualizada'])
        self.assertEqual(self.client.post(url, {'assinatura_esperada': old}, format='json').status_code, 409)
        self.assertEqual(self.generate_draft(case).status_code, 400)

    def test_draft_and_template_are_scoped_to_authorized_tenant(self):
        hidden = Atendimento.objects.create(tenant=self.other, criado_por=self.user, titulo='Isolado')
        for path in ['modelo-minuta', 'minuta-preparada']:
            self.assertEqual(self.client.get(f'/api/v1/atendimentos/{hidden.id}/{path}/').status_code, 404)

    def test_conditional_block_uses_only_confirmed_representation(self):
        case = self.ready_for_draft()
        self.client.post(f'/api/v1/atendimentos/{case}/mensagens/',
            {'texto': 'Representação: PROCURADOR FICTICIO', 'client_id': str(uuid4())}, format='json')
        self.assertEqual(self.answer(case, 'representacao', 'PROCURADOR FICTICIO')[0].status_code, 201)
        self.save_template(case)
        response = self.generate_draft(case)
        self.assertEqual(response.status_code, 200)
        self.assertIn('REPRESENTAÇÃO\nPROCURADOR FICTICIO', response.data['versoes'][0]['corpo'])
        self.assertIn('origem', response.data['versoes'][0]['dados']['representacao'])

    def test_unfilled_marker_in_confirmed_data_blocks_rendering(self):
        case = self.ready_for_draft()
        self.client.post(f'/api/v1/atendimentos/{case}/mensagens/',
            {'texto': 'Vendedores: Pessoa {{campo_pendente}}', 'client_id': str(uuid4())}, format='json')
        self.answer(case, 'vendedores', 'Pessoa {{campo_pendente}}')
        self.save_template(case)
        self.assertFalse(self.client.get(f'/api/v1/atendimentos/{case}/minuta-preparada/').data['pronto'])
        self.assertEqual(self.generate_draft(case).status_code, 400)

    def draft_for_editing(self):
        case = self.ready_for_draft()
        self.save_template(case)
        return case, self.generate_draft(case).data['versoes'][0]

    def edit_draft(self, case, draft, text):
        data = {'minuta_id': draft['id'], 'versao_esperada': draft['versao'], 'client_id': str(uuid4()),
                'corpo': text, 'motivo': 'Ajuste manual fictício para teste'}
        return self.client.post(f'/api/v1/atendimentos/{case}/editar-minuta/', data, format='json'), data

    def test_manual_edit_is_new_version_and_retry_does_not_duplicate(self):
        case, first = self.draft_for_editing()
        text = first['corpo'] + '\nREVISÃO MANUAL FICTÍCIA: cláusula <teste> & condições.'
        saved, payload = self.edit_draft(case, first, text)
        self.assertEqual(saved.status_code, 201)
        again = self.client.post(f'/api/v1/atendimentos/{case}/editar-minuta/', payload, format='json')
        self.assertEqual(again.status_code, 200)
        state = self.client.get(f'/api/v1/atendimentos/{case}/minuta-preparada/').data
        self.assertEqual(len(state['versoes']), 2)
        self.assertEqual(state['versoes'][0]['corpo'], text)
        self.assertEqual(state['versoes'][0]['tipo'], 'editada')
        self.assertEqual(state['versoes'][1]['corpo'], first['corpo'])
        self.assertEqual(state['versoes'][0]['base_id'], first['id'])
        self.assertEqual(self.edit_draft(case, first, 'Outro texto')[0].status_code, 409)

    def review_draft(self, case, draft):
        response = self.client.post(f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/revisar/", {
            'versao_esperada':draft['versao'], 'motivo':'Conferência fictícia para testar exportação',
            'conferi_texto':True, 'conferi_dados':True, 'conferi_fontes':True}, format='json')
        self.assertIn(response.status_code, [200,201])
        return response

    def test_word_and_pdf_export_saved_edited_text(self):
        from docx import Document
        from pypdf import PdfReader
        case, first = self.draft_for_editing()
        text = first['corpo'] + '\nREVISÃO MANUAL FICTÍCIA: cláusula <teste> & condições.'
        saved, _ = self.edit_draft(case, first, text)
        self.review_draft(case, saved.data)
        url = f"/api/v1/atendimentos/{case}/minutas/{saved.data['id']}/exportar/"
        word = self.client.get(url, {'formato': 'docx'})
        self.assertEqual(word.status_code, 200)
        document = Document(BytesIO(word.content))
        self.assertEqual('\n'.join(p.text for p in document.paragraphs[3:]), text)
        pdf = self.client.get(url, {'formato': 'pdf'})
        self.assertEqual(pdf.status_code, 200)
        extracted = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages)
        self.assertIn('VENDEDOR FICTICIO', extracted)
        self.assertIn('cláusula <teste> & condições.', extracted)
        self.assertEqual(word['Cache-Control'], 'no-store')
        self.assertEqual(pdf['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{case}/minutas/{first['id']}/exportar/", {'formato': 'pdf'}).status_code, 409)

    def test_changed_data_blocks_editing_and_export(self):
        case, first = self.draft_for_editing()
        self.client.post(f'/api/v1/atendimentos/{case}/mensagens/', {'texto': 'Nova informação fictícia', 'client_id': str(uuid4())}, format='json')
        self.assertEqual(self.edit_draft(case, first, first['corpo'] + '\nAlteração')[0].status_code, 409)
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{case}/minutas/{first['id']}/exportar/", {'formato': 'docx'}).status_code, 409)

    def test_invalid_edit_and_unauthorized_export_are_rejected(self):
        case, first = self.draft_for_editing()
        for text in ['  ', '{{campo_pendente}}', 'Texto\x00inválido']:
            self.assertEqual(self.edit_draft(case, first, text)[0].status_code, 400)
        hidden = Atendimento.objects.create(tenant=self.other, criado_por=self.user, titulo='Isolado')
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{hidden.id}/minutas/{first['id']}/exportar/", {'formato': 'docx'}).status_code, 404)

    def test_pdf_does_not_silently_replace_unsupported_characters(self):
        case, first = self.draft_for_editing()
        saved, _ = self.edit_draft(case, first, first['corpo'] + '\n\U0001f680')
        self.assertEqual(saved.status_code, 201)
        self.review_draft(case, saved.data)
        response = self.client.get(f"/api/v1/atendimentos/{case}/minutas/{saved.data['id']}/exportar/", {'formato': 'pdf'})
        self.assertEqual(response.status_code, 400)

    def test_pdf_paginates_long_text_without_losing_the_end(self):
        from types import SimpleNamespace
        from django.utils import timezone
        from apps.processos.exportacao import pdf
        from pypdf import PdfReader
        text = '\n'.join(f'Parágrafo fictício {i}: revisão de conteúdo e dados sem validade.' for i in range(140))
        text += '\n' + 'A' * 500 + '\nFIM DO TESTE FICTICIO'
        draft = SimpleNamespace(corpo=text, versao=1, tipo='editada', created_at=timezone.now(), modelo=SimpleNamespace(versao=1))
        reader = PdfReader(BytesIO(pdf(draft)))
        self.assertGreater(len(reader.pages), 1)
        self.assertIn('FIM DO TESTE FICTICIO', reader.pages[-1].extract_text())
