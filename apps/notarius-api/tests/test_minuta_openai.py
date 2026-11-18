import json
from unittest.mock import patch
from uuid import uuid4

import httpx
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.processos import minuta_assistida
from apps.processos.modelo_escritura_fiel import chave_campo
from apps.processos.models import Atendimento, PaginaAnexoAtendimento, RevisaoDadoAtendimento
from tests import test_atendimentos as helpers


@override_settings(NOTARIUS_AMBIENTE='real', NOTARIUS_MINUTA_PROVEDOR='openai',
                   NOTARIUS_MODELO_MINUTA_LOCAL='local', NOTARIUS_MINUTA_OPENAI_CHAVE='test-only',
                   NOTARIUS_MINUTA_OPENAI_ORGANIZACAO='org-test', NOTARIUS_MINUTA_OPENAI_PROJETO='proj-test',
                   NOTARIUS_MINUTA_OPENAI_REGIAO='eu', NOTARIUS_MINUTA_OPENAI_AUTORIZACAO='autorizacao-ficticia')
class MinutaOpenAITests(APITestCase):
    setUp = helpers.AtendimentoTests.setUp
    create_case = helpers.AtendimentoTests.create_case

    def anexar(self, case, name, text, finalidade=None):
        url = f'/api/v1/atendimentos/{case}/anexos/'
        upload = self.client.post(url, {'arquivo': SimpleUploadedFile(name, text.encode())}, format='multipart')
        self.assertEqual(upload.status_code, 201)
        if finalidade:
            saved = self.client.post(f'{url}{upload.data["id"]}/organizacao/', {
                'client_id': str(uuid4()), 'versao_esperada': 0, 'leitura_versao': 1,
                'finalidade': finalidade, 'tipo_documento': 'Documento inteiramente fictício',
                'vinculos': [{'objeto_id': None, 'paginas': [1]}] if finalidade == 'caso' else [],
                'motivo': 'Conferência simulada', 'conferi': True,
            }, format='json')
            self.assertEqual(saved.status_code, 201, saved.data)
        return upload.data['id']

    def preparar(self, case):
        url = f'/api/v1/atendimentos/{case}/'
        state = self.client.get(url + 'minuta-preparada/').data
        return self.client.post(url + 'minuta-assistida/', {'assinatura_esperada': state['assinatura'],
            'minuta_atual_id': state['versoes'][0]['id'] if state['versoes'] else None}, format='json')

    def test_sem_autorizacao_ou_com_outro_tenant_nao_abre_transporte(self):
        case = self.create_case()
        with patch.object(minuta_assistida, 'abrir_cliente') as transport:
            with override_settings(NOTARIUS_MINUTA_OPENAI_TENANT=str(self.other.id)):
                self.assertEqual(self.preparar(case).status_code, 503)
            with override_settings(NOTARIUS_MINUTA_OPENAI_TENANT=str(self.tenant.id), NOTARIUS_MINUTA_OPENAI_AUTORIZACAO=''):
                self.assertEqual(self.preparar(case).status_code, 503)
            transport.assert_not_called()

    def test_envia_apenas_pagina_classificada_e_preserva_as_pendencias(self):
        case = self.create_case()
        text = 'A compradora fictícia Elisa da Serra está inscrita no CPF 000.000.004-00.'
        file_id = self.anexar(case, 'nome-interno.txt', text, 'caso')
        page = PaginaAnexoAtendimento.objects.get(anexo_id=file_id, numero=1)
        page.pk = None
        page._state.adding = True
        page.numero = 2
        page.texto = 'PÁGINA FORA DO ENVIO'
        page.save()
        self.anexar(case, 'pendente.txt', 'ARQUIVO NÃO CLASSIFICADO')
        self.anexar(case, 'modelo.txt', 'DADO DA REFERÊNCIA', 'referencia_redacao')
        cpf = chave_campo('CPF da compradora')
        ato = chave_campo('Número do ato')
        requests = []

        def answer(request):
            requests.append(request)
            body = json.loads(request.content)
            self.assertFalse(body['store'])
            self.assertNotIn('tools', body)
            sent = json.loads(body['input'][1]['content'])
            self.assertEqual([source['texto'] for source in sent['documentos']], [text])
            self.assertNotIn('nome-interno.txt', request.content.decode())
            rows = [{'campo': minuta_assistida.CAMPOS_EXTRAIVEIS.index(key), 'fonte': sent['documentos'][0]['fonte'],
                     'valor': value, 'trecho': text} for key, value in [(cpf, '000.000.004-00'), (ato, '000')]]
            return httpx.Response(200, json={'status': 'completed', 'output': [{'type': 'message', 'role': 'assistant',
                'content': [{'type': 'output_text', 'text': json.dumps({'dados': rows})}]}]})

        client = httpx.Client(base_url='https://eu.api.openai.com', transport=httpx.MockTransport(answer))
        with override_settings(NOTARIUS_MINUTA_OPENAI_TENANT=str(self.tenant.id)), \
             patch.object(minuta_assistida.httpx, 'Client', return_value=client) as constructor:
            response = self.preparar(case)
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(self.preparar(case).status_code, 200)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].url.path, '/v1/responses')
        settings = constructor.call_args.kwargs
        self.assertEqual(settings['base_url'], 'https://eu.api.openai.com')
        self.assertEqual(settings['headers']['OpenAI-Project'], 'proj-test')
        self.assertEqual(settings['headers']['OpenAI-Organization'], 'org-test')
        self.assertFalse(settings['follow_redirects'])
        self.assertFalse(settings['trust_env'])
        version = response.data['versoes'][0]
        self.assertEqual(version['assistencia']['provedor'], 'openai')
        self.assertEqual(version['dados'][cpf]['valor'], '000.000.004-00')
        self.assertNotIn(ato, version['dados'])
        self.assertIn(chave_campo('Conferência da quitação e da transmissão'),
                      {item['campo'] for item in version['assistencia']['pendencias']})
        self.assertEqual(len(version['assistencia']['avisos']), 1)
        url = f'/api/v1/atendimentos/{case}/'
        edit = self.client.post(url + 'editar-minuta/', {'minuta_id': version['id'], 'versao_esperada': version['versao'],
            'client_id': str(uuid4()), 'corpo': 'Rascunho fictício editado sem os marcadores.', 'motivo': 'Teste'}, format='json')
        self.assertEqual(edit.status_code, 201, edit.data)
        denied = self.client.post(url + f'minutas/{edit.data["id"]}/revisar/', {
            'versao_esperada': edit.data['versao'], 'motivo': 'Teste', 'conferi_texto': True,
            'conferi_dados': True, 'conferi_fontes': True,
        }, format='json')
        self.assertEqual(denied.status_code, 400, denied.data)
        self.assertIn('conferências obrigatórias', str(denied.data))

    def test_falha_da_api_preserva_documento_sem_recorrer_ao_qwen(self):
        case = self.create_case()
        self.anexar(case, 'qualificacao.txt', 'Nome da compradora: Pessoa Fictícia\nInformação em texto livre.', 'caso')
        with override_settings(NOTARIUS_MINUTA_OPENAI_TENANT=str(self.tenant.id)), \
             patch.object(minuta_assistida, 'extrair_openai', side_effect=httpx.ReadTimeout('Teste')), \
             patch.object(minuta_assistida, 'extrair') as local:
            self.assertEqual(self.preparar(case).status_code, 503)
        local.assert_not_called()
        saved = Atendimento.objects.get(pk=case)
        self.assertTrue(saved.anexos.exists())
        self.assertFalse(saved.minutas_preparadas.exists())

    def test_confirmar_declaracao_salva_nova_versao_e_reabre_apos_mudar_fontes(self):
        case = self.create_case()
        self.anexar(case, 'qualificacao.txt', 'Nome da compradora: Pessoa Fictícia', 'caso')
        url = f'/api/v1/atendimentos/{case}/'
        key = chave_campo('Conferência da quitação e da transmissão')
        marker = minuta_assistida.marcador_declaracao(key)
        with override_settings(NOTARIUS_MINUTA_OPENAI_TENANT=str(self.tenant.id)), \
             patch.object(minuta_assistida, 'extrair_openai') as provider:
            prepared = self.preparar(case)
            self.assertEqual(prepared.status_code, 200, prepared.data)
            base = prepared.data['versoes'][0]
            self.assertIn(marker, base['corpo'])
            self.assertTrue(next(p for p in base['assistencia']['pendencias'] if p['campo'] == key)['confirmacao'])
            payload = {'minuta_id': base['id'], 'versao_esperada': base['versao'], 'client_id': str(uuid4()),
                       'corpo': base['corpo'].replace(marker, ''), 'motivo': 'Conferência fictícia', 'confirmacoes': [key]}
            tampered = self.client.post(url + 'editar-minuta/', {**payload, 'corpo': 'Texto alterado.'}, format='json')
            self.assertEqual(tampered.status_code, 400, tampered.data)
            invalid = self.client.post(url + 'editar-minuta/', {**payload, 'confirmacoes': ['outro_campo']}, format='json')
            self.assertEqual(invalid.status_code, 400, invalid.data)
            saved = self.client.post(url + 'editar-minuta/', payload, format='json')
            self.assertEqual(saved.status_code, 201, saved.data)
            replay = self.client.post(url + 'editar-minuta/', payload, format='json')
            self.assertEqual(replay.status_code, 200, replay.data)
            self.assertEqual(replay.data, saved.data)
            state = self.client.get(url + 'minuta-preparada/').data
            new, old = state['versoes']
            self.assertEqual(new['corpo'], payload['corpo'])
            self.assertEqual(old['corpo'], base['corpo'])
            self.assertEqual(Atendimento.objects.get(pk=case).minutas_preparadas.first().assinatura, state['assinatura'])
            self.assertEqual(len(new['assistencia']['pendencias']), len(old['assistencia']['pendencias']) - 1)
            self.assertEqual(new['dados'][key]['situacao'], 'confirmado')
            registration = RevisaoDadoAtendimento.objects.get(atendimento_id=case, chave=key)
            self.assertEqual(registration.autor, self.user)
            self.anexar(case, 'outro.txt', 'Endereço do imóvel: Endereço Fictício', 'caso')
            regenerated = self.preparar(case)
            self.assertEqual(regenerated.status_code, 200, regenerated.data)
            self.assertIn(marker, regenerated.data['versoes'][0]['corpo'])
            provider.assert_not_called()
