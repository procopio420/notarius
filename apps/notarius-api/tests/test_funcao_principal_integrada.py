"""Nine fictional integrated journeys. Human decisions and provider are TEST ONLY."""
from io import BytesIO
from uuid import uuid4
from unittest.mock import patch
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from apps.processos.models import Atendimento, RevisaoDadoAtendimento, PropostaDadoAtendimento, PaginaAnexoAtendimento
from tests import test_redacao_estruturada as base
from tests import test_pendencias_ficha as pending
from tests import test_propostas_dados as proposals
from tests import test_comparacao_fontes as comparison
from tests import test_organizacao_anexos as documents
from tests.provedor_documental_simulado import ProvedorSimulado, resposta_ficticia


@override_settings(NOTARIUS_TESTE_ANALISE_DOCUMENTAL=True)
class FuncaoPrincipalIntegradaTests(APITestCase):
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
    issues = pending.PendenciasFichaTests.issues
    decide = pending.PendenciasFichaTests.decide
    request_proposals = proposals.PropostasDadosTests.request_proposals

    def api(self, action, data=None):
        url=f'/api/v1/atendimentos/{self.case}/{action}/'
        return self.client.get(url) if data is None else self.client.post(url,data,format='json')

    def file(self, text, owner):
        raw=text.encode()
        r=self.client.post(f'/api/v1/atendimentos/{self.case}/anexos/', {'arquivo':SimpleUploadedFile('DOCUMENTO-INTEIRAMENTE-FICTICIO.txt',raw)},format='multipart')
        self.assertEqual(r.status_code,201,r.data)
        file=r.data
        r=self.api(f"anexos/{file['id']}/organizacao", {'client_id':str(uuid4()),'versao_esperada':0,'leitura_versao':1,
            'finalidade':'caso','tipo_documento':'FONTE FICTÍCIA DE TESTE','vinculos':[{'objeto_id':owner,'paginas':[]}],
            'motivo':'ASSOCIAÇÃO EXPLÍCITA SIMULADA, NÃO INFERIDA POR NOME','conferi':True})
        self.assertEqual(r.status_code,201,r.data)
        downloaded=self.client.get(f"/api/v1/atendimentos/{self.case}/anexos/{file['id']}/download/")
        self.assertEqual(downloaded.content,raw)
        return file

    def review_pages(self):
        for row in self.issues(self.case):
            if row['tipo']=='pagina' and row['situacao']!='resolvida':
                r=self.decide(self.case,row,revisoes_ids=row['contexto']['usos_atuais'])
                self.assertEqual(r.status_code,201,r.data)

    def comparisons(self):
        for row in self.issues(self.case):
            if row['tipo']=='comparacao_fontes' and row['situacao']!='resolvida':
                rid=row['contexto']['revisao_atual']['id']
                r=comparison.ComparacaoFontesTests.resolve(self,row,rid)
                self.assertEqual(r.status_code,201,r.data)

    def build(self, extra=None, missing=False):
        self.case=self.create_case(); ids={}; positions=[]; files=[]; names={}
        people=['vendedor','comprador'] + (['vendedor2'] if extra=='vendedor2' else ['comprador2'] if extra=='comprador2' else ['conjuge'] if extra=='conjuge' else ['representante'] if extra=='representante' else [])
        for i,alias in enumerate(people):
            ids[alias]=self.obj(self.case)
            positions.append({'chave':alias,'rotulo':'POSIÇÃO FICTÍCIA '+alias,'tipo':'pessoa','vinculos':{}})
            names[alias]='PESSOA INTEIRAMENTE FICTÍCIA ALFA'+(' B'*i)
            files.append(self.file('Nome: '+names[alias],ids[alias]))
        provider=ProvedorSimulado(resposta_ficticia)
        with patch('apps.processos.analise_documental.provedor_do_ambiente',return_value=provider), patch('openai.OpenAI') as external:
            r=self.api('analise-documental',{'client_id':str(uuid4()),'documentos':[{'documento_id':f['id'],'leitura_versao':1,'organizacao_versao':1} for f in files]})
        self.assertEqual(r.status_code,201,r.data); self.assertTrue(r.data['simulado']); external.assert_not_called()
        self.assertEqual(RevisaoDadoAtendimento.objects.filter(atendimento_id=self.case).count(),0)
        current=self.api('propostas-dados').data['propostas']
        for alias,file in zip(people,files):
            proposal=next(p for p in current if p['origem'].get('anexo_id')==file['id'])
            r=proposals.PropostasDadosTests.apply(self,self.case,ids[alias],proposal,confirm=True)
            self.assertEqual(r.status_code,201,r.data)
        self.assertEqual(Atendimento.objects.get(pk=self.case).objetos_ficha.filter(tipo='relacao').count(),0)
        if extra=='conjuge':
            self.confirmed(self.case,ids['vendedor'],'estado_civil','ESTADO CIVIL FICTÍCIO INFORMADO')
            self.assertFalse(Atendimento.objects.get(pk=self.case).objetos_ficha.filter(tipo='relacao').exists())
        text='EXERCÍCIO INTEIRAMENTE FICTÍCIO — SEM VALIDADE PROFISSIONAL\n{% repetir partes '+','.join(people)+' %}{{item.nome}}\n{% fim %}'
        for alias in [p for p in people if p.startswith(('vendedor','comprador'))]:
            role='vendedor' if alias.startswith('vendedor') else 'comprador'; key='papel_'+alias
            ids[key]=self.obj(self.case,'papel',pessoa_a_id=ids[alias])
            self.confirmed(self.case,ids[key],'tipo_papel',role)
            positions.append({'chave':key,'rotulo':'PAPEL FICTÍCIO '+alias,'tipo':'papel','vinculos':{'pessoa_a':alias}})
            text+='\n{% se verificar_'+key+' {"campo":"'+key+'.tipo_papel","permitidos":["'+role+'"],"incluir":["'+role+'"]} %}Papel informado: {{'+key+'.tipo_papel}} · {{'+alias+'.nome}}{% fim %}'
        ids['bem']=self.obj(self.case,'imovel'); self.confirmed(self.case,ids['bem'],'descricao','IMÓVEL FICTÍCIO SEM MATRÍCULA REAL')
        ids['negocio']=self.obj(self.case,'negociacao',imovel_id=ids['bem'])
        for key,value in {'preco':'R$ 100.000,00','situacao_pagamento':'previsto',**({} if missing else {'condicoes':'PREVISÃO FICTÍCIA PARA DATA FUTURA'})}.items(): self.confirmed(self.case,ids['negocio'],key,value)
        positions += [{'chave':'bem','rotulo':'IMÓVEL FICTÍCIO','tipo':'imovel','vinculos':{}}, {'chave':'negocio','rotulo':'NEGOCIAÇÃO FICTÍCIA','tipo':'negociacao','vinculos':{'imovel':'bem'}}]
        text+='\nImóvel: {{bem.descricao}}\nPreço informado: {{negocio.preco}}\nSituação: {{negocio.situacao_pagamento}}\n{% se previsao {"campo":"negocio.situacao_pagamento","permitidos":["previsto"],"incluir":["previsto"]} %}Condições informadas: {{negocio.condicoes}}{% fim %}'
        if extra in ['conjuge','representante']:
            ids['relacao']=self.obj(self.case,'relacao',pessoa_a_id=ids[extra],pessoa_b_id=ids['vendedor'])
            kind='conjuge_de' if extra=='conjuge' else 'representante_de'
            self.confirmed(self.case,ids['relacao'],'tipo_relacao',kind)
            positions.append({'chave':'relacao','rotulo':'RELAÇÃO FICTÍCIA EXPLICITAMENTE INFORMADA','tipo':'relacao','vinculos':{'pessoa_a':extra,'pessoa_b':'vendedor'}})
            text+='\nRelação informada para revisão: {{relacao.tipo_relacao}}'
            if extra=='representante':
                self.field(self.case,ids['relacao'],'instrumento','INSTRUMENTO FICTÍCIO COM DÚVIDA DE ALCANCE')
                text+='\nInstrumento informado: {{relacao.instrumento}}'
        self.review_pages()
        model=self.save_template(self.case,corpo=text,representacao='',observacoes='',registros_minuta=positions)
        self.assertEqual(model.status_code,201,model.data)
        self.assertEqual(self.binding(self.case,ids)[0].status_code,201)
        return ids,names,files

    def finish(self, expected=None):
        guide=self.api('roteiro-conversa').data
        self.assertEqual(guide['pendencias'],[],guide['pendencias'])
        fresh=APIClient(); fresh.force_authenticate(self.user); fresh.credentials(HTTP_X_TENANT_ID=str(self.tenant.id)); self.client=fresh
        with patch('openai.OpenAI') as external:
            r=self.generate_draft(self.case); self.assertEqual(r.status_code,200,r.data)
            first=r.data['versoes'][0]
            if expected: self.assertIn(expected,first['corpo'])
            self.assertNotIn('quitação',first['corpo'].casefold()); self.assertNotIn('pagamento realizado',first['corpo'].casefold())
            for datum in first['dados'].values():
                self.assertTrue(datum['confirmacao']); self.assertTrue(datum['origem']['trecho'])
                for occurrence in datum['ocorrencias']:
                    self.assertEqual(first['corpo'][occurrence['inicio']:occurrence['fim']],datum['valor'])
            text=first['corpo']+'\nNOTA MANUAL EXCLUSIVAMENTE FICTÍCIA'
            r=self.api('editar-minuta',{'client_id':str(uuid4()),'minuta_id':first['id'],'versao_esperada':first['versao'],'corpo':text,'motivo':'EDIÇÃO HUMANA SIMULADA NO BANCO DE TESTE'})
            self.assertEqual(r.status_code,201,r.data)
            draft=self.api('minuta-preparada').data['versoes'][0]
            self.assertEqual(draft['dados'],first['dados']); self.assertFalse(draft['ocorrencias_correspondem_texto'])
            compared=self.client.get(f'/api/v1/atendimentos/{self.case}/comparar-minutas/',{'base':first['id'],'destino':draft['id']})
            self.assertEqual(compared.status_code,200); self.assertTrue(compared.data['texto_alterado'])
            url=f"/api/v1/atendimentos/{self.case}/minutas/{draft['id']}/exportar/"
            self.assertEqual(self.client.get(url,{'formato':'docx'}).status_code,409)
            r=self.api(f"minutas/{draft['id']}/revisar",{'versao_esperada':draft['versao'],'motivo':'REVISÃO FINAL SIMULADA, SEM HOMOLOGAÇÃO PROFISSIONAL','conferi_texto':True,'conferi_dados':True,'conferi_fontes':True})
            self.assertEqual(r.status_code,201,r.data)
            from docx import Document
            from pypdf import PdfReader
            word=self.client.get(url,{'formato':'docx'}); pdf=self.client.get(url,{'formato':'pdf'})
            self.assertEqual(word.status_code,200); self.assertEqual(pdf.status_code,200)
            self.assertEqual('\n'.join(p.text for p in Document(BytesIO(word.content)).paragraphs[3:]),text)
            self.assertIn('NOTA MANUAL EXCLUSIVAMENTE FICTÍCIA','\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages))
        external.assert_not_called()
        return draft

    def test_01_simple_sale_receives_sources_questions_review_and_export(self):
        ids,names,files=self.build(); draft=self.finish(names['vendedor'])
        self.assertEqual(draft['dados']['comprador.nome']['objeto_id'],ids['comprador'])
        self.assertEqual(self.api('roteiro-conversa').data['recebido']['documentos'],2)

    def test_02_multiple_sellers_and_buyers_keep_ids_and_order(self):
        for extra in ['vendedor2','comprador2']:
            with self.subTest(extra=extra):
                ids,names,_=self.build(extra); draft=self.finish(names[extra])
                self.assertEqual(draft['dados'][extra+'.nome']['objeto_id'],ids[extra])
                self.assertNotEqual(ids[extra],ids[extra[:-1]])

    def test_03_spouse_is_only_explicit_relation_not_inferred_co_buyer(self):
        ids,names,_=self.build('conjuge'); draft=self.finish(names['conjuge'])
        relation=Atendimento.objects.get(pk=self.case).objetos_ficha.get(pk=ids['relacao'])
        self.assertEqual(str(relation.pessoa_a_id),ids['conjuge'])
        self.assertFalse(Atendimento.objects.get(pk=self.case).objetos_ficha.filter(tipo='papel',pessoa_a_id=ids['conjuge']).exists())
        self.assertEqual(draft['dados']['relacao.tipo_relacao']['valor'],'conjuge_de')

    def test_04_representation_requires_human_decision_before_drafting(self):
        ids,_,_=self.build('representante')
        r=self.api('pendencias-ficha',{'operacao':'abrir','client_id':str(uuid4()),'objeto_id':ids['relacao'],'campo':'instrumento','pergunta':'DÚVIDA FICTÍCIA: alcance da representação a revisar','justificativa':'NÃO PRESUMIR PODERES'})
        self.assertEqual(r.status_code,201,r.data)
        self.assertEqual(self.generate_draft(self.case).status_code,400)
        self.confirmed(self.case,ids['relacao'],'instrumento','INSTRUMENTO SINTÉTICO REVISTO SOMENTE NO TESTE',versao_esperada=1)
        issue=next(p for p in self.issues(self.case) if p['tipo']=='manual' and p['situacao']!='resolvida')
        rid=str(RevisaoDadoAtendimento.objects.filter(objeto_id=ids['relacao'],chave='instrumento').first().id)
        self.assertEqual(self.decide(self.case,issue,revisoes_ids=[rid]).status_code,201)
        self.finish('INSTRUMENTO SINTÉTICO REVISTO SOMENTE NO TESTE')

    def test_05_divergent_document_keeps_both_prices_until_human_choice(self):
        ids,_,_=self.build()
        file=self.file('Preço: R$ 120.000,00',ids['bem'])
        extracted,_=self.request_proposals(self.case,anexo_id=file['id'],leitura_versao=1)
        self.assertEqual(extracted.status_code,201,extracted.data)
        p=PropostaDadoAtendimento.objects.get(pk=extracted.data['propostas_ids'][0])
        self.assertEqual(comparison.ComparacaoFontesTests.associate(self,p,ids['negocio'],'preco').status_code,201)
        groups=self.api('comparacao-fontes').data['grupos']; group=next(g for g in groups if g['campo']=='preco')
        self.assertIn('divergencia',group['problemas']); self.assertEqual(self.generate_draft(self.case).status_code,400)
        self.assertEqual(RevisaoDadoAtendimento.objects.filter(objeto_id=ids['negocio'],chave='preco').first().valor,'R$ 100.000,00')
        proposal=next(v for v in self.api('propostas-dados').data['propostas'] if v['id']==str(p.id))
        chosen=proposals.PropostasDadosTests.apply(self,self.case,ids['negocio'],proposal,key='preco',confirm=True,versao_esperada=1)
        self.assertEqual(chosen.status_code,201,chosen.data)
        self.review_pages(); self.comparisons(); self.finish('R$ 120.000,00')

    def test_06_unreadable_partial_page_cannot_be_confirmed_as_complete(self):
        ids,_,_=self.build()
        raw=documents.pdf_ficticio(['Nome: PESSOA FICTICIA PARCIAL',''])
        with patch('apps.processos.leitura_anexos.executar_ocr',return_value={'texto_ocr':'','regioes_ocr':[],'ocr_erro':'FALHA SIMULADA DE LEITURA'}), patch('apps.processos.leitura_anexos.rasterizar_pagina',return_value=b'FICTICIO'):
            file=documents.OrganizacaoAnexosTests.upload(self,self.case,raw,'PAGINAS-FICTICIAS.pdf')
        self.assertEqual(file['cobertura']['paginas_sem_texto'],[2])
        classified,_=documents.OrganizacaoAnexosTests.classify(self,self.case,file,[{'objeto_id':None,'paginas':[1,2]}])
        self.assertEqual(classified.status_code,201,classified.data)
        self.assertEqual(self.generate_draft(self.case).status_code,400)
        for issue in self.issues(self.case):
            if issue['tipo']=='pagina' and issue['situacao']!='resolvida':
                self.assertEqual(self.decide(self.case,issue,acao='nao_utilizar',justificativa='DESCARTE HUMANO SIMULADO: cópia sem uso, não comprova inexistência de fato').status_code,201)
        self.finish()

    def test_07_missing_information_is_not_synthesized(self):
        ids,_,_=self.build(missing=True)
        self.assertEqual(self.generate_draft(self.case).status_code,400)
        self.assertFalse(RevisaoDadoAtendimento.objects.filter(objeto_id=ids['negocio'],chave='condicoes').exists())
        self.assertTrue(any(q.get('destino',{}).get('campo')=='condicoes' for q in self.api('roteiro-conversa').data['pendencias']))
        self.confirmed(self.case,ids['negocio'],'condicoes','PREVISÃO FICTÍCIA INFORMADA APÓS PERGUNTA')
        self.finish('PREVISÃO FICTÍCIA INFORMADA APÓS PERGUNTA')

    def test_08_future_payment_never_turns_into_quittance(self):
        ids,_,_=self.build(); self.finish('previsto')
        self.assertFalse(RevisaoDadoAtendimento.objects.filter(objeto_id=ids['negocio'],chave='quitacao').exists())
        self.confirmed(self.case,ids['negocio'],'situacao_pagamento','declarado_realizado',versao_esperada=1)
        self.assertEqual(self.generate_draft(self.case).status_code,400)

    def test_09_correction_after_final_review_blocks_old_download(self):
        ids,_,_=self.build(); draft=self.finish()
        revision=RevisaoDadoAtendimento.objects.filter(objeto_id=ids['negocio'],chave='condicoes').first()
        original=revision.mensagem.texto
        corrected=self.api(f'mensagens/{revision.mensagem_id}/corrigir',{'client_id':str(uuid4()),'texto':'INFORMAÇÃO FICTÍCIA CORRIGIDA, AGUARDA REVISÃO','justificativa':'CORREÇÃO SIMULADA APÓS REVISÃO FINAL'})
        self.assertEqual(corrected.status_code,201,corrected.data)
        revision.refresh_from_db(); self.assertEqual(revision.mensagem.texto,original)
        self.assertEqual(self.generate_draft(self.case).status_code,400)
        self.assertEqual(self.client.get(f"/api/v1/atendimentos/{self.case}/minutas/{draft['id']}/exportar/",{'formato':'docx'}).status_code,409)
        self.assertTrue(self.api('roteiro-conversa').data['pendencias'])

class RotulosInteracaoTests(APITestCase):
    setUp=base.RedacaoEstruturadaTests.setUp
    create_case=base.RedacaoEstruturadaTests.create_case
    get=base.RedacaoEstruturadaTests.get
    post=base.RedacaoEstruturadaTests.post
    obj=base.RedacaoEstruturadaTests.obj
    field=base.RedacaoEstruturadaTests.field

    def test_roles_show_explicit_person_names_without_confirming_or_crossing_tenants(self):
        case=self.create_case(); a=self.obj(case); b=self.obj(case)
        self.field(case,a,'nome','PESSOA FICTÍCIA ALFA'); self.field(case,b,'nome','PESSOA FICTÍCIA ALFA B')
        ar=self.obj(case,'papel',pessoa_a_id=a); br=self.obj(case,'papel',pessoa_a_id=b)
        self.field(case,ar,'tipo_papel','vendedor'); self.field(case,br,'tipo_papel','vendedor')
        sheet=self.get(case).data
        labels={o['id']:o['rotulo'] for o in sheet['objetos']}
        self.assertIn('PESSOA FICTÍCIA ALFA ·',labels[ar]); self.assertIn('PESSOA FICTÍCIA ALFA B ·',labels[br])
        self.assertNotEqual(labels[ar],labels[br])
        self.assertFalse(RevisaoDadoAtendimento.objects.filter(atendimento_id=case,situacao='confirmado').exists())
        guide=self.client.get(f'/api/v1/atendimentos/{case}/roteiro-conversa/').data
        question=next(q for q in guide['pendencias'] if q.get('destino',{}).get('objeto_id')==br)
        self.assertEqual(question['destino']['registro_rotulo'],labels[br])
        state=self.client.get(f'/api/v1/atendimentos/{case}/vinculacao-minuta/').data
        self.assertFalse(state['modelo_aprovado'])
        self.user.profile.tenants.add(self.other)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertEqual(self.get(case).status_code,404)
