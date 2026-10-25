from uuid import uuid4
from tests import test_ficha_estruturada as base
from rest_framework.test import APITestCase
from apps.processos.models import Atendimento, RevisaoDadoAtendimento
from tests import test_propostas_dados as proposals


class PendenciasFichaTests(APITestCase):
    setUp = base.FichaEstruturadaTests.setUp
    create_case = base.FichaEstruturadaTests.create_case
    get = base.FichaEstruturadaTests.get
    post = base.FichaEstruturadaTests.post
    obj = base.FichaEstruturadaTests.obj
    field = base.FichaEstruturadaTests.field
    save_template = base.FichaEstruturadaTests.save_template

    def issues(self, case):
        response = self.client.post(f'/api/v1/atendimentos/{case}/pendencias-ficha/', {'operacao': 'atualizar'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        return response.data['pendencias']

    def decide(self, case, issue, **changes):
        data = {'operacao': 'resolver', 'client_id': str(uuid4()), 'justificativa': 'REVISÃO FICTÍCIA HUMANA',
                'pendencia_id': issue['id'], 'assinatura': issue['assinatura'], 'versao_esperada': issue['versao'],
                'acao': 'vincular', 'confirmei_revisao': True, **changes}
        return self.client.post(f'/api/v1/atendimentos/{case}/pendencias-ficha/', data, format='json')

    def test_field_confirmation_closes_only_own_issue_and_keeps_history(self):
        case = self.create_case(); a = self.obj(case); b = self.obj(case)
        self.field(case, a, 'nome', 'PESSOA A FICTÍCIA'); self.field(case, b, 'nome', 'PESSOA B FICTÍCIA')
        old = next(p for p in self.issues(case) if p['chave'] == f'dado:{a}:nome')
        self.assertEqual(self.decide(case, old).status_code, 400)
        self.field(case, a, 'nome', 'PESSOA A FICTÍCIA', versao_esperada=1, situacao='confirmado', confirmar=True, conferir_fonte=True)
        rows = self.issues(case)
        current = next(p for p in rows if p['id'] == old['id'])
        self.assertEqual(current['situacao'], 'resolvida')
        self.assertGreaterEqual(len(current['historico']), 2)
        self.assertEqual(next(p for p in rows if p['chave'] == f'dado:{b}:nome')['situacao'], 'aberta')
        self.field(case, a, 'nome', 'VALOR A ESCLARECER', versao_esperada=2, situacao='divergente')
        self.assertEqual(next(p for p in self.issues(case) if p['id'] == old['id'])['situacao'], 'reaberta')

    def test_manual_doubt_requires_exact_confirmed_field_and_reopens(self):
        case = self.create_case(); a = self.obj(case)
        self.field(case, a, 'nome', 'PESSOA FICTÍCIA', situacao='confirmado', confirmar=True, conferir_fonte=True)
        payload = {'operacao': 'abrir', 'client_id': str(uuid4()), 'objeto_id': a, 'campo': 'nome', 'pergunta': 'Homônimo?', 'justificativa': 'DÚVIDA FICTÍCIA'}
        url = f'/api/v1/atendimentos/{case}/pendencias-ficha/'
        opened = self.client.post(url, payload, format='json'); self.assertEqual(opened.status_code, 201)
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 200)
        issue = next(p for p in self.issues(case) if p['tipo'] == 'manual')
        rid = str(RevisaoDadoAtendimento.objects.get(objeto_id=a).id)
        self.assertEqual(self.decide(case, issue, revisoes_ids=[rid]).status_code, 201)
        self.assertEqual(self.decide(case, issue, revisoes_ids=[rid]).status_code, 409)
        self.field(case, a, 'nome', 'OUTRA PESSOA FICTÍCIA', versao_esperada=1, situacao='confirmado', confirmar=True, conferir_fonte=True)
        self.assertEqual(next(p for p in self.issues(case) if p['id'] == issue['id'])['situacao'], 'reaberta')

    def test_linked_person_change_reopens_role_without_changing_original(self):
        case = self.create_case(); person = self.obj(case)
        self.field(case, person, 'nome', 'PESSOA FICTÍCIA')
        role = self.obj(case, 'papel', pessoa_a_id=person)
        self.field(case, role, 'tipo_papel', 'vendedor', situacao='confirmado', confirmar=True, conferir_fonte=True)
        self.field(case, person, 'nome', 'PESSOA CORRIGIDA FICTÍCIA', versao_esperada=1)
        row = next(p for p in self.issues(case) if p['chave'] == f'dado:{role}:tipo_papel')
        self.assertEqual(row['situacao'], 'reaberta')
        self.assertEqual(row['tipo'], 'dependencia')
        self.assertEqual(RevisaoDadoAtendimento.objects.get(objeto_id=role).valor_original, 'vendedor')

    def test_one_discarded_line_does_not_close_another(self):
        case = self.create_case(); self.obj(case)
        self.client.post(f'/api/v1/atendimentos/{case}/mensagens/', {'texto': 'DÚVIDA FICTÍCIA A\nDÚVIDA FICTÍCIA B', 'client_id': str(uuid4())}, format='json')
        lines = [p for p in self.issues(case) if p['tipo'] == 'trecho']
        self.assertEqual(len(lines), 2)
        self.assertEqual(self.decide(case, lines[0], acao='nao_utilizar').status_code, 201)
        rows = self.issues(case)
        self.assertEqual(next(p for p in rows if p['id'] == lines[1]['id'])['situacao'], 'aberta')

    def test_other_case_cannot_resolve_issue(self):
        case = self.create_case(); self.obj(case)
        issue = self.issues(case)[0]
        other = self.create_case()
        self.assertEqual(self.decide(other, issue).status_code, 404)

    def test_no_unconfigured_professional_requirement(self):
        case = self.create_case(); person = self.obj(case)
        self.field(case, person, 'nome', 'PESSOA FICTÍCIA', situacao='confirmado', confirmar=True, conferir_fonte=True)
        self.assertFalse([p for p in self.issues(case) if p['situacao'] != 'resolvida'])
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{case}/conferencia/').data['pendencias'][-1]['chave'], 'ficha_estruturada')

    def test_configured_requirement_dependency_and_cycle_validation(self):
        case = self.create_case(); person = self.obj(case)
        response = self.save_template(case, campos_obrigatorios_ficha=[{'tipo': 'pessoa', 'chave': 'cpf'}],
            dependencias_campos_ficha=[{'tipo': 'pessoa', 'chave': 'nome', 'depende_de': ['cpf']}])
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(next(p for p in self.issues(case) if p['campo'] == 'cpf' and p['chave'].startswith('dado:'))['contexto']['exigido_modelo'])
        self.field(case, person, 'nome', 'PESSOA FICTÍCIA', situacao='confirmado', confirmar=True, conferir_fonte=True)
        self.field(case, person, 'cpf', 'DADO FICTÍCIO', situacao='informado')
        self.assertEqual(next(p for p in self.issues(case) if p['campo'] == 'nome')['tipo'], 'dependencia')
        invalid = self.save_template(case, expected=1, dependencias_campos_ficha=[
            {'tipo': 'pessoa', 'chave': 'nome', 'depende_de': ['cpf']},
            {'tipo': 'pessoa', 'chave': 'cpf', 'depende_de': ['nome']}])
        self.assertEqual(invalid.status_code, 400)
        invalid_type = self.save_template(case, expected=1, campos_obrigatorios_ficha=[{'tipo': [], 'chave': 'nome'}])
        self.assertEqual(invalid_type.status_code, 400)

    def test_page_review_cannot_bypass_proposals_or_current_uses(self):
        case = self.create_case(); person = self.obj(case)
        self.request_proposals = lambda case, **kw: proposals.PropostasDadosTests.request_proposals(self, case, **kw)
        proposals.PropostasDadosTests.document(self, case, 'Nome: PESSOA FICTÍCIA')
        page = next(p for p in self.issues(case) if p['tipo'] == 'pagina')
        self.assertEqual(self.decide(case, page, acao='nao_utilizar').status_code, 400)
        proposal = proposals.PropostasDadosTests.proposals(self, case)[0]
        applied = proposals.PropostasDadosTests.apply(self, case, person, proposal, confirm=True)
        self.assertEqual(applied.status_code, 201, applied.data)
        page = next(p for p in self.issues(case) if p['tipo'] == 'pagina')
        self.assertEqual(self.decide(case, page, acao='nao_utilizar').status_code, 400)
        self.assertEqual(self.decide(case, page, revisoes_ids=applied.data['revisoes']).status_code, 201)

    def test_other_tenant_cannot_consult_or_update_history(self):
        case = self.create_case(); self.obj(case)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        url = f'/api/v1/atendimentos/{case}/pendencias-ficha/'
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {'operacao': 'atualizar'}, format='json').status_code, 403)
