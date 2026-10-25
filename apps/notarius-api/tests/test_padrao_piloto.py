"""Professional candidate contract and full synthetic path, no operational approval."""
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import re
from uuid import uuid4
from unittest.mock import patch
from docx import Document
from pypdf import PdfReader
from django.test import SimpleTestCase
from rest_framework.test import APITestCase, APIClient
from apps.processos.padrao_piloto import candidato, ARQUIVO
from apps.processos.models import Atendimento, ModeloAtendimento, MinutaAtendimento
from apps.processos.exportacao import descricao
from tests import test_redacao_estruturada as base
from tests.test_comparacao_fontes import cpf_ficticio


class ContratoPadraoPilotoTests(SimpleTestCase):
    def test_all_reference_sections_are_mapped_without_legacy_tokens_or_case_defaults(self):
        package = candidato()
        old = json.loads((ARQUIVO.parent / 'modelo-v1.json').read_text(encoding='utf-8'))
        legacy = set(re.findall(r'\{\{([a-z_]+)\}\}', old['modelo']['corpo'] + old['modelo']['observacoes']))
        self.assertEqual({s['chave'] for s in package['revisao']}, legacy)
        self.assertFalse(package['modelo']['aprovado'])
        self.assertEqual(package['modelo']['versao_esperada'], 0)
        self.assertNotIn('{{quitacao}}', package['modelo']['corpo'])
        self.assertNotIn('negocio.quitacao', {f['marcador'] for f in package['mapa_campos']})
        self.assertNotIn('fora_deste_cenario', package['texto_candidato'])
        self.assertNotIn('{%', package['texto_candidato'])
        self.assertNotIn('{{', package['texto_candidato'])
        self.assertEqual(len(package['sha256']), 64)
        self.assertEqual(len(package['mapa_campos']), 46)
        for position in package['modelo']['registros_minuta']:
            self.assertNotIn('campos', position)
            self.assertNotIn('objeto_id', position)
        package['modelo']['corpo'] = 'alterado somente em memória'
        self.assertNotEqual(candidato()['modelo']['corpo'], package['modelo']['corpo'])


