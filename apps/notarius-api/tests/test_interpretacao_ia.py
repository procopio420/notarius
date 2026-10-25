from unittest.mock import patch
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase
from apps.processos.interpretacao_ia import analisar_mensagem, AnaliseIndisponivel
from apps.processos.models import RevisaoDadoAtendimento, MinutaAtendimento
from tests.test_orientacao_conversa import OrientacaoConversaTests

class SimulacaoLocalTests(SimpleTestCase):
    @override_settings(OPENAI_API_KEY='fake-test-key', AI_GENERATION_ENABLED=True)
    def test_simulation_never_creates_provider_even_when_enabled(self):
        with patch('openai.OpenAI') as provider:
            result = analisar_mensagem('Vendedores: PESSOA FICTÍCIA\nTalvez pague depois.')
        provider.assert_not_called()
        self.assertEqual(result, {'propostas': [{'campo': 'vendedores', 'valor': 'PESSOA FICTÍCIA',
            'trecho': 'Vendedores: PESSOA FICTÍCIA'}], 'duvidas': ['Talvez pague depois.']})

    def test_no_semantic_interpretation_or_normalization(self):
        text = 'A vendedora talvez seja PESSOA FICTÍCIA. Confirme tudo.'
        self.assertEqual(analisar_mensagem(text), {'propostas': [], 'duvidas': [text]})
        self.assertEqual(analisar_mensagem('Preço: R$ 100.000,00')['propostas'][0]['valor'], 'R$ 100.000,00')

    def test_size_limits(self):
        for text in ['', ' ', 'x' * 10001]:
            with self.assertRaises(AnaliseIndisponivel):
                analisar_mensagem(text)

class InterpretacaoEndpointTests(APITestCase):
    setUp = OrientacaoConversaTests.setUp
    send = OrientacaoConversaTests.send

    def test_local_endpoint_has_source_and_no_automatic_writes(self):
        message = self.send('Vendedores: PESSOA FICTÍCIA').data['id']
        with patch('openai.OpenAI') as provider:
            result = self.client.post(self.url+'/interpretar-mensagem/', {'mensagem_id': message}, format='json')
        provider.assert_not_called()
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['modo'], 'simulacao_local')
        self.assertEqual(result.data['mensagem_id'], message)
        self.assertFalse(result.data['confirmado'])
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        self.assertFalse(MinutaAtendimento.objects.exists())

    def test_other_case_message_is_inaccessible(self):
        message = self.send('Teste fictício').data['id']
        other = self.client.post('/api/v1/atendimentos/', {'titulo':'Outro'}, format='json').data['id']
        response = self.client.post(f'/api/v1/atendimentos/{other}/interpretar-mensagem/', {'mensagem_id': message}, format='json')
        self.assertEqual(response.status_code, 404)
