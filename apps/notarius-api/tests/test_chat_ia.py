import json
import os
from uuid import uuid4
from unittest import skipUnless
from unittest.mock import patch
from django.test import override_settings
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase
from tests import test_atendimentos as helpers
from apps.processos.models import Atendimento, MensagemAtendimento, RespostaChatIA
from apps.processos.orcamento_documental import OrcamentoBloqueado
from apps.processos import chat_ia
from apps.processos.chat_ia import interpretar


def envelope(text='Confira o original.', citations=None):
    return {'status': 'completed', 'usage': {'input_tokens': 10, 'output_tokens': 10},
            'output': [{'type': 'message', 'role': 'assistant', 'status': 'completed', 'content': [
                {'type': 'output_text', 'text': json.dumps({'resposta': text, 'citacoes': citations or []})}]}]}


class ChatIATests(APITestCase):
    setUp = helpers.AtendimentoTests.setUp
    create_case = helpers.AtendimentoTests.create_case

    def prepare(self):
        case = self.create_case()
        self.url = f'/api/v1/atendimentos/{case}/chat-ia/'
        message = self.client.post(f'/api/v1/atendimentos/{case}/mensagens/',
            {'texto': 'EXERCÍCIO FICTÍCIO: o que falta?', 'client_id': str(uuid4())}, format='json')
        self.assertEqual(message.status_code, 201, message.data)
        return case, {'mensagem_id': message.data['id']}

    def test_saved_answer_replay_and_reload_never_resend(self):
        case, payload = self.prepare()
        with patch('apps.processos.chat_ia.habilitado', return_value=True), patch('apps.processos.chat_ia.enviar', return_value=envelope()) as send:
            first = self.client.post(self.url, payload, format='json')
            second = self.client.post(self.url, payload, format='json')
            loaded = self.client.get(self.url)
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data['respostas'][0]['estado'], 'concluido')
        self.assertEqual(second.data['respostas'], loaded.data['respostas'])
        send.assert_called_once()
        self.assertFalse(Atendimento.objects.get(pk=case).revisoes.exists())

    def test_failed_budget_is_persisted_without_retry(self):
        _, payload = self.prepare()
        with patch('apps.processos.chat_ia.habilitado', return_value=True), patch('apps.processos.chat_ia.enviar', side_effect=OrcamentoBloqueado('Teto atingido')) as send:
            result = self.client.post(self.url, payload, format='json')
            self.client.post(self.url, payload, format='json')
        self.assertEqual(result.data['respostas'][0]['codigo'], 'orcamento_bloqueado')
        send.assert_called_once()

    def test_attachment_added_during_analysis_invalidates_the_answer(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        case, payload = self.prepare()

        def send_with_new_attachment(_request):
            uploaded = self.client.post(f'/api/v1/atendimentos/{case}/anexos/', {
                'arquivo': SimpleUploadedFile('preco.txt', b'Preco: R$ 300.000,00'),
            }, format='multipart')
            self.assertEqual(uploaded.status_code, 201, uploaded.data)
            return envelope('Resposta baseada na leitura anterior.')

        with patch('apps.processos.chat_ia.habilitado', return_value=True), patch(
            'apps.processos.chat_ia.enviar', side_effect=send_with_new_attachment,
        ) as send:
            result = self.client.post(self.url, payload, format='json')
            loaded = self.client.get(self.url)
            self.client.post(self.url, payload, format='json')

        self.assertEqual(result.status_code, 200, result.data)
        answer, = result.data['respostas']
        self.assertEqual((answer['estado'], answer['codigo']), ('falha', 'evidencia_invalida'))
        self.assertNotIn('Resposta baseada na leitura anterior.', answer['texto'])
        self.assertEqual(loaded.data['respostas'], [answer])
        self.assertFalse(Atendimento.objects.get(pk=case).revisoes.exists())
        send.assert_called_once()

    def test_disabled_and_other_case_message_never_send(self):
        _, payload = self.prepare()
        with patch('apps.processos.chat_ia.habilitado', return_value=False), patch('apps.processos.chat_ia.enviar') as send:
            self.assertEqual(self.client.post(self.url, payload, format='json').status_code, 400)
            other = self.create_case()
            self.assertEqual(self.client.post(f'/api/v1/atendimentos/{other}/chat-ia/', payload, format='json').status_code, 404)
        send.assert_not_called()

    def test_real_or_unknown_environment_blocks_external_chat_despite_global_flag(self):
        _, payload = self.prepare()
        for environment in ('real', None):
            with self.subTest(environment=environment), override_settings(NOTARIUS_AMBIENTE=environment), patch(
                'apps.processos.chat_ia.Path.is_file', return_value=True,
            ), patch('apps.processos.chat_ia.montar') as build, patch(
                'apps.processos.chat_ia.reservar',
            ) as reserve, patch('apps.processos.chat_ia.OpenAI') as client:
                state = self.client.get(self.url)
                self.assertFalse(state.data['habilitado'])
                self.assertEqual(self.client.post(self.url, payload, format='json').status_code, 400)
                with self.assertRaises(ValidationError):
                    chat_ia.enviar({})
                build.assert_not_called()
                reserve.assert_not_called()
                client.assert_not_called()
        self.assertTrue(MensagemAtendimento.objects.filter(id=payload['mensagem_id']).exists())
        self.assertFalse(RespostaChatIA.objects.exists())

    @override_settings(NOTARIUS_AMBIENTE='ficticio')
    def test_fictional_environment_still_requires_global_flag(self):
        with patch('apps.processos.chat_ia.Path.is_file', return_value=False):
            self.assertFalse(chat_ia.habilitado())
        with patch('apps.processos.chat_ia.Path.is_file', return_value=True):
            self.assertTrue(chat_ia.habilitado())

    def test_literal_quotes_and_refusals_fail_closed(self):
        sources = {'a': {'texto': 'Pagamento previsto, não quitado.', 'arquivo': 'FICTICIO.txt', 'pagina': 1}}
        valid = envelope(citations=[{'fonte': 'a', 'trecho': 'Pagamento previsto, não quitado.'}])
        self.assertIn('não quitado', interpretar(valid, sources))
        for citation in [{'fonte': 'a', 'trecho': 'Quitado.'}, {'fonte': 'outro', 'trecho': 'Pagamento'}]:
            with self.assertRaises(ValueError):
                interpretar(envelope(citations=[citation]), sources)
        with self.assertRaises(ValueError):
            interpretar({'status': 'incomplete'}, sources)


@skipUnless(os.environ.get('NOTARIUS_TESTE_REAL_AUTORIZADO') == '1', 'Teste pago somente com autorização explícita')
@override_settings(NOTARIUS_AMBIENTE='ficticio')
class ChatIALiveTests(APITestCase):
    setUp = helpers.AtendimentoTests.setUp
    create_case = helpers.AtendimentoTests.create_case

    def test_chat_real_com_pagamento_futuro(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        case = self.create_case()
        url = f'/api/v1/atendimentos/{case}'
        uploaded = self.client.post(url + '/anexos/', {'arquivo': SimpleUploadedFile('FICTICIO-PAGAMENTO.txt',
            'TESTE FICTÍCIO. Compradora: ANA EXEMPLO. Preço: R$ 150.000,00. Pagamento previsto para 30/11/2026. Não há declaração de quitação.'.encode(), content_type='text/plain')}, format='multipart')
        self.assertEqual(uploaded.status_code, 201, uploaded.data)
        message = self.client.post(url + '/mensagens/', {'texto': 'Resuma os documentos e diga se posso considerar o pagamento quitado.', 'client_id': str(uuid4())}, format='json')
        self.assertEqual(message.status_code, 201, message.data)
        with patch('apps.processos.chat_ia.habilitado', return_value=True):
            result = self.client.post(url + '/chat-ia/', {'mensagem_id': message.data['id']}, format='json')
            self.assertEqual(result.status_code, 200, result.data)
            self.assertEqual(result.data['respostas'][0]['estado'], 'concluido', result.data)
            loaded = self.client.get(url + '/chat-ia/')
            self.assertEqual(loaded.data['respostas'], result.data['respostas'])
        answer = result.data['respostas'][0]['texto']
        self.assertIn('Fontes para conferir:', answer)
        self.assertIn('nenhum dado foi confirmado automaticamente', answer)
        self.assertFalse(Atendimento.objects.get(pk=case).revisoes.exists())
        print('Resposta real fictícia validada:', answer)
