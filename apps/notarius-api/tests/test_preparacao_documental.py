"""Offline evaluation only. Every provider answer below is a handwritten test fixture."""
import json
import tempfile
from copy import deepcopy
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from django.test import SimpleTestCase, override_settings
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APITestCase
from apps.processos.politica_documental import LIMITES, diagnostico, codigo_falha
from apps.processos.provedor_documental import ProvedorReal, ProvedorIndisponivel, RespostaInvalida
from apps.processos.casos_avaliacao_documental import casos
from apps.processos.avaliacao_documental import validar_casos, avaliar_caso, versoes
from tests import test_analise_documental as base
from tests.provedor_documental_simulado import ProvedorSimulado, resposta_ficticia


def resposta_manual(case):
    """Gold-derived fixture ONLY to test the evaluator; never a model evaluation."""
    rows=[]
    for unit in case['entrada']['unidades']:
        proposals=[]
        for expected in case['obrigatorios']:
            if expected['unidade_id']!=unit['unidade_id']: continue
            proposals.append({**{k:v for k,v in expected.items() if k!='unidade_id'},
                'relacionado_id':expected['registro_sugerido_id'],'fonte':unit['fonte'],
                'trecho':unit['texto'],'inicio':0,'fim':len(unit['texto'])})
        rows.append({'unidade_id':unit['unidade_id'],'situacao':'propostas' if proposals else 'revisao_manual',
                     'propostas':proposals,'duvidas':['FIXTURE SIMULADA: revisão humana necessária.'] if case['duvida_obrigatoria'] or not proposals else []})
    return {'contrato':'documental_v1','contexto_assinatura':case['entrada']['contexto_assinatura'],'unidades':rows}


def envelope(raw):
    return {'status':'completed','output':[{'type':'message','role':'assistant','status':'completed',
            'content':[{'type':'output_text','text':json.dumps(raw,ensure_ascii=False)}]}]}


