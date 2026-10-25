from io import BytesIO
from uuid import uuid4
from unittest.mock import patch
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.processos.models import Atendimento, AnexoAtendimento, RevisaoDadoAtendimento
from apps.processos.leitura_anexos import ler_pdf
from tests import test_ficha_estruturada as base


def pdf_ficticio(texts):
    from reportlab.pdfgen import canvas
    stream = BytesIO(); document = canvas.Canvas(stream)
    for text in texts:
        if text:
            document.drawString(50, 750, text)
        document.showPage()
    document.save(); return stream.getvalue()


class OrganizacaoAnexosTests(APITestCase):
    setUp = base.FichaEstruturadaTests.setUp
    create_case = base.FichaEstruturadaTests.create_case
    get = base.FichaEstruturadaTests.get
    post = base.FichaEstruturadaTests.post
    obj = base.FichaEstruturadaTests.obj

    def upload(self, case, content=b'Nome: PESSOA FICTICIA ALFA', name='FICTICIO.txt', result=None):
        with patch('apps.processos.views.extrair_pdf', return_value=result) if result else patch('apps.processos.views.extrair_pdf', side_effect=ler_pdf):
            response = self.client.post(f'/api/v1/atendimentos/{case}/anexos/', {'arquivo': SimpleUploadedFile(name, content)}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def classify(self, case, file, links=None, **kw):
        data = {'client_id': str(uuid4()), 'versao_esperada': file['organizacao']['versao'], 'leitura_versao': file['leitura_versao'],
                'finalidade': 'caso', 'tipo_documento': 'Identificação FICTÍCIA', 'vinculos': links or [],
                'motivo': 'DECISÃO HUMANA SIMULADA: tipo e destinatários do documento fictício', 'conferi': True, **kw}
        return self.client.post(f"/api/v1/atendimentos/{case}/anexos/{file['id']}/organizacao/", data, format='json'), data

    def file(self, case, fid):
        return next(a for a in self.client.get(f'/api/v1/atendimentos/{case}/anexos/').data if a['id'] == fid)

    def source(self, case, obj, file, page=0, value='PESSOA FICTICIA ALFA', **kw):
        p = file['paginas'][page]
        data = {'client_id': str(uuid4()), 'modelo_id': self.get(case).data['modelo_id'], 'operacao': 'salvar', 'objeto_id': obj,
                'justificativa': 'CONFIRMAÇÃO SIMULADA EM TESTE, COM VÍNCULO EXPLÍCITO', 'campos': [{
                    'chave': 'nome', 'valor': value, 'valor_original': value, 'origem': 'documento', 'situacao': 'confirmado',
                    'versao_esperada': 0, 'confirmar': True, 'conferir_fonte': True, 'pagina_id': p['id'],
                    'leitura_versao': file['leitura_versao'], 'organizacao_versao': file['organizacao']['versao'],
                    'trecho_origem': p['texto'], **kw}]}
        return self.client.post(f'/api/v1/atendimentos/{case}/ficha-detalhada/', data, format='json')

    def test_multpage_similar_names_explicit_page_owners_and_original_preserved(self):
        case = self.create_case(); a = self.obj(case); b = self.obj(case)
        raw = pdf_ficticio(['Nome: PESSOA FICTICIA ALFA', 'Nome: PESSOA FICTICIA ALFA B', ''])
        with patch('apps.processos.leitura_anexos.executar_ocr', return_value={'texto_ocr': '', 'regioes_ocr': [], 'ocr_erro': 'OCR SIMULADO: sem texto'}), patch('apps.processos.leitura_anexos.rasterizar_pagina', return_value=b'FICTICIO'):
            file = self.upload(case, raw, 'MULTIPESSOAS-FICTICIO.pdf')
        self.assertEqual(file['cobertura']['total_paginas'], 3)
        self.assertEqual(file['cobertura']['paginas_sem_texto'], [3])
        self.assertEqual(file['organizacao']['finalidade'], 'pendente')
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        self.assertEqual(self.source(case, a, file).status_code, 400)
        response, _ = self.classify(case, file, [{'objeto_id': a, 'paginas': [1]}, {'objeto_id': b, 'paginas': [2]}, {'objeto_id': None, 'paginas': [3]}])
        self.assertEqual(response.status_code, 201, response.data)
        file = self.file(case, file['id'])
        self.assertEqual(self.source(case, b, file).status_code, 400)
        self.assertEqual(self.source(case, a, file).status_code, 201)
        self.assertEqual(self.source(case, b, file, page=1, value='PESSOA FICTICIA ALFA B').status_code, 201)
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{case}/anexos/{file['id']}/download/").content, raw)
        self.assertEqual(bytes(AnexoAtendimento.objects.get(id=file['id']).conteudo), raw)
        self.assertEqual(self.file(case, file['id'])['sha256'], file['sha256'])

    def test_reference_document_cannot_feed_case_even_with_literal_excerpt(self):
        case = self.create_case(); person = self.obj(case); file = self.upload(case)
        extracted = self.client.post(f'/api/v1/atendimentos/{case}/propostas-dados/', {'operacao': 'extrair', 'client_id': str(uuid4()), 'anexo_id': file['id'], 'leitura_versao': 1}, format='json')
        self.assertEqual(extracted.status_code, 201)
        result, _ = self.classify(case, file, finalidade='referencia_redacao', tipo_documento='Exemplo de redação FICTÍCIO')
        self.assertEqual(result.status_code, 201, result.data)
        file = self.file(case, file['id'])
        self.assertEqual(self.source(case, person, file).status_code, 400)
        self.assertEqual(self.source(case, person, file, situacao='informado', confirmar=False).status_code, 400)
        blocked = self.client.post(f'/api/v1/atendimentos/{case}/propostas-dados/', {'operacao': 'extrair', 'client_id': str(uuid4()), 'anexo_id': file['id'], 'leitura_versao': 1}, format='json')
        self.assertEqual(blocked.status_code, 400)
        proposal = self.client.get(f'/api/v1/atendimentos/{case}/propostas-dados/').data['propostas'][0]
        self.assertEqual(proposal['situacao'], 'referencia_redacao')
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        other = self.create_case(); other_person = self.obj(other)
        self.assertEqual(self.source(other, other_person, file).status_code, 404)

    def test_correction_reopens_sources_and_keeps_classification_history(self):
        case = self.create_case(); a = self.obj(case); b = self.obj(case); file = self.upload(case)
        self.assertEqual(self.classify(case, file, [{'objeto_id': a, 'paginas': []}])[0].status_code, 201)
        old_file = self.file(case, file['id'])
        self.assertEqual(self.source(case, a, old_file).status_code, 201)
        self.assertEqual(self.classify(case, old_file, [{'objeto_id': b, 'paginas': []}], motivo='CORREÇÃO HUMANA FICTÍCIA DE DESTINATÁRIO')[0].status_code, 201)
        person = next(o for o in self.get(case).data['objetos'] if o['id'] == a)
        field = next(f for f in person['campos'] if f['chave'] == 'nome')
        self.assertEqual(field['atual']['valor'], 'PESSOA FICTICIA ALFA')
        self.assertEqual(field['atual']['situacao_efetiva'], 'reaberta')
        self.assertFalse(field['atual']['confirmacao_atual'])
        self.assertEqual(self.source(case, b, old_file).status_code, 409)
        history = self.client.get(f"/api/v1/atendimentos/{case}/anexos/{file['id']}/organizacao/").data['historico']
        self.assertEqual([h['versao'] for h in history], [2, 1])
        self.assertEqual(history[1]['vinculos'][0]['objeto_id'], a)

    def test_idempotence_stale_decision_and_isolation(self):
        case = self.create_case(); person = self.obj(case); file = self.upload(case)
        response, data = self.classify(case, file, [{'objeto_id': person, 'paginas': []}]); self.assertEqual(response.status_code, 201)
        url = f"/api/v1/atendimentos/{case}/anexos/{file['id']}/organizacao/"
        self.assertEqual(self.client.post(url, data, format='json').status_code, 200)
        self.assertEqual(self.client.post(url, {**data, 'client_id': str(uuid4())}, format='json').status_code, 409)
        other = self.create_case(); other_person = self.obj(other)
        self.assertEqual(self.classify(case, self.file(case, file['id']), [{'objeto_id': other_person, 'paginas': []}])[0].status_code, 404)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, data, format='json').status_code, 403)

    def test_shared_document_property_and_reference_correction_reopen_used_data(self):
        from apps.processos.organizacao_anexos import permite
        from apps.processos.models import ObjetoFichaAtendimento
        case = self.create_case(); a = self.obj(case); b = self.obj(case); home = self.obj(case, 'imovel')
        file = self.upload(case)
        self.assertEqual(self.classify(case, file, [{'objeto_id': oid, 'paginas': [1]} for oid in [a, b, home]])[0].status_code, 201)
        joint = self.obj(case, 'relacao', pessoa_a_id=a, pessoa_b_id=b)
        attachment = AnexoAtendimento.objects.get(id=file['id'])
        self.assertTrue(permite(attachment, ObjetoFichaAtendimento.objects.get(id=joint), 1))
        self.assertTrue(permite(attachment, ObjetoFichaAtendimento.objects.get(id=home), 1))
        self.assertFalse(permite(attachment, None, 1))
        file = self.file(case, file['id'])
        self.assertEqual(self.source(case, a, file).status_code, 201)
        self.assertEqual(self.classify(case, file, finalidade='referencia_redacao')[0].status_code, 201)
        field = next(f for o in self.get(case).data['objetos'] if o['id'] == a for f in o['campos'] if f['chave'] == 'nome')
        self.assertEqual(field['atual']['situacao_efetiva'], 'reaberta')
        self.assertEqual(field['atual']['valor'], 'PESSOA FICTICIA ALFA')
        self.assertFalse(field['atual']['fonte_atual'])

    def test_rereading_preserves_old_pages_and_requires_new_source_and_link_review(self):
        case = self.create_case(); person = self.obj(case)
        result = {'situacao': 'extraido', 'aviso': 'LEITURA SIMULADA', 'paginas': [{'numero': 1, 'texto': 'Nome: PESSOA FICTICIA ALFA', 'situacao': 'extraido', 'aviso': 'SIMULAÇÃO'}], 'metadados_leitura': {'total_paginas': 1}}
        raw = pdf_ficticio(['Nome: PESSOA FICTICIA ALFA']); file = self.upload(case, raw, 'FICTICIO.pdf', result)
        self.classify(case, file, [{'objeto_id': person, 'paginas': [1]}]); file = self.file(case, file['id'])
        self.assertEqual(self.source(case, person, file).status_code, 201)
        with patch('apps.processos.views.extrair_pdf', return_value=result):
            reread = self.client.post(f"/api/v1/atendimentos/{case}/anexos/{file['id']}/reler/", {'leitura_versao': 1}, format='json')
        self.assertEqual(reread.status_code, 200, reread.data)
        self.assertFalse(reread.data['organizacao']['leitura_atual'])
        self.assertNotEqual(reread.data['paginas'][0]['id'], file['paginas'][0]['id'])
        self.assertEqual(AnexoAtendimento.objects.get(id=file['id']).paginas.count(), 2)
        self.assertEqual(self.source(case, person, file, versao_esperada=1).status_code, 409)
        self.assertEqual(self.source(case, person, reread.data, versao_esperada=1).status_code, 400)
        self.assertEqual(self.classify(case, reread.data, [{'objeto_id': person, 'paginas': [1]}])[0].status_code, 201)
        latest = self.file(case, file['id'])
        self.assertEqual(self.source(case, person, latest, versao_esperada=1).status_code, 201)
        self.assertEqual(bytes(AnexoAtendimento.objects.get(id=file['id']).conteudo), raw)

    def test_page_and_ocr_limits_are_visible_and_not_reported_as_absent_facts(self):
        with patch('apps.processos.leitura_anexos.executar_ocr', return_value={'texto_ocr': 'OCR FICTICIO', 'regioes_ocr': []}), patch('apps.processos.leitura_anexos.rasterizar_pagina', return_value=b'FICTICIO'):
            truncated = ler_pdf(pdf_ficticio(['X' * 50001]))
        self.assertEqual(len(truncated['paginas'][0]['texto']), 50000)
        self.assertIn('texto_50000', truncated['paginas'][0]['limites_leitura'])
        self.assertIn('truncado', truncated['paginas'][0]['aviso'])
        raw = pdf_ficticio([''] * 41)
        limited = ler_pdf(raw)
        self.assertEqual(limited['metadados_leitura']['total_paginas'], 41)
        self.assertIn('quantidade_paginas', limited['metadados_leitura']['limites'])
        self.assertEqual(limited['paginas'], [])
        with patch('apps.processos.leitura_anexos.executar_ocr', return_value={'texto_ocr': '', 'regioes_ocr': [], 'ocr_erro': 'OCR SIMULADO: sem texto'}) as ocr, patch('apps.processos.leitura_anexos.rasterizar_pagina', return_value=b'FICTICIO'):
            result = ler_pdf(pdf_ficticio([''] * 12))
        self.assertEqual(ocr.call_count, 10)
        self.assertIn('ocr_10_paginas', result['paginas'][10]['limites_leitura'])
        case = self.create_case(); file = self.upload(case, raw, 'LIMITE-FICTICIO.pdf', limited)
        self.assertEqual(file['cobertura']['paginas_processadas'], 0)
        self.assertIn('não significa inexistência', file['cobertura']['aviso'])
