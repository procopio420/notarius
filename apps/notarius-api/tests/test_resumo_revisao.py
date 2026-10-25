from uuid import uuid4
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from apps.processos.models import Atendimento, RevisaoDadoAtendimento, MinutaAtendimento, DecisaoConferencia
from tests import test_atendimentos as helpers

class ResumoRevisaoTests(APITestCase):
    setUp=helpers.AtendimentoTests.setUp
    create_case=helpers.AtendimentoTests.create_case
    report=helpers.AtendimentoTests.report
    answer=helpers.AtendimentoTests.answer
    ready_for_draft=helpers.AtendimentoTests.ready_for_draft
    save_template=helpers.AtendimentoTests.save_template
    generate_draft=helpers.AtendimentoTests.generate_draft

    def summary(self,case):
        return self.client.get(f'/api/v1/atendimentos/{case}/resumo-revisao/')

    def test_empty_case_is_explicitly_incomplete_and_read_only(self):
        case=self.create_case()
        response=self.summary(case)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response['Cache-Control'],'no-store')
        self.assertFalse(response.data['pronto_para_preparar'])
        self.assertEqual(len(response.data['campos']),7)
        self.assertTrue(all(f['atual'] is None for f in response.data['campos']))
        self.assertIsNone(response.data['modelo'])
        self.assertIsNone(response.data['minuta'])
        self.assertTrue(response.data['pendencias'])
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        self.assertFalse(MinutaAtendimento.objects.exists())
        self.assertFalse(DecisaoConferencia.objects.exists())

    def test_ready_state_matches_generation_and_new_message_marks_draft_stale(self):
        case=self.ready_for_draft()
        self.save_template(case)
        self.generate_draft(case)
        ready=self.summary(case).data
        self.assertTrue(ready['pronto_para_preparar'])
        self.assertEqual(ready['pendencias'],[])
        self.assertIsNotNone(ready['documentos'][0]['revisao_manual'])
        self.assertFalse(ready['minuta']['desatualizada'])
        self.assertEqual(ready['assinatura'],self.client.get(f'/api/v1/atendimentos/{case}/minuta-preparada/').data['assinatura'])
        self.client.post(f'/api/v1/atendimentos/{case}/mensagens/',{'texto':'Compradores: OUTRA PESSOA FICTÍCIA','client_id':str(uuid4())},format='json')
        changed=self.summary(case).data
        self.assertFalse(changed['pronto_para_preparar'])
        self.assertTrue(changed['minuta']['desatualizada'])
        self.assertTrue(any(q['chave']=='compradores' for q in changed['pendencias']))
        self.assertEqual(MinutaAtendimento.objects.count(),1)

    def test_sources_and_unreviewed_document_remain_visible(self):
        case=self.create_case()
        attachment=self.client.post(f'/api/v1/atendimentos/{case}/anexos/',{'arquivo':SimpleUploadedFile('FICTICIO.txt',b'Preco: R$ 100.000,00')},format='multipart').data
        self.client.post(f'/api/v1/atendimentos/{case}/ficha/',{
            'chave':'preco','valor':'R$ 100.000,00','situacao':'informado', 'versao_esperada':0, 'organizacao_versao':0,
            'pagina_id':attachment['paginas'][0]['id'],'trecho_origem':'Preco: R$ 100.000,00',
            'justificativa':'Trecho fictício ainda sem confirmação'},format='json')
        response=self.summary(case)
        field=next(f for f in response.data['campos'] if f['chave']=='preco')['atual']
        self.assertEqual(field['situacao'],'informado')
        self.assertEqual(field['origem']['trecho'],'Preco: R$ 100.000,00')
        self.assertEqual(field['origem']['arquivo'],'FICTICIO.txt')
        self.assertIsNone(response.data['documentos'][0]['revisao_manual'])
        self.assertNotIn('conteudo',response.data['documentos'][0])

    def test_tenant_isolation_and_change_during_summary(self):
        hidden=Atendimento.objects.create(tenant=self.other,criado_por=self.user,titulo='Não acessar')
        self.assertEqual(self.summary(hidden.id).status_code,404)
        case=self.create_case()
        with patch('apps.processos.resumo_revisao.snapshot',side_effect=[(None,{},'before'),(None,{},'after')]):
            self.assertEqual(self.summary(case).status_code,409)
