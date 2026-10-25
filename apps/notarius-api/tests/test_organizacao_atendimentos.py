from uuid import uuid4
from rest_framework.test import APITestCase
from apps.processos.models import Atendimento
from apps.processos.redacao import snapshot
from tests import test_atendimentos as helpers

class OrganizacaoAtendimentoTests(APITestCase):
    setUp=helpers.AtendimentoTests.setUp

    def case(self,title='Caso fictício'):
        return self.client.post('/api/v1/atendimentos/',{'titulo':title},format='json').data

    def organize(self,case,state='pausado',version=1,title='Caso renomeado'):
        return self.client.post(f"/api/v1/atendimentos/{case['id']}/organizacao/",{'titulo':title,'situacao':state,'versao_esperada':version,'motivo':'Organização fictícia para teste'},format='json')

    def test_pause_resume_preserves_messages_draft_snapshot_and_audit(self):
        case=self.case()
        self.client.post(f"/api/v1/atendimentos/{case['id']}/mensagens/",{'texto':'Informação fictícia preservada','client_id':str(uuid4())},format='json')
        instance=Atendimento.objects.get(pk=case['id'])
        before=snapshot(instance)[2]
        saved=self.organize(case)
        self.assertEqual(saved.status_code,200)
        self.assertEqual(saved.data['situacao'],'pausado')
        self.assertEqual(saved.data['versao_cadastro'],2)
        self.assertEqual(snapshot(instance)[2],before)
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{case['id']}/mensagens/").data[0]['texto'],'Informação fictícia preservada')
        restored=self.organize(case,state='em_andamento',version=2)
        self.assertEqual(restored.status_code,200)
        history=self.client.get(f"/api/v1/atendimentos/{case['id']}/organizacao/")
        self.assertEqual(history['Cache-Control'],'no-store')
        self.assertEqual([event['versao'] for event in history.data['historico']],[3,2])
        self.assertEqual(history.data['historico'][-1]['titulo_anterior'],case['titulo'])
        self.assertEqual(history.data['historico'][0]['situacao_anterior'],'pausado')

    def test_stale_write_invalid_status_and_empty_reason_are_rejected(self):
        case=self.case()
        self.assertEqual(self.organize(case).status_code,200)
        self.assertEqual(self.organize(case,title='Sobrescrever indevidamente').status_code,409)
        self.assertEqual(self.organize(case,state='concluido',version=2).status_code,400)
        url=f"/api/v1/atendimentos/{case['id']}/organizacao/"
        self.assertEqual(self.client.post(url,{'titulo':'Teste','situacao':'pausado','versao_esperada':2,'motivo':' '},format='json').status_code,400)
        self.assertEqual(len(self.client.get(url).data['historico']),1)

    def test_search_and_status_filter_remain_scoped_to_tenant(self):
        first=self.case('ALFA FICTÍCIO')
        second=self.case('BETA FICTÍCIO')
        self.organize(first,title='ALFA RENOMEADO',state='aguardando')
        Atendimento.objects.create(tenant=self.other,criado_por=self.user,titulo='ALFA OCULTO',situacao='aguardando')
        found=self.client.get('/api/v1/atendimentos/',{'busca':'ALFA','situacao':'aguardando'})
        self.assertEqual([item['id'] for item in found.data],[first['id']])
        self.assertEqual(self.client.get('/api/v1/atendimentos/',{'situacao':'concluido'}).status_code,400)
        self.assertEqual(len(self.client.get('/api/v1/atendimentos/').data),2)
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{second['id']}/",{'busca':'ALFA','situacao':'pausado'}).status_code,200)

    def test_organization_history_cannot_be_read_or_changed_in_another_tenant(self):
        case=self.case()
        self.organize(case)
        self.user.profile.tenants.add(self.other)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{case['id']}/organizacao/").status_code,404)
        self.assertEqual(self.organize(case,version=2).status_code,404)
