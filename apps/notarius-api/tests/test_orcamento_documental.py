import tempfile
import sqlite3
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from apps.processos.orcamento_documental import criar_registro, reservar, OrcamentoBloqueado


class OrcamentoTests(TestCase):
    def setUp(self):
        private = Path(__file__).resolve().parents[3] / '.local'
        private.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=private)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'orcamento.sqlite3'
        self.request = {'model': 'gpt-6-luna', 'store': False, 'max_output_tokens': 4000,
                        'input': [{'role': 'system', 'content': 'Extrair dados.'},
                                  {'role': 'user', 'content': 'Documento fictício.'}],
                        'text': {'format': {'type': 'json_schema'}}}

    def test_missing_or_corrupt_ledger_blocks_without_reset(self):
        with self.assertRaises(OrcamentoBloqueado):
            reservar(self.request, self.path)
        self.assertFalse(self.path.exists())
        self.path.write_bytes(b'invalid')
        with self.assertRaises(OrcamentoBloqueado):
            reservar(self.request, self.path)
        with self.assertRaises(FileExistsError):
            criar_registro(self.path)

    def test_parallel_attempts_never_exceed_budget_and_survive_reopen(self):
        criar_registro(self.path)
        def attempt(_):
            try:
                return reservar(self.request, self.path)
            except OrcamentoBloqueado:
                return None
        with ThreadPoolExecutor(max_workers=8) as executor:
            values = list(executor.map(attempt, range(25)))
        self.assertEqual(sorted(v for v in values if v is not None), list(range(5, 51, 5)))
        with self.assertRaises(OrcamentoBloqueado):
            reservar(self.request, self.path)

    def test_rejects_model_tools_images_large_input_and_output(self):
        criar_registro(self.path)
        invalid = [{**self.request, 'model': 'gpt-6-astra'},
                   {**self.request, 'tools': []},
                   {**self.request, 'max_output_tokens': 4001},
                   {**self.request, 'store': True},
                   {**self.request, 'input': [{'role': 'user', 'content': []}]},
                   {**self.request, 'input': [{'role': 'system', 'content': 'x'},
                                             {'role': 'user', 'content': 'x' * 32001}]}]
        for request in invalid:
            with self.subTest(keys=list(request)), self.assertRaises(OrcamentoBloqueado):
                reservar(request, self.path)
        self.assertEqual(reservar(self.request, self.path), 5)

    def test_lower_ceiling_preserves_previous_reservations(self):
        criar_registro(self.path)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute('UPDATE orcamento SET reservado=45')
        self.assertEqual(reservar(self.request, self.path), 50)
        with self.assertRaises(OrcamentoBloqueado):
            reservar(self.request, self.path)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute('UPDATE orcamento SET reservado=80')
        with self.assertRaises(OrcamentoBloqueado):
            reservar(self.request, self.path)

    def test_ten_fictional_payloads_fit_small_limits_without_reserving_or_sending(self):
        from apps.processos.casos_avaliacao_documental import casos
        from apps.processos.contratos_documentais import EntradaDocumental
        from apps.processos.provedor_documental import ProvedorReal, ProvedorIndisponivel
        with patch('socket.create_connection', side_effect=AssertionError('Rede proibida')), \
                patch('openai.OpenAI', side_effect=AssertionError('API proibida')), \
                patch('openai.AsyncOpenAI', side_effect=AssertionError('API proibida')):
            examples = casos()
            self.assertEqual(len(examples), 10)
            for case in examples:
                entrada = EntradaDocumental.model_validate(case['entrada'])
                request = ProvedorReal.preparar_requisicao_teste(entrada)
                self.assertEqual(request['model'], 'gpt-6-luna')
                self.assertEqual(request['max_output_tokens'], 4000)
                with self.assertRaises(ProvedorIndisponivel):
                    ProvedorReal().analisar(entrada)
        self.assertFalse(self.path.exists())
