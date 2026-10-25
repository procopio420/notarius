from copy import deepcopy
from uuid import uuid4
from unittest.mock import patch
from django.test import SimpleTestCase
from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError
from apps.processos.blocos_minuta import plano, referencias
from apps.processos.models import Atendimento
from tests import test_redacao_estruturada as base


class ContratoBlocosTests(SimpleTestCase):
    def model(self, text):
        return {'corpo':text,'representacao':'','observacoes':''}

    def test_rejects_nesting_unknown_commands_and_incomplete_directives(self):
        for text in ['{% exec abrir %}', '{% fim %}', '{% repetir a p1 %}{{item.nome}}', '{% repetir a p1 %}{% repetir b p2 %}{% fim %}{% fim %}', '{% se x {} %}texto{% fim %}', '{% repetir a p1,p1 %}{{item.nome}}{% fim %}']:
            with self.subTest(text=text), self.assertRaises(ValidationError): plano(self.model(text))

    def test_duplicates_limits_and_uncertainty_are_not_approved_alternatives(self):
        for rule in ['{"campo":"a.nome","campo":"b.nome","permitidos":["X"],"incluir":["X"]}', '{"campo":"a.nome","permitidos":["X"],"incluir":["Y"]}', '{"campo":"a.nome","permitidos":["a_esclarecer"],"incluir":["a_esclarecer"]}']:
            with self.subTest(rule=rule), self.assertRaises(ValidationError): plano(self.model('{% se a '+rule+' %}FICTÍCIO{% fim %}'))

    def test_repetition_expands_only_explicit_aliases_without_name_matching(self):
        self.assertEqual(referencias(self.model('{% repetir r p1,p2 %}{{item.nome}} {{item.nome}}{% fim %}')), [('p1','nome'),('p1','nome'),('p2','nome'),('p2','nome')])


