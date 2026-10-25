from rest_framework.test import APITestCase
from apps.processos.models import Atendimento, ModeloAtendimento, ModeloReutilizavel
from apps.processos.redacao import BASE
from tests import test_atendimentos as helpers

class BibliotecaModelosTests(APITestCase):
    setUp=helpers.AtendimentoTests.setUp

    def setup_cases(self):
        first=Atendimento.objects.create(tenant=self.tenant,criado_por=self.user,titulo='Origem fictícia')
        second=Atendimento.objects.create(tenant=self.tenant,criado_por=self.user,titulo='Destino fictício')
        model=ModeloAtendimento.objects.create(tenant=self.tenant,atendimento=first,autor=self.user,
            versao=1,aprovado=True,justificativa='Teste fictício',**BASE)
        return first,second,model

    def publish(self,case,model,confirm=True):
        return self.client.post(f'/api/v1/atendimentos/{case.id}/publicar-modelo/',
            {'modelo_id':str(model.id),'nome':'Padrão FICTÍCIO para revisão','confirmar_sem_dados':confirm},format='json')

    def test_publish_requires_explicit_confirmation_and_current_approved_source(self):
        source,_,model=self.setup_cases()
        self.assertEqual(self.publish(source,model,False).status_code,400)
        self.assertFalse(ModeloReutilizavel.objects.exists())
        self.assertEqual(self.publish(source,model).status_code,201)
        self.assertEqual(self.publish(source,model).status_code,200)
        self.assertEqual(ModeloReutilizavel.objects.count(),1)
        ModeloAtendimento.objects.create(tenant=self.tenant,atendimento=source,autor=self.user,
            versao=2,aprovado=False,justificativa='Nova revisão pendente',**BASE)
        self.assertEqual(self.publish(source,model).status_code,409)
        self.assertEqual(self.publish(source,source.modelos_minuta.first()).status_code,409)

    def test_library_reuse_preserves_source_and_does_not_inherit_approval(self):
        source,target,model=self.setup_cases()
        published=self.publish(source,model).data
        library=self.client.get('/api/v1/atendimentos/biblioteca-modelos/',{'busca':'FICTÍCIO'})
        self.assertEqual(library.status_code,200)
        self.assertEqual(library['Cache-Control'],'no-store')
        self.assertEqual(library.data['modelos'][0]['corpo'],model.corpo)
        self.assertNotIn('dados',library.data['modelos'][0])
        self.assertNotIn('atendimento_id',library.data['modelos'][0])
        payload={**BASE,'referencia_id':published['id'],'aprovado':False,'versao_esperada':0,'justificativa':'Revisar padrão no novo caso'}
        response=self.client.post(f'/api/v1/atendimentos/{target.id}/modelo-minuta/',payload,format='json')
        self.assertEqual(response.status_code,201)
        self.assertFalse(response.data['aprovado'])
        self.assertEqual(response.data['referencia_id'],published['id'])
        self.assertFalse(self.client.get(f'/api/v1/atendimentos/{target.id}/minuta-preparada/').data['pronto'])
        self.assertFalse(target.revisoes.exists())
        self.assertFalse(target.minutas_preparadas.exists())
        model.refresh_from_db(); self.assertEqual(model.versao,1)
        self.assertEqual(model.corpo,BASE['corpo'])

    def test_tenant_isolation_for_catalog_publication_and_import(self):
        source,target,model=self.setup_cases()
        item=self.publish(source,model).data
        hidden=Atendimento.objects.create(tenant=self.other,criado_por=self.user,titulo='Outro cartório')
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        # This user cannot access the other tenant at all.
        self.assertIn(self.client.get('/api/v1/atendimentos/biblioteca-modelos/').status_code,[403,404])
        self.user.profile.tenants.add(self.other)
        self.assertEqual(self.client.get('/api/v1/atendimentos/biblioteca-modelos/').data['modelos'],[])
        payload={**BASE,'referencia_id':item['id'],'aprovado':False,'versao_esperada':0,'justificativa':'Teste de isolamento'}
        self.assertEqual(self.client.post(f'/api/v1/atendimentos/{hidden.id}/modelo-minuta/',payload,format='json').status_code,404)
        self.assertEqual(self.publish(hidden,model).status_code,404)

    def test_new_source_version_does_not_mutate_published_pattern(self):
        source,_,model=self.setup_cases()
        self.publish(source,model)
        ModeloAtendimento.objects.create(tenant=self.tenant,atendimento=source,autor=self.user,
            versao=2,aprovado=True,justificativa='Padrão modificado',**{**BASE,'corpo':'NOVA VERSÃO FICTÍCIA\n'+BASE['corpo']})
        self.assertEqual(ModeloReutilizavel.objects.get().corpo,BASE['corpo'])
