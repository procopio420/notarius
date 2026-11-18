import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from apps.processos.provedor_documental import ProvedorTesteControlado, ProvedorReal, ProvedorIndisponivel, RespostaInvalida
from apps.processos.orcamento_documental import criar_registro, OrcamentoBloqueado
from apps.processos.casos_avaliacao_documental import casos
from apps.processos.contratos_documentais import EntradaDocumental


class TransporteTests(TestCase):
    def test_budget_commits_before_client_and_exhaustion_never_connects(self):
        private = Path(__file__).resolve().parents[3] / '.local'
        with tempfile.TemporaryDirectory(dir=private) as directory:
            ledger = Path(directory) / 'budget.sqlite3'
            criar_registro(ledger)
            provider = ProvedorTesteControlado('CHAVE-FICTICIA', ledger)
            entry = EntradaDocumental.model_validate(casos()[0]['entrada'])
            with patch('openai.OpenAI', side_effect=TimeoutError) as client:
                for _ in range(10):
                    with self.assertRaises(ProvedorIndisponivel):
                        provider.analisar(entry)
                self.assertEqual(client.call_count, 10)
                with self.assertRaises(OrcamentoBloqueado):
                    provider.analisar(entry)
                self.assertEqual(client.call_count, 10)
                self.assertEqual(client.call_args.kwargs['max_retries'], 0)

    def test_reasoning_is_not_evidence_and_tool_calls_still_rejected(self):
        raw = {'contrato': 'documental_v1', 'contexto_assinatura': '0'*64,
               'unidades': [{'unidade_id': '1', 'situacao': 'revisao_manual', 'propostas': [], 'duvidas': ['Confira o original.']}]}
        message = {'type': 'message', 'role': 'assistant', 'status': 'completed',
                   'content': [{'type': 'output_text', 'text': json.dumps(raw)}]}
        envelope = {'status': 'completed', 'output': [{'type': 'reasoning', 'summary': []}, message]}
        self.assertEqual(ProvedorReal.interpretar_resposta(envelope).contrato, 'documental_v1')
        envelope['output'] = [{'type': 'reasoning', 'summary': []}]
        with self.assertRaises(RespostaInvalida):
            ProvedorReal.interpretar_resposta(envelope)
        envelope['output'] = [{'type': 'function_call'}, message]
        with self.assertRaises(RespostaInvalida):
            ProvedorReal.interpretar_resposta(envelope)