class PreparacaoOfflineTests(SimpleTestCase):
    def test_diagnostico_never_exposes_key_or_authorizes_send(self):
        for env in [{},{'OPENAI_API_KEY':'SEGREDO-FICTICIO-TESTE','NOTARIUS_MODELO_DOCUMENTAL':'MODELO-TESTE'},
                    {'OPENAI_BASE_URL':'https://destino-nao-permitido.invalid'}]:
            with self.subTest(env_keys=list(env)), patch('openai.OpenAI') as sync, patch('openai.AsyncOpenAI') as async_client, patch('socket.create_connection',side_effect=AssertionError('Rede proibida')):
                report=diagnostico(env)
            sync.assert_not_called(); async_client.assert_not_called()
            self.assertFalse(report['disponivel'])
            self.assertIn('transporte_real_nao_implementado',report['pendencias'])
            self.assertNotIn('SEGREDO-FICTICIO-TESTE',json.dumps(report))
            self.assertNotIn('MODELO-TESTE',json.dumps(report))
        self.assertIn('chave_ausente',diagnostico({})['pendencias'])
        self.assertIn('destino_alternativo_nao_permitido',diagnostico({'OPENAI_BASE_URL':'https://outro.invalid'})['pendencias'])

    def test_error_classification_is_sanitized_and_distinguishes_quota_rate_timeout(self):
        samples=[(TimeoutError('SEGREDO'),'tempo_esgotado'),(Exception('SEGREDO'),'provedor_indisponivel')]
        for status,code,expected in [(429,'insufficient_quota','creditos_indisponiveis'),(429,'rate_limit_exceeded','limite_temporario'),(401,None,'credencial_recusada'),(503,None,'provedor_indisponivel')]:
            error=Exception('SEGREDO'); error.status_code=status; error.body={'error':{'code':code}}
            samples.append((error,expected))
        error=Exception('SEGREDO'); error.codigo=[]; error.body={'code':{}}
        samples.append((error,'provedor_indisponivel'))
        for error,expected in samples: self.assertEqual(codigo_falha(error),expected)
        self.assertEqual(ProvedorIndisponivel(codigo=[]).codigo,'provedor_indisponivel')

    def test_planned_limits_and_request_reject_missing_model_oversize_and_bad_response(self):
        options=ProvedorReal.opcoes_cliente_planejado()
        self.assertEqual(options['max_retries'],0)
        self.assertEqual(options['timeout'],{'connect':5,'read':45,'write':10,'pool':5})
        self.assertEqual(options['prazo_total_s'],60)
        self.assertEqual(LIMITES.tentativas_por_acao,1)
        for model in [None,'',' '*3,True,'a'*121]:
            with self.assertRaises(RespostaInvalida): ProvedorReal.preparar_requisicao(SimpleNamespace(model_dump=lambda:{}),model)
        with self.assertRaises(RespostaInvalida):
            ProvedorReal.preparar_requisicao(SimpleNamespace(model_dump=lambda:{'texto':'a'*600000}),'MODELO-TESTE')
        for text in ['a'*500001,'\ud800','['*1500]:
            data=envelope({}); data['output'][0]['content'][0]['text']=text
            with self.assertRaises(RespostaInvalida): ProvedorReal.interpretar_resposta(data)

    def test_all_ten_fictional_oracles_and_sources_validate_without_network(self):
        corpus=casos(); self.assertEqual(len(corpus),10); validar_casos(corpus)
        for case in corpus:
            with self.subTest(case=case['id']): self.assertEqual(avaliar_caso(case,resposta_manual(case))['erros'],[])

    def test_evaluator_catches_omissions_wrong_people_values_versions_and_context(self):
        corpus={c['id']:c for c in casos()}
        case=corpus['nomes_proximos']
        for change in ['pessoa','valor','fonte','omissao','trecho','duvida','quitacao','releitura']:
            current=corpus['pagamento_futuro'] if change=='quitacao' else corpus['releitura_corrigida'] if change=='releitura' else corpus['cpf_divergente'] if change=='duvida' else case
            raw=resposta_manual(current); p=raw['unidades'][0]['propostas'][0]
            if change=='pessoa': p.update(registro_sugerido_id=raw['unidades'][1]['propostas'][0]['registro_sugerido_id'],relacionado_id=raw['unidades'][1]['propostas'][0]['relacionado_id'])
            elif change=='valor': p['valor']='NOME INVENTADO'
            elif change in ['fonte','releitura']: p['fonte']['leitura_versao']=99
            elif change=='omissao': raw['unidades'].pop()
            elif change=='trecho': p.update(trecho=p['valor'],inicio=6,fim=6+len(p['valor']))
            elif change=='duvida': raw['unidades'][0]['duvidas']=[]
            elif change=='quitacao': p['valor']='quitado'
            with self.subTest(change=change): self.assertTrue(avaliar_caso(current,raw)['erros'])
        for key in ['pagina_sem_texto','instrucao_maliciosa','preco_ausente']:
            raw=resposta_manual(corpus[key]); raw['unidades'][0]['duvidas']=[]
            self.assertTrue(avaliar_caso(corpus[key],raw)['erros'])

    def test_commands_prepare_and_check_only_offline_without_attesting_ai(self):
        with tempfile.TemporaryDirectory() as temp, patch('openai.OpenAI') as sync, patch('openai.AsyncOpenAI') as async_client, patch('httpx.Client.send',side_effect=AssertionError('Rede proibida')):
            directory=Path(temp); destination=directory/'plano.json'
            call_command('avaliar_ia_documental',saida=str(destination),stdout=StringIO())
            plan=json.loads(destination.read_text(encoding='utf-8'))
            self.assertEqual(plan['avaliacao_real'],'nao_executada')
            self.assertTrue(all(c['requisicao_planejada'] is None for c in plan['casos']))
            with self.assertRaises(CommandError): call_command('avaliar_ia_documental',saida=str(destination),stdout=StringIO())
            with self.assertRaises(CommandError): call_command('avaliar_ia_documental',saida=str(directory/'proibido.json'),executar_real=True,stdout=StringIO())
            self.assertFalse((directory/'proibido.json').exists())
            source=directory/'fixtures-simuladas.json'; corpus=casos()
            source.write_text(json.dumps({'versoes':versoes(corpus),'respostas':[{'caso':c['id'],'resposta_api':envelope(resposta_manual(c))} for c in corpus]}),encoding='utf-8')
            call_command('avaliar_ia_documental',saida=str(directory/'resultado.json'),respostas=str(source),stdout=StringIO())
            report=json.loads((directory/'resultado.json').read_text(encoding='utf-8'))
            self.assertEqual(report['origem_das_respostas'],'nao_atestada')
            self.assertEqual(report['resultado'],'sem_erros_nos_casos_fornecidos')
            self.assertEqual(report['avaliacao_real'],'nao_executada_por_este_comando')
            source.write_text('{"versoes":{},"respostas":[]}',encoding='utf-8')
            with self.assertRaises(CommandError): call_command('avaliar_ia_documental',saida=str(directory/'invalido.json'),respostas=str(source),stdout=StringIO())
            self.assertFalse((directory/'invalido.json').exists())
            call_command('diagnosticar_ia_documental',saida=str(directory/'diagnostico.json'),stdout=StringIO())
        sync.assert_not_called(); async_client.assert_not_called()


