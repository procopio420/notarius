from django.test import SimpleTestCase
from rest_framework.test import APITestCase
from apps.processos.comparacao_minutas import comparar_textos
from apps.processos.models import Atendimento, ModeloAtendimento, MinutaAtendimento
from tests import test_atendimentos as helpers

class ComparacaoTextoTests(SimpleTestCase):
    def test_exact_reconstruction_preserves_unicode_whitespace_and_line_endings(self):
        samples=[('', ''), ('a\r\nb\n', 'a\r\nc\n'), ('á <tag> &\n\n fim', 'á <tag> &\n\n fim\n'),
                 ('Preço R$ 100.000,00', 'Preço R$ 200.000,00'), ('linha\n'*1600, 'nova\n'*1600)]
        for old,new in samples:
            parts,_=comparar_textos(old,new)
            self.assertEqual(''.join(p['texto'] for p in parts if p['tipo']!='adicionado'),old)
            self.assertEqual(''.join(p['texto'] for p in parts if p['tipo']!='removido'),new)
        self.assertTrue(comparar_textos(samples[-1][0],samples[-1][1])[1])

class ComparacaoEndpointTests(APITestCase):
    setUp=helpers.AtendimentoTests.setUp

    def make_version(self,case,version,text,data=None):
        model,_=ModeloAtendimento.objects.get_or_create(atendimento=case,versao=1,
            defaults={'tenant':self.tenant,'autor':self.user,'corpo':'FICTÍCIO','justificativa':'Teste'})
        return MinutaAtendimento.objects.create(atendimento=case,tenant=self.tenant,modelo=model,
            versao=version,corpo=text,dados=data or {},assinatura=str(version)*64,autor=self.user)

    def test_comparison_detects_record_change_even_when_value_is_identical(self):
        case=Atendimento.objects.create(tenant=self.tenant,criado_por=self.user,titulo='TESTE COMPARAÇÃO')
        first=self.make_version(case,1,'Texto anterior\n',{'preco':{'valor':'100','versao':1,'situacao':'confirmado'}})
        second=self.make_version(case,2,'Texto depois\n',{'preco':{'valor':'100','versao':2,'situacao':'confirmado'}})
        response=self.client.get(f'/api/v1/atendimentos/{case.id}/comparar-minutas/',{'base':first.id,'destino':second.id})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response['Cache-Control'],'no-store')
        self.assertTrue(response.data['texto_alterado'])
        self.assertEqual(response.data['dados_alterados'][0]['rotulo'],'Preço')
        self.assertFalse(response.data['dados_alterados'][0]['valor_alterado'])
        self.assertEqual(MinutaAtendimento.objects.count(),2)
        first.refresh_from_db(); self.assertEqual(first.corpo,'Texto anterior\n')
        # Merely comparing does not make a draft current or exportable.
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{case.id}/minutas/{second.id}/exportar/',{'formato':'pdf'}).status_code,409)

    def test_cross_case_and_cross_tenant_versions_are_rejected(self):
        case=Atendimento.objects.create(tenant=self.tenant,criado_por=self.user,titulo='Visível')
        other=Atendimento.objects.create(tenant=self.tenant,criado_por=self.user,titulo='Outro')
        first=self.make_version(case,1,'Um')
        foreign=self.make_version(other,1,'Dois')
        url=f'/api/v1/atendimentos/{case.id}/comparar-minutas/'
        self.assertEqual(self.client.get(url,{'base':first.id,'destino':foreign.id}).status_code,404)
        self.assertEqual(self.client.get(url,{'base':'invalid','destino':first.id}).status_code,400)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertIn(self.client.get(url,{'base':first.id,'destino':first.id}).status_code,[403,404])
