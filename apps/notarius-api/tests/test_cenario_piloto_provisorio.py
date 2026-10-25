"""Run the proposed scenario in an isolated database with fictional decisions."""
import json
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from rest_framework.test import APITestCase

from apps.processos.models import Atendimento
from tests import test_redacao_estruturada as base


def configuracao():
    path = Path(__file__).resolve().parents[3] / 'docs/piloto-profissional/cenario-provisorio-v1.json'
    return json.loads(path.read_text(encoding='utf-8'))


class CenarioPilotoProvisorioTests(APITestCase):
    setUp = base.RedacaoEstruturadaTests.setUp
    create_case = base.RedacaoEstruturadaTests.create_case
    get = base.RedacaoEstruturadaTests.get
    post = base.RedacaoEstruturadaTests.post
    obj = base.RedacaoEstruturadaTests.obj
    field = base.RedacaoEstruturadaTests.field
    confirmed = base.RedacaoEstruturadaTests.confirmed
    binding = base.RedacaoEstruturadaTests.binding
    generate_draft = base.RedacaoEstruturadaTests.generate_draft

    def preparar(self, approved_in_test=False, status='previsto', omit=None):
        case = self.create_case()
        a, b = self.obj(case), self.obj(case)
        home = self.obj(case, 'imovel')
        seller = self.obj(case, 'papel', pessoa_a_id=a)
        buyer = self.obj(case, 'papel', pessoa_a_id=b)
        deal = self.obj(case, 'negociacao', imovel_id=home)
        records = dict(vendedor=a, comprador=b, papel_vendedor=seller,
                       papel_comprador=buyer, bem=home, negocio=deal)
        model = configuracao()['modelo']
        model['aprovado'] = approved_in_test
        model['justificativa'] = 'SOMENTE TESTE FICTÍCIO: aprovação simulada em banco isolado.'
        saved = self.client.post(f'/api/v1/atendimentos/{case}/modelo-minuta/', model, format='json')
        self.assertEqual(saved.status_code, 201, saved.data)
        values = [('vendedor', 'nome', 'PESSOA FICTÍCIA ALFA'),
                  ('comprador', 'nome', 'PESSOA FICTÍCIA ALFA'),
                  ('papel_vendedor', 'tipo_papel', 'vendedor'),
                  ('papel_comprador', 'tipo_papel', 'comprador'),
                  ('bem', 'descricao', 'IMÓVEL INTEIRAMENTE FICTÍCIO'),
                  ('bem', 'matricula', 'MATRÍCULA DE TESTE'),
                  ('bem', 'registro', 'REGISTRO FICTÍCIO'),
                  ('negocio', 'preco', 'R$ 123.456,78'),
                  ('negocio', 'situacao_pagamento', status),
                  ('negocio', 'condicoes', 'PREVISÃO FICTÍCIA, SEM COMPROVANTE')]
        for alias, key, value in values:
            if (alias, key) != omit:
                self.confirmed(case, records[alias], key, value)
        if approved_in_test:
            response, _ = self.binding(case, records)
            self.assertEqual(response.status_code, 201, response.data)
            # Required fields initially missing create persistent review issues.
            # Resolve only completed comparisons, explicitly and in tests only.
            issues = self.client.post(f'/api/v1/atendimentos/{case}/pendencias-ficha/',
                                      {'operacao': 'atualizar'}, format='json').data['pendencias']
            for issue in issues:
                context = issue['contexto']
                if issue['tipo'] != 'comparacao_fontes' or context.get('problemas'):
                    continue
                current = context.get('revisao_atual')
                if not current or current['situacao'] != 'confirmado':
                    continue
                resolved = self.client.post(f'/api/v1/atendimentos/{case}/pendencias-ficha/', {
                    'operacao': 'resolver', 'client_id': str(uuid4()), 'pendencia_id': issue['id'],
                    'assinatura': issue['assinatura'], 'versao_esperada': issue['versao'],
                    'acao': 'vincular', 'revisoes_ids': [current['id']],
                    'evidencias_ids': [e['id'] for e in context['evidencias']],
                    'confirmei_revisao': True,
                    'justificativa': 'REVISÃO FICTÍCIA DAS FONTES NO BANCO ISOLADO DE TESTE.'}, format='json')
                self.assertEqual(resolved.status_code, 201, resolved.data)
        return case, records

    def test_artifact_loads_as_draft_without_professional_approval(self):
        self.assertFalse(configuracao()['aprovado'])
        case, _ = self.preparar()
        self.assertFalse(Atendimento.objects.get(pk=case).modelos_minuta.first().aprovado)
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertFalse(Atendimento.objects.get(pk=case).minutas_preparadas.exists())

    def test_future_payment_and_same_names_keep_ids_and_never_create_quittance(self):
        case, records = self.preparar(approved_in_test=True)
        with patch('openai.OpenAI') as provider:
            response = self.generate_draft(case)
        provider.assert_not_called()
        self.assertEqual(response.status_code, 200, self.client.get(f'/api/v1/atendimentos/{case}/conferencia/').data)
        draft = response.data['versoes'][0]
        self.assertEqual(draft['dados']['vendedor.nome']['objeto_id'], records['vendedor'])
        self.assertEqual(draft['dados']['comprador.nome']['objeto_id'], records['comprador'])
        self.assertNotEqual(records['vendedor'], records['comprador'])
        self.assertNotIn('quitação', draft['corpo'].lower())
        self.assertNotIn('quitacao', draft['dados'])
        self.assertFalse(Atendimento.objects.get(pk=case).revisoes.filter(chave='quitacao').exists())

    def test_wrong_person_role_link_is_rejected_even_with_identical_names(self):
        case, records = self.preparar(approved_in_test=True)
        swapped = {**records, 'vendedor': records['comprador'], 'comprador': records['vendedor']}
        self.assertEqual(self.binding(case, swapped)[0].status_code, 400)

    def test_outside_payment_scenario_stops_without_partial_draft(self):
        case, _ = self.preparar(approved_in_test=True, status='declarado_realizado')
        response = self.generate_draft(case)
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(Atendimento.objects.get(pk=case).minutas_preparadas.exists())

    def test_required_field_missing_stops_generation(self):
        case, _ = self.preparar(approved_in_test=True, omit=('bem', 'matricula'))
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertFalse(Atendimento.objects.get(pk=case).minutas_preparadas.exists())

    def test_price_correction_reopens_dependent_conditions_and_stales_draft(self):
        case, records = self.preparar(approved_in_test=True)
        response = self.generate_draft(case)
        self.assertEqual(response.status_code, 200, response.data)
        self.confirmed(case, records['negocio'], 'preco', 'R$ 234.567,89', versao_esperada=1)
        state = self.get(case).data
        deal = next(o for o in state['objetos'] if o['id'] == records['negocio'])
        conditions = next(f for f in deal['campos'] if f['chave'] == 'condicoes')
        self.assertFalse(conditions['atual']['confirmacao_atual'])
        self.assertEqual(self.generate_draft(case).status_code, 400)