@override_settings(NOTARIUS_TESTE_ANALISE_DOCUMENTAL=True)
class PreservacaoDocumentalTests(APITestCase):
    setUpBase=base.AnaliseDocumentalTests.setUpBase
    create_case=base.AnaliseDocumentalTests.create_case
    get=base.AnaliseDocumentalTests.get
    post=base.AnaliseDocumentalTests.post
    obj=base.AnaliseDocumentalTests.obj
    field=base.AnaliseDocumentalTests.field
    setUp=base.AnaliseDocumentalTests.setUp
    document=base.AnaliseDocumentalTests.document
    classify=base.AnaliseDocumentalTests.classify
    analyse=base.AnaliseDocumentalTests.analyse
    counts=base.AnaliseDocumentalTests.counts

    def test_normal_replay_cannot_return_saved_simulation(self):
        response,_=self.analyse(); self.assertEqual(response.status_code,201)
        before=self.counts()
        with patch('openai.OpenAI') as sdk:
            response=self.client.post(self.url,self.payload,format='json')
        self.assertEqual(response.status_code,503,response.data)
        self.assertEqual(response.data['codigo'],'ia_bloqueada')
        self.assertEqual(before,self.counts()); sdk.assert_not_called()
        history=self.client.get(self.url).data
        self.assertTrue(history['analises'][0]['simulado'])
        self.assertFalse(history['preparacao']['disponivel'])

    def test_failures_preserve_work_are_clear_and_can_be_retried_explicitly(self):
        quota=Exception('SEGREDO-FICTICIO'); quota.body={'error':{'code':'insufficient_quota'}}
        errors=[(TimeoutError('SEGREDO-FICTICIO'),'tempo_esgotado'),(quota,'creditos_indisponiveis'),
                (ProvedorIndisponivel(codigo='chave_ausente'),'chave_ausente'),(Exception('SEGREDO-FICTICIO'),'provedor_indisponivel')]
        before=self.counts()
        original=self.client.get(f'/api/v1/atendimentos/{self.case}/anexos/').data
        for error,code in errors:
            response,provider=self.analyse(error=error)
            self.assertEqual(response.status_code,503,response.data)
            self.assertEqual(response.data['codigo'],code)
            self.assertNotIn('SEGREDO-FICTICIO',json.dumps(response.data))
            self.assertEqual(provider.chamadas,1); self.assertEqual(before,self.counts())
            self.assertEqual(original,self.client.get(f'/api/v1/atendimentos/{self.case}/anexos/').data)
        response,_=self.analyse(); self.assertEqual(response.status_code,201,response.data)
        after=self.counts(); response,provider=self.analyse()
        self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(provider.chamadas,0); self.assertEqual(after,self.counts())

    def test_simulated_provider_rejected_outside_test_flag_without_writes(self):
        provider=ProvedorSimulado(resposta_ficticia); before=self.counts()
        with override_settings(NOTARIUS_TESTE_ANALISE_DOCUMENTAL=False), patch('apps.processos.analise_documental.provedor_do_ambiente',return_value=provider):
            response=self.client.post(self.url,self.payload,format='json')
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.data['codigo'],'simulacao_fora_teste')
        self.assertEqual(provider.chamadas,0); self.assertEqual(before,self.counts())

    def test_blank_doubt_cannot_make_missing_information_look_processed(self):
        before=self.counts()
        def invalid(data,entry):
            data['unidades'][1]['duvidas']=['   ']
            return data
        response,_=self.analyse(invalid)
        self.assertEqual(response.status_code,422,response.data)
        self.assertEqual(before,self.counts())
