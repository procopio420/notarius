import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, override_settings
from apps.processos.avaliacao_ia import avaliar_resultado, validar_casos, versoes
from apps.processos.casos_avaliacao_ia import CASOS
from apps.processos.interpretacao_ia import AnaliseIndisponivel

class AvaliacaoIaTests(SimpleTestCase):
    def test_cases_have_valid_literal_expectations_and_empty_is_not_a_pass(self):
        validar_casos(CASOS)
        for case in CASOS:
            self.assertTrue(avaliar_resultado(case, {'propostas':[], 'duvidas':[]}))
        self.assertEqual(versoes(CASOS),versoes(CASOS))

    def test_swapped_roles_literal_text_still_fails(self):
        case=CASOS[0]
        wrong={'propostas':[
            {'campo':'vendedores','valor':'PESSOA BETA FICTÍCIA','trecho':case['texto']},
            {'campo':'compradores','valor':'PESSOA ALFA FICTÍCIA','trecho':case['texto']}], 'duvidas':[]}
        self.assertTrue(avaliar_resultado(case,wrong))
        correct={'propostas':[
            {'campo':field,'valor':values[0],'trecho':case['texto']} for field,values in case['permitidos'].items()], 'duvidas':[]}
        self.assertEqual(avaliar_resultado(case,correct),[])

    def test_uncertainty_and_injection_cannot_become_proposals(self):
        for key in ['preco_incerto','injecao_instrucao','nao_corrigir_valor']:
            case=next(c for c in CASOS if c['id']==key)
            self.assertEqual(avaliar_resultado(case,{'propostas':[], 'duvidas':[case['texto']]}),[])
            wrong={'propostas':[{'campo':'preco','valor':case['texto'],'trecho':case['texto']}], 'duvidas':[case['texto']]}
            self.assertTrue(avaliar_resultado(case,wrong))

    def test_local_report_does_not_claim_model_was_evaluated_or_call_provider(self):
        with TemporaryDirectory() as directory, patch('apps.processos.management.commands.avaliar_ia_compra_venda.analisar_mensagem') as provider:
            output=Path(directory)/'report.json'
            call_command('avaliar_ia_compra_venda',saida=str(output),stdout=StringIO())
            report=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['avaliacao_modelo'],'nao_executada')
            self.assertEqual(report['resultados'],[])
            provider.assert_not_called()
            with self.assertRaises(CommandError):
                call_command('avaliar_ia_compra_venda',saida=str(output),stdout=StringIO())

    @override_settings(OPENAI_API_KEY='', AI_GENERATION_ENABLED=True)
    def test_execution_without_key_is_explicitly_simulated(self):
        with TemporaryDirectory() as directory, patch('openai.OpenAI') as provider:
            output = Path(directory)/'report.json'
            with self.assertRaises(CommandError):
                call_command('avaliar_ia_compra_venda',executar=True,saida=str(output),stdout=StringIO())
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['modo'], 'simulacao_local')
            self.assertEqual(report['modelo'], 'simulador_por_rotulos')
            provider.assert_not_called()

    @override_settings(OPENAI_API_KEY='fake-only', AI_GENERATION_ENABLED=True)
    def test_provider_failure_is_inconclusive_and_stops_further_calls(self):
        with TemporaryDirectory() as directory, patch('apps.processos.management.commands.avaliar_ia_compra_venda.analisar_mensagem',side_effect=AnaliseIndisponivel('Failure')) as provider:
            output=Path(directory)/'report.json'
            with self.assertRaises(CommandError):
                call_command('avaliar_ia_compra_venda',executar=True,saida=str(output),stdout=StringIO())
            report=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['avaliacao_modelo'],'inconclusiva')
            self.assertEqual(len(report['resultados']),1)
            provider.assert_called_once()

    @override_settings(OPENAI_API_KEY='fake-only', AI_GENERATION_ENABLED=True)
    def test_semantic_failures_exit_unsuccessfully_even_with_valid_structure(self):
        with TemporaryDirectory() as directory, patch('apps.processos.management.commands.avaliar_ia_compra_venda.analisar_mensagem',return_value={'propostas':[], 'duvidas':[]}):
            output=Path(directory)/'report.json'
            with self.assertRaises(CommandError):
                call_command('avaliar_ia_compra_venda',executar=True,saida=str(output),stdout=StringIO())
            report=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['avaliacao_modelo'],'reprovada')
            self.assertEqual(len(report['resultados']),len(CASOS))