class BlocosMinutaTests(APITestCase):
    setUpBase = base.RedacaoEstruturadaTests.setUp
    create_case = base.RedacaoEstruturadaTests.create_case
    get = base.RedacaoEstruturadaTests.get
    post = base.RedacaoEstruturadaTests.post
    obj = base.RedacaoEstruturadaTests.obj
    field = base.RedacaoEstruturadaTests.field
    confirmed = base.RedacaoEstruturadaTests.confirmed
    save_template = base.RedacaoEstruturadaTests.save_template
    generate_draft = base.RedacaoEstruturadaTests.generate_draft
    binding = base.RedacaoEstruturadaTests.binding
    position = base.RedacaoEstruturadaTests.position
    template = base.RedacaoEstruturadaTests.template
    draft = base.RedacaoEstruturadaTests.draft

    def setUp(self):
        self.setUpBase(); self.case = self.create_case()
        self.a, self.b = self.obj(self.case), self.obj(self.case)
        self.confirmed(self.case,self.a,value='PESSOA FICTÍCIA ALFA')
        self.confirmed(self.case,self.b,value='PESSOA FICTÍCIA ALFA B')
        self.confirmed(self.case,self.a,'estado_civil','SOLTEIRA FICTÍCIA')
        self.positions = [self.position('a'),self.position('b')]
        self.text = 'TESTE FICTÍCIO\n{% repetir partes a,b %}{{item.nome}} / {{item.nome}}\n{% fim %}{% se exemplo {"campo":"a.estado_civil","permitidos":["SOLTEIRA FICTÍCIA","CASADA FICTÍCIA"],"incluir":["SOLTEIRA FICTÍCIA"]} %}BLOCO FICTÍCIO {{a.nome}}{% fim %}'
        self.template(self.case,self.positions,self.text)
        self.assertEqual(self.binding(self.case,{'a':self.a,'b':self.b})[0].status_code,201)

    def test_repeated_positions_conditional_source_and_offsets(self):
        with patch('openai.OpenAI') as external: draft = self.draft(self.case)
        external.assert_not_called()
        self.assertEqual(draft['corpo'].count('PESSOA FICTÍCIA ALFA B'),2)
        self.assertIn('BLOCO FICTÍCIO PESSOA FICTÍCIA ALFA',draft['corpo'])
        self.assertNotIn('{%',draft['corpo'])
        guard=draft['dados']['a.estado_civil']
        self.assertTrue(guard['decisoes_blocos'][0]['incluido'])
        self.assertEqual(guard['decisoes_blocos'][0]['revisao_id'],guard['revisao_id'])
        for data in draft['dados'].values():
            for occurrence in data['ocorrencias']:
                self.assertEqual(draft['corpo'][occurrence['inicio']:occurrence['fim']],data['valor'])
        self.assertEqual(draft['dados']['b.nome']['ocorrencias'][0]['repeticao']['posicao'],'b')

    def test_false_condition_omits_only_configured_text_and_records_decision(self):
        self.confirmed(self.case,self.a,'estado_civil','CASADA FICTÍCIA',versao_esperada=1)
        draft=self.draft(self.case)
        self.assertNotIn('BLOCO FICTÍCIO',draft['corpo'])
        self.assertFalse(draft['dados']['a.estado_civil']['decisoes_blocos'][0]['incluido'])

    def test_outside_scenario_or_unconfirmed_condition_blocks_without_partial_draft(self):
        old=self.draft(self.case)
        self.confirmed(self.case,self.a,'estado_civil','FORA DO CENÁRIO FICTÍCIO',versao_esperada=1)
        response=self.generate_draft(self.case)
        self.assertEqual(response.status_code,400,response.data)
        self.assertEqual(Atendimento.objects.get(pk=self.case).minutas_preparadas.count(),1)
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{self.case}/minutas/{old['id']}/exportar/",{'formato':'docx'}).status_code,409)
        self.field(self.case,self.a,'estado_civil','SOLTEIRA FICTÍCIA',versao_esperada=2)
        self.assertEqual(self.generate_draft(self.case).status_code,400)

    def test_same_record_in_two_repeated_positions_is_refused(self):
        self.assertEqual(self.binding(self.case,{'a':self.a,'b':self.a},exclusions=[{'objeto_id':self.b,'motivo':'EXCLUSÃO SIMULADA'}])[0].status_code,201)
        self.assertEqual(self.generate_draft(self.case).status_code,400)

    def test_condition_only_required_field_and_no_free_expression(self):
        for text in [self.text.replace('a.estado_civil','a.campo_inexistente'), self.text+'{% exec python %}', self.text.replace('a,b','a,z')]:
            self.assertEqual(self.save_template(self.case,expected=1,corpo=text,representacao='',observacoes='',registros_minuta=self.positions).status_code,400)

    def test_fictional_reference_is_explicit_and_never_approved_by_loading(self):
        from apps.processos.modelo_ficticio_estruturado import MODELO_FICTICIO_ETAPA7
        from apps.processos.redacao import validar_modelo
        validar_modelo(deepcopy(MODELO_FICTICIO_ETAPA7))
        response=self.save_template(self.case,approved=False,expected=1,**MODELO_FICTICIO_ETAPA7)
        self.assertEqual(response.status_code,201,response.data)
        self.assertFalse(response.data['aprovado'])
        self.assertEqual(self.generate_draft(self.case).status_code,400)

    def test_omitted_block_does_not_authorize_unconfirmed_configured_fields(self):
        self.confirmed(self.case,self.a,'estado_civil','CASADA FICTÍCIA',versao_esperada=1)
        self.field(self.case,self.b,'nome','PESSOA FICTÍCIA NÃO CONFERIDA',versao_esperada=1)
        self.assertEqual(self.generate_draft(self.case).status_code,400)

    def test_manual_edit_comparison_review_and_exports_keep_conditional_trace(self):
        from io import BytesIO
        from docx import Document
        from pypdf import PdfReader
        old=self.draft(self.case)
        text='EDIÇÃO MANUAL FICTÍCIA\n'+old['corpo']
        edited=self.client.post(f'/api/v1/atendimentos/{self.case}/editar-minuta/', {
            'client_id':str(uuid4()),'minuta_id':old['id'],'versao_esperada':old['versao'],
            'corpo':text,'motivo':'REVISÃO SINTÉTICA, SEM HOMOLOGAÇÃO'},format='json')
        self.assertEqual(edited.status_code,201,edited.data)
        new=self.client.get(f'/api/v1/atendimentos/{self.case}/minuta-preparada/').data['versoes'][0]
        self.assertEqual(new['dados'],old['dados'])
        self.assertFalse(new['ocorrencias_correspondem_texto'])
        compared=self.client.get(f'/api/v1/atendimentos/{self.case}/comparar-minutas/',{'base':old['id'],'destino':new['id']})
        self.assertEqual(compared.status_code,200,compared.data)
        self.assertTrue(compared.data['texto_alterado'])
        url=f"/api/v1/atendimentos/{self.case}/minutas/{new['id']}/exportar/"
        self.assertEqual(self.client.get(url,{'formato':'docx'}).status_code,409)
        reviewed=self.client.post(f"/api/v1/atendimentos/{self.case}/minutas/{new['id']}/revisar/", {
            'versao_esperada':new['versao'],'motivo':'REVISÃO FINAL EXCLUSIVA DO BANCO DE TESTE',
            'conferi_texto':True,'conferi_dados':True,'conferi_fontes':True},format='json')
        self.assertEqual(reviewed.status_code,201,reviewed.data)
        word=self.client.get(url,{'formato':'docx'}); pdf=self.client.get(url,{'formato':'pdf'})
        self.assertEqual(word.status_code,200); self.assertEqual(pdf.status_code,200)
        self.assertEqual('\n'.join(p.text for p in Document(BytesIO(word.content)).paragraphs[3:]),text)
        self.assertIn('EDIÇÃO MANUAL FICTÍCIA','\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages))

    def test_full_fictional_people_roles_property_and_payment_scenario(self):
        from apps.processos.modelo_ficticio_estruturado import MODELO_FICTICIO_ETAPA7 as sample
        case=self.create_case(); ids={}
        values={'vendedor':{'nome':'VENDEDORA INTEIRAMENTE FICTÍCIA'},'comprador':{'nome':'COMPRADORA INTEIRAMENTE FICTÍCIA'},
                'papel_vendedor':{'tipo_papel':'vendedor'},'papel_comprador':{'tipo_papel':'comprador'},
                'bem':{'descricao':'IMÓVEL FICTÍCIO'},'negocio':{'preco':'R$ 100.000,00','situacao_pagamento':'previsto','condicoes':'PREVISÃO FICTÍCIA PARA REVISÃO'}}
        for position in sample['registros_minuta']:
            alias=position['chave']; ids[alias]=self.obj(case,position['tipo'],**{k+'_id':ids[v] for k,v in position['vinculos'].items()})
            for key,value in values[alias].items(): self.confirmed(case,ids[alias],key,value)
        # Approval exists exclusively as a simulated human decision in test DB.
        model=self.save_template(case,**sample)
        self.assertEqual(model.status_code,201,model.data)
        self.assertEqual(self.binding(case,ids)[0].status_code,201)
        draft=self.draft(case)
        self.assertIn('BLOCO FICTÍCIO CONDICIONAL',draft['corpo'])
        self.assertEqual(draft['dados']['papel_vendedor.tipo_papel']['objeto_id'],ids['papel_vendedor'])
        self.assertEqual(draft['dados']['negocio.situacao_pagamento']['decisoes_blocos'][0]['valor_confirmado'],'previsto')
        self.confirmed(case,ids['papel_vendedor'],'tipo_papel','comprador',versao_esperada=1)
        self.assertEqual(self.generate_draft(case).status_code,400)
        self.confirmed(case,ids['papel_vendedor'],'tipo_papel','vendedor',versao_esperada=2)
        self.confirmed(case,ids['negocio'],'situacao_pagamento','declarado_realizado',versao_esperada=1)
        self.assertEqual(self.generate_draft(case).status_code,400)
        self.assertEqual(Atendimento.objects.get(pk=case).minutas_preparadas.count(),1)
