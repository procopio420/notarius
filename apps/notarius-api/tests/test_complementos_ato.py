from uuid import uuid4
from types import SimpleNamespace
from rest_framework.test import APITestCase
from apps.processos.models import Atendimento, RevisaoDadoAtendimento
from apps.processos.redacao import validar_modelo, validar_fatos_fixos
from apps.processos.modelo_complementar import referencia_complementar
from tests import test_redacao_estruturada as base


class ComplementosAtoTests(APITestCase):
    setUp = base.RedacaoEstruturadaTests.setUp
    create_case = base.RedacaoEstruturadaTests.create_case
    get = base.RedacaoEstruturadaTests.get
    post = base.RedacaoEstruturadaTests.post
    obj = base.RedacaoEstruturadaTests.obj
    field = base.RedacaoEstruturadaTests.field
    confirmed = base.RedacaoEstruturadaTests.confirmed
    save_template = base.RedacaoEstruturadaTests.save_template
    generate_draft = base.RedacaoEstruturadaTests.generate_draft
    binding = base.RedacaoEstruturadaTests.binding
    draft = base.RedacaoEstruturadaTests.draft

    def issues(self, case):
        return self.client.get(f'/api/v1/atendimentos/{case}/pendencias-ficha/').data['pendencias']

    def classified(self, case, obj, category='consulta', state='nao_realizado', text='CONSULTA NÃO REALIZADA — CENÁRIO FICTÍCIO'):
        fields = [{'chave': k, 'valor': v, 'situacao': 'confirmado', 'origem': 'manual', 'versao_esperada': 0,
                   'confirmar': True, 'conferir_fonte': True} for k, v in [('categoria', category), ('situacao', state), ('conteudo', text)]]
        response, _ = self.post(case, {'operacao': 'salvar', 'objeto_id': obj, 'campos': fields})
        self.assertEqual(response.status_code, 201, response.data)

    def test_new_types_are_optional_empty_and_do_not_create_sources_or_defaults(self):
        case = self.create_case()
        self.assertEqual(self.get(case).data['objetos'], [])
        act = self.obj(case, 'ato')
        data = self.get(case).data['objetos'][0]
        self.assertEqual(data['id'], act)
        self.assertTrue(all(c['atual'] is None for c in data['campos']))
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        self.assertEqual(self.generate_draft(case).status_code, 400)

    def test_complement_requires_explicit_scope_and_forbids_other_person_or_case(self):
        case = self.create_case(); person = self.obj(case); home = self.obj(case, 'imovel')
        self.assertEqual(self.post(case, {'operacao': 'criar', 'tipo': 'complemento'})[0].status_code, 400)
        self.assertEqual(self.post(case, {'operacao': 'criar', 'tipo': 'complemento', 'escopo': 'pessoa'})[0].status_code, 400)
        self.assertEqual(self.post(case, {'operacao': 'criar', 'tipo': 'complemento', 'escopo': 'atendimento', 'pessoa_a_id': person})[0].status_code, 400)
        complement = self.obj(case, 'complemento', escopo='pessoa_imovel', pessoa_a_id=person, imovel_id=home)
        self.assertEqual(self.post(case, {'operacao': 'salvar', 'objeto_id': complement, 'escopo': 'atendimento'})[0].status_code, 400)
        other = self.create_case()
        self.assertEqual(self.post(other, {'operacao': 'criar', 'tipo': 'complemento', 'escopo': 'pessoa', 'pessoa_a_id': person})[0].status_code, 404)
        self.assertEqual(self.post(case, {'operacao': 'criar', 'tipo': 'ato', 'pessoa_a_id': person})[0].status_code, 400)

    def test_batch_confirmation_captures_classification_and_change_reopens_text(self):
        case = self.create_case(); complement = self.obj(case, 'complemento', escopo='atendimento')
        self.classified(case, complement)
        rows = self.issues(case)
        self.assertFalse([p for p in rows if p['situacao'] != 'resolvida'])
        self.confirmed(case, complement, 'situacao', 'declarado_realizado', versao_esperada=1)
        issue = next(p for p in self.issues(case) if p['campo'] == 'conteudo')
        self.assertEqual(issue['situacao'], 'reaberta'); self.assertEqual(issue['tipo'], 'dependencia')
        old = RevisaoDadoAtendimento.objects.get(objeto_id=complement, chave='conteudo')
        self.assertEqual(old.valor_original, 'CONSULTA NÃO REALIZADA — CENÁRIO FICTÍCIO')
        self.assertEqual(old.situacao, 'confirmado')

    def test_classification_missing_or_uncertain_keeps_content_blocked(self):
        case = self.create_case(); complement = self.obj(case, 'complemento', escopo='atendimento')
        self.confirmed(case, complement, 'conteudo', 'CONTEÚDO FICTÍCIO')
        rows = self.issues(case)
        self.assertEqual({p['campo'] for p in rows if p['situacao'] != 'resolvida'}, {'categoria', 'situacao'})
        self.assertFalse(next(p for p in rows if p['campo'] == 'categoria')['contexto']['exigido_modelo'])
        self.confirmed(case, complement, 'categoria', 'certidao')
        self.confirmed(case, complement, 'situacao', 'a_esclarecer')
        self.assertTrue(next(p for p in self.issues(case) if p['campo'] == 'situacao')['ativa'])
        self.assertEqual(self.generate_draft(case).status_code, 400)

    def test_model_cannot_treat_person_document_as_general_or_other_person(self):
        case = self.create_case(); a = self.obj(case); b = self.obj(case)
        self.confirmed(case, a); self.confirmed(case, b, value='OUTRA PESSOA FICTÍCIA')
        complement = self.obj(case, 'complemento', escopo='pessoa', pessoa_a_id=a)
        self.classified(case, complement)
        positions = [{'chave': 'p', 'rotulo': 'Pessoa fictícia', 'tipo': 'pessoa', 'vinculos': {}},
                     {'chave': 'c', 'rotulo': 'Consulta fictícia', 'tipo': 'complemento', 'categoria': 'consulta', 'vinculos': {'pessoa_a': 'p'}}]
        model = self.save_template(case, corpo='{{p.nome}}\n{{c.conteudo}}', representacao='', observacoes='', registros_minuta=positions)
        self.assertEqual(model.status_code, 201, model.data)
        self.assertEqual(self.binding(case, {'p': b, 'c': complement}, [{'objeto_id': a, 'motivo': 'TESTE FICTÍCIO'}])[0].status_code, 400)
        self.assertEqual(self.binding(case, {'p': a, 'c': complement}, [{'objeto_id': b, 'motivo': 'TESTE FICTÍCIO'}])[0].status_code, 201)
        self.draft(case)
        positions[1]['vinculos'] = {}
        self.assertEqual(self.save_template(case, expected=1, corpo='{{p.nome}}\n{{c.conteudo}}', representacao='', observacoes='', registros_minuta=positions).status_code, 201)
        self.assertEqual(self.binding(case, {'p': a, 'c': complement}, [{'objeto_id': b, 'motivo': 'TESTE FICTÍCIO'}])[0].status_code, 400)

    def test_general_act_and_individual_complement_fill_with_provenance_and_export_gate(self):
        case = self.create_case(); act = self.obj(case, 'ato'); complement = self.obj(case, 'complemento', escopo='atendimento')
        self.confirmed(case, act, 'abertura', 'ABERTURA FICTÍCIA SEM ATO CONCLUÍDO')
        self.confirmed(case, act, 'encerramento', 'ENCERRAMENTO FICTÍCIO PARA REVISÃO')
        self.classified(case, complement)
        positions = [{'chave': 'ato', 'rotulo': 'Ato fictício', 'tipo': 'ato', 'vinculos': {}},
                     {'chave': 'consulta', 'rotulo': 'Consulta fictícia', 'tipo': 'complemento', 'categoria': 'consulta', 'vinculos': {}}]
        model = self.save_template(case, corpo='{{ato.abertura}}\n{{consulta.conteudo}}\n{{ato.encerramento}}', representacao='', observacoes='', registros_minuta=positions)
        self.assertEqual(model.status_code, 201, model.data)
        self.assertEqual(self.binding(case, {'ato': act, 'consulta': complement})[0].status_code, 201)
        draft = self.draft(case)
        self.assertIn('CONSULTA NÃO REALIZADA', draft['corpo'])
        self.assertEqual(draft['dados']['consulta.conteudo']['objeto_id'], complement)
        self.assertTrue(draft['dados']['ato.abertura']['origem']['mensagem_id'])
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/exportar/", {'formato': 'pdf'}).status_code, 409)
        review = self.client.post(f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/revisar/", {
            'versao_esperada': draft['versao'], 'motivo': 'REVISÃO FINAL SIMULADA, SOMENTE TESTE',
            'conferi_texto': True, 'conferi_dados': True, 'conferi_fontes': True}, format='json')
        self.assertEqual(review.status_code, 201, review.data)
        for fmt in ['docx', 'pdf']:
            exported = self.client.get(f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/exportar/", {'formato': fmt})
            self.assertEqual(exported.status_code, 200)
        self.confirmed(case, complement, 'categoria', 'outro', versao_esperada=1)
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/exportar/", {'formato': 'docx'}).status_code, 409)

    def test_default_technical_dependencies_are_included_when_rejecting_model_cycles(self):
        case = self.create_case()
        response = self.save_template(case, dependencias_campos_ficha=[{'tipo': 'complemento', 'chave': 'categoria', 'depende_de': ['conteudo']}])
        self.assertEqual(response.status_code, 400)

    def test_both_complementary_references_are_valid_unapproved_and_read_only(self):
        case = self.create_case()
        result = self.client.get(f'/api/v1/atendimentos/{case}/modelo-minuta/')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data['referencias_complementares']), 2)
        for variant in ['direta', 'procuracao']:
            ref = referencia_complementar(variant)
            self.assertFalse(ref['aprovado']); self.assertFalse(ref['modelo']['aprovado'])
            validar_modelo(ref['modelo']); validar_fatos_fixos(SimpleNamespace(**ref['modelo']))
            self.assertIn('{{ato.encerramento}}', ref['modelo']['corpo'])
            self.assertIn('{{tributo.conteudo}}', ref['modelo']['corpo'])
            self.assertIn('{{negocio.quitacao}}', ref['modelo']['corpo'])
        current = Atendimento.objects.get(pk=case)
        self.assertFalse(current.modelos_minuta.exists()); self.assertFalse(current.objetos_ficha.exists())
        self.assertFalse(current.revisoes.exists())

    def test_stale_opened_context_cannot_confirm_text_after_classification_changed(self):
        case = self.create_case(); complement = self.obj(case, 'complemento', escopo='atendimento')
        self.classified(case, complement)
        context = next(f['contexto_assinatura'] for o in self.get(case).data['objetos'] if o['id'] == complement for f in o['campos'] if f['chave'] == 'conteudo')
        self.confirmed(case, complement, 'categoria', 'certidao', versao_esperada=1)
        response, _ = self.field(case, complement, 'conteudo', 'TEXTO COM CONTEXTO ANTIGO', versao_esperada=1,
            situacao='confirmado', confirmar=True, conferir_fonte=True, contexto_assinatura=context)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(RevisaoDadoAtendimento.objects.filter(objeto_id=complement, chave='conteudo').count(), 1)

    def test_consultation_cannot_fill_a_tax_position_even_with_same_scope(self):
        case = self.create_case(); complement = self.obj(case, 'complemento', escopo='atendimento')
        self.classified(case, complement)
        positions = [{'chave': 'tributo', 'rotulo': 'Tributo fictício', 'tipo': 'complemento', 'categoria': 'tributo', 'vinculos': {}}]
        response = self.save_template(case, corpo='{{tributo.conteudo}}', representacao='', observacoes='', registros_minuta=positions)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.binding(case, {'tributo': complement})[0].status_code, 400)