class PadraoPilotoPercursoTests(APITestCase):
    setUp = base.RedacaoEstruturadaTests.setUp
    create_case = base.RedacaoEstruturadaTests.create_case
    get = base.RedacaoEstruturadaTests.get
    post = base.RedacaoEstruturadaTests.post
    obj = base.RedacaoEstruturadaTests.obj
    field = base.RedacaoEstruturadaTests.field
    confirmed = base.RedacaoEstruturadaTests.confirmed
    binding = base.RedacaoEstruturadaTests.binding
    generate_draft = base.RedacaoEstruturadaTests.generate_draft

    def save(self, case, approved=False, expected=0, **changes):
        model = deepcopy(candidato()['modelo'])
        model.update(aprovado=approved, versao_esperada=expected, **changes)
        if approved:
            model['justificativa'] = 'APROVAÇÃO EXCLUSIVAMENTE SIMULADA EM BANCO DE TESTES FICTÍCIOS.'
        response = self.client.post(f'/api/v1/atendimentos/{case}/modelo-minuta/', model, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_offer_and_draft_save_reopen_edit_do_not_create_records_or_transfer_approval(self):
        case = self.create_case()
        url = f'/api/v1/atendimentos/{case}/modelo-minuta/'
        offer = self.client.get(url)
        self.assertFalse(offer.data['padrao_piloto']['aprovado'])
        self.assertFalse(ModeloAtendimento.objects.exists())
        self.assertFalse(Atendimento.objects.get(pk=case).objetos_ficha.exists())
        first = self.save(case)
        fresh = APIClient()
        fresh.force_authenticate(self.user)
        fresh.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
        reopened = fresh.get(url).data['versoes'][0]
        for key in ['corpo', 'observacoes', 'registros_minuta', 'campos_obrigatorios_ficha', 'dependencias_campos_ficha']:
            self.assertEqual(reopened[key], candidato()['modelo'][key])
        self.assertFalse(reopened['aprovado'])
        self.assertEqual(self.generate_draft(case).status_code, 400)
        second = self.save(case, expected=1, corpo=first['corpo'] + '\nTÍTULO EDITORIAL FICTÍCIO')
        self.assertFalse(second['aprovado'])
        self.assertEqual(len(fresh.get(url).data['versoes']), 2)
        self.assertFalse(MinutaAtendimento.objects.exists())
        self.assertEqual(self.client.post(url, candidato()['modelo'], format='json').status_code, 409)
        hidden = Atendimento.objects.create(tenant=self.other, criado_por=self.user, titulo='FICTÍCIO ISOLADO')
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{hidden.pk}/modelo-minuta/').status_code, 404)

    def resolve_comparisons(self, case):
        url = f'/api/v1/atendimentos/{case}/pendencias-ficha/'
        for issue in self.client.post(url, {'operacao': 'atualizar'}, format='json').data['pendencias']:
            context = issue['contexto']
            if issue['tipo'] != 'comparacao_fontes' or context.get('problemas') or issue['situacao'] == 'resolvida':
                continue
            current = context.get('revisao_atual')
            if not current or current['situacao'] != 'confirmado':
                continue
            response = self.client.post(url, {'operacao': 'resolver', 'client_id': str(uuid4()),
                'pendencia_id': issue['id'], 'assinatura': issue['assinatura'], 'versao_esperada': issue['versao'],
                'acao': 'vincular', 'revisoes_ids': [current['id']],
                'evidencias_ids': [e['id'] for e in context['evidencias']], 'confirmei_revisao': True,
                'justificativa': 'COMPARAÇÃO E DECISÃO SIMULADAS EXCLUSIVAMENTE NO TESTE.'}, format='json')
            self.assertEqual(response.status_code, 201, response.data)

    def test_entire_candidate_binds_literal_fields_and_exports_only_after_simulated_review(self):
        case = self.create_case()
        model = self.save(case, approved=True)
        package = candidato()
        ids = {}
        for position in package['modelo']['registros_minuta']:
            links = {key + '_id': ids[value] for key, value in position['vinculos'].items()}
            if position['tipo'] == 'complemento':
                links['escopo'] = 'pessoa' if 'pessoa_a_id' in links else 'imovel' if 'imovel_id' in links else 'atendimento'
            ids[position['chave']] = self.obj(case, position['tipo'], **links)
        values = {}
        for position in package['modelo']['registros_minuta']:
            alias = position['chave']
            batch = []
            fields = [f['marcador'].split('.')[1] for f in package['mapa_campos'] if f['marcador'].startswith(alias + '.')]
            if position['tipo'] == 'negociacao':
                fields = ['preco', 'situacao_pagamento', 'condicoes']
            if position['tipo'] == 'complemento':
                fields = ['categoria', 'situacao', *fields]
            for key in fields:
                value = ('PESSOA INTEIRAMENTE FICTÍCIA HOMÔNIMA' if key == 'nome' else
                         cpf_ficticio('123456789' if alias == 'vendedor' else '987654321') if key == 'cpf' else
                         position['categoria'] if key == 'categoria' else
                         'informado' if key == 'situacao' else
                         'direta' if position['tipo'] == 'papel' and key == 'descricao' else
                         'vendedor' if alias == 'papel_vendedor' and key == 'tipo_papel' else
                         'comprador' if alias == 'papel_comprador' and key == 'tipo_papel' else
                         'previsto' if key == 'situacao_pagamento' else
                         'R$ 123.456,78' if key == 'preco' else
                         'PREVISÃO FICTÍCIA, SEM DECLARAÇÃO DE RECEBIMENTO' if key == 'condicoes' else
                         f'TEXTO FICTÍCIO {alias} {key} <teste> & ação 0007')
                batch.append({'chave': key, 'valor': value, 'valor_original': value, 'origem': 'manual',
                              'situacao': 'confirmado', 'versao_esperada': 0, 'confirmar': True, 'conferir_fonte': True})
                values[alias + '.' + key] = value
            response, _ = self.post(case, {'operacao': 'salvar', 'objeto_id': ids[alias], 'campos': batch})
            self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.binding(case, ids)[0].status_code, 201)
        self.resolve_comparisons(case)
        with patch('openai.OpenAI') as external:
            response = self.generate_draft(case)
        external.assert_not_called()
        diagnostic = self.client.get(f'/api/v1/atendimentos/{case}/conferencia/').data
        self.assertEqual(response.status_code, 200, [(p['chave'], p['pergunta']) for p in diagnostic['pendencias']])
        draft = response.data['versoes'][0]
        self.assertNotEqual(ids['vendedor'], ids['comprador'])
        self.assertNotIn('quitação', draft['corpo'].lower())
        self.assertNotIn('{{', draft['corpo'])
        for marker, datum in draft['dados'].items():
            self.assertEqual(datum['objeto_id'], ids[marker.split('.')[0]])
            self.assertEqual(datum['valor'], values[marker])
            self.assertTrue(datum['origem']['mensagem_id'])
            for occurrence in datum['ocorrencias']:
                self.assertEqual(draft['corpo'][occurrence['inicio']:occurrence['fim']], datum['valor'])
        swapped = {**ids, 'consulta_vendedor': ids['consulta_comprador'], 'consulta_comprador': ids['consulta_vendedor']}
        self.assertEqual(self.binding(case, swapped)[0].status_code, 400)
        export = f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/exportar/"
        self.assertEqual(self.client.get(export, {'formato': 'docx'}).status_code, 409)
        review = self.client.post(f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/revisar/", {
            'versao_esperada': draft['versao'], 'motivo': 'REVISÃO FINAL SIMULADA NO TESTE FICTÍCIO.',
            'conferi_texto': True, 'conferi_dados': True, 'conferi_fontes': True}, format='json')
        self.assertEqual(review.status_code, 201, review.data)
        word = self.client.get(export, {'formato': 'docx'})
        pdf = self.client.get(export, {'formato': 'pdf'})
        self.assertEqual(word.status_code, 200)
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual('\n'.join(p.text for p in Document(BytesIO(word.content)).paragraphs[3:]), draft['corpo'])
        extracted = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages)
        saved = MinutaAtendimento.objects.get(pk=draft['id'])
        for metadata in ['Minuta de compra e venda', 'Para revisão. Não constitui documento assinado ou ato concluído.', descricao(saved), 'Minuta para revisão']:
            extracted = extracted.replace(metadata, '')
        extracted = re.sub(r'Página\s+\d+', '', extracted)
        compact = lambda text: re.sub(r'\s+', '', text)
        self.assertEqual(compact(extracted), compact(draft['corpo']))
        self.save(case, expected=model['versao'])
        self.assertEqual(self.client.get(export, {'formato': 'docx'}).status_code, 409)
        self.assertEqual(self.generate_draft(case).status_code, 400)
