from unittest.mock import patch

from rest_framework.test import APITestCase

from apps.processos.models import PropostaDadoAtendimento, RevisaoDadoAtendimento
from tests import test_organizacao_anexos as fixtures


class ComparacaoAnexosTests(APITestCase):
    setUp = fixtures.OrganizacaoAnexosTests.setUp
    create_case = fixtures.OrganizacaoAnexosTests.create_case
    get = fixtures.OrganizacaoAnexosTests.get
    post = fixtures.OrganizacaoAnexosTests.post
    obj = fixtures.OrganizacaoAnexosTests.obj
    upload = fixtures.OrganizacaoAnexosTests.upload
    classify = fixtures.OrganizacaoAnexosTests.classify
    file = fixtures.OrganizacaoAnexosTests.file

    def report(self, case):
        response = self.client.get(f'/api/v1/atendimentos/{case}/comparacao-anexos/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response['Cache-Control'], 'no-store')
        return response.data

    def test_new_attachment_updates_literal_evidence_without_confirming_payment(self):
        case = self.create_case()
        self.assertEqual(self.report(case)['grupos'], [])
        a = self.upload(case, 'Nome: ALFA\nPreço: R$ 100,00\nForma de pagamento: previsto por Pix'.encode(), 'alfa.txt')
        self.assertEqual(self.report(case)['total_sugestoes'], 3)
        b = self.upload(case, 'Nome: ALFA B\nPreço: R$ 200,00\nQuitação: não declarada'.encode(), 'beta.txt')
        groups = {group['campo']: group for group in self.report(case)['grupos']}
        self.assertEqual(groups['nome']['estado'], 'conferir_vinculo')
        self.assertIsNone(groups['nome']['objeto_id'])
        self.assertEqual(groups['preco']['estado'], 'possivel_divergencia')
        self.assertEqual(groups['condicoes']['fontes'][0]['trecho'], 'Forma de pagamento: previsto por Pix')
        self.assertEqual(groups['quitacao']['fontes'][0]['trecho'], 'Quitação: não declarada')
        self.assertIn('expressa de quitação', groups['quitacao']['pergunta'])
        sources = groups['preco']['fontes']
        self.assertEqual([source['anexo_id'] for source in sources], [a['id'], b['id']])
        self.assertEqual([source['trecho'] for source in sources], ['Preço: R$ 100,00', 'Preço: R$ 200,00'])
        self.assertEqual(sources[1]['pagina_id'], b['paginas'][0]['id'])
        self.assertEqual((sources[1]['pagina'], sources[1]['linha'], sources[1]['canal']), (1, 2, 'texto'))
        self.assertFalse(PropostaDadoAtendimento.objects.exists())
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        self.assertFalse(self.client.get(f'/api/v1/atendimentos/{case}/minuta-preparada/').data['pronto'])

    def test_document_owners_control_comparison_and_reference_is_excluded(self):
        case = self.create_case()
        first, second = self.obj(case), self.obj(case)
        a = self.upload(case, b'Nome: ALFA', 'a.txt')
        b = self.upload(case, b'Nome: ALFA B', 'b.txt')
        for file, owner in ((a, first), (b, second)):
            response, _ = self.classify(case, file, [{'objeto_id': owner, 'paginas': [1]}])
            self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual({group['estado'] for group in self.report(case)['grupos']}, {'sugestao'})
        response, _ = self.classify(case, self.file(case, b['id']), [{'objeto_id': first, 'paginas': [1]}])
        self.assertEqual(response.status_code, 201, response.data)
        group, = self.report(case)['grupos']
        self.assertEqual((group['estado'], group['objeto_id']), ('divergencia', first))
        response, _ = self.classify(case, self.file(case, b['id']), finalidade='referencia_redacao')
        self.assertEqual(response.status_code, 201, response.data)
        group, = self.report(case)['grupos']
        self.assertEqual([source['anexo_id'] for source in group['fontes']], [a['id']])
        self.assertEqual(self.report(self.create_case())['grupos'], [])
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{case}/comparacao-anexos/').status_code, 403)

    def test_rereading_replaces_evidence_and_mixed_channels_stay_uncertain(self):
        case = self.create_case()
        original = {'situacao': 'extraido', 'aviso': '', 'paginas': [
            {'numero': 1, 'texto': 'Nome: ALFA', 'situacao': 'extraido', 'aviso': ''}]}
        file = self.upload(case, fixtures.pdf_ficticio(['Nome: ALFA']), 'leitura.pdf', original)
        self.assertEqual(self.report(case)['grupos'][0]['fontes'][0]['trecho'], 'Nome: ALFA')
        updated = {**original, 'paginas': [
            {**original['paginas'][0], 'texto': 'Nome: BETA', 'texto_ocr': 'Nome: BETA B'}]}
        with patch('apps.processos.views.extrair_pdf', return_value=updated):
            response = self.client.post(f"/api/v1/atendimentos/{case}/anexos/{file['id']}/reler/",
                                        {'leitura_versao': 1}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        group, = self.report(case)['grupos']
        self.assertEqual(group['estado'], 'conferir_leitura')
        self.assertEqual({source['trecho'] for source in group['fontes']}, {'Nome: BETA', 'Nome: BETA B'})
        self.assertEqual({source['canal'] for source in group['fontes']}, {'texto', 'ocr'})
        self.assertTrue(all(source['leitura_versao'] == 2 and 'leitura_incerta' in source['problemas']
                            for source in group['fontes']))
