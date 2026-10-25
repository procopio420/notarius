from uuid import uuid4
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from apps.processos.models import Atendimento, FeedbackTesteAtendimento, MensagemAtendimento, RevisaoDadoAtendimento
from apps.processos.redacao import snapshot
from tests import test_atendimentos as helpers

class FeedbackTesteTests(APITestCase):
    setUp=helpers.AtendimentoTests.setUp
    create_case=helpers.AtendimentoTests.create_case

    def payload(self):
        return {'client_id':str(uuid4()),'etapa':'anexos','tipo':'duvida',
                'descricao':'TESTE FICTÍCIO: não entendi onde revisar a leitura.', 'esperado':'Encontrar uma indicação mais clara.'}

    def test_feedback_is_persistent_idempotent_and_does_not_change_evidence(self):
        case=self.create_case()
        url=f'/api/v1/atendimentos/{case}/feedbacks-teste/'
        instance=Atendimento.objects.get(pk=case)
        signature=snapshot(instance)[2]
        payload=self.payload()
        created=self.client.post(url,payload,format='json')
        self.assertEqual(created.status_code,201)
        self.assertEqual(self.client.post(url,payload,format='json').status_code,200)
        self.assertEqual(FeedbackTesteAtendimento.objects.count(),1)
        listed=self.client.get(url)
        self.assertEqual(listed['Cache-Control'],'no-store')
        self.assertEqual(listed.data[0]['descricao'],payload['descricao'])
        self.assertEqual(listed.data[0]['contexto']['assinatura_dados'],signature)
        self.assertIsNone(listed.data[0]['contexto']['minuta_versao'])
        self.assertEqual(snapshot(instance)[2],signature)
        self.assertFalse(MensagemAtendimento.objects.exists())
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        payload['descricao']='Tentar trocar um registro anterior'
        self.assertEqual(self.client.post(url,payload,format='json').status_code,400)

    def test_feedback_rejects_blank_oversized_and_unknown_categories(self):
        case=self.create_case();url=f'/api/v1/atendimentos/{case}/feedbacks-teste/'
        for changes in [{'descricao':' '},{'descricao':'x'*4001},{'esperado':'x'*2001},{'etapa':'desconhecida'},{'tipo':'aprovacao'}]:
            self.assertEqual(self.client.post(url,{**self.payload(),**changes},format='json').status_code,400)
        self.assertFalse(FeedbackTesteAtendimento.objects.exists())

    def test_case_tenant_and_author_isolation(self):
        case=self.create_case();url=f'/api/v1/atendimentos/{case}/feedbacks-teste/'
        payload=self.payload();self.client.post(url,payload,format='json')
        other=self.create_case()
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{other}/feedbacks-teste/').data,[])
        self.user.profile.tenants.add(self.other)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.post(url,payload,format='json').status_code,404)
        other_user=get_user_model().objects.create_user('feedback_other',password='ficticio')
        from apps.profiles.models import UserProfile
        profile,_=UserProfile.objects.get_or_create(user=other_user);profile.tenants.add(self.tenant)
        self.client.force_authenticate(other_user)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
        self.assertEqual(self.client.post(url,payload,format='json').status_code,400)
        self.assertEqual(FeedbackTesteAtendimento.objects.count(),1)

    def test_context_is_server_generated_not_client_claimed(self):
        case=self.create_case();url=f'/api/v1/atendimentos/{case}/feedbacks-teste/'
        response=self.client.post(url,{**self.payload(),'contexto':{'minuta_versao':999,'pendencias':0}},format='json')
        self.assertEqual(response.status_code,201)
        self.assertIsNone(response.data['contexto']['minuta_versao'])
        self.assertGreater(response.data['contexto']['pendencias'],0)
