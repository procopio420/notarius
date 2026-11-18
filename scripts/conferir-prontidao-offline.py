"""Run fictional local regressions with socket connections and SDK clients blocked.

No paid model tests, no API key checks and no operations on the selected case.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


def main():
    root = Path(__file__).resolve().parent.parent
    tempfile.tempdir = str(root / '.local')
    sys.path.insert(0, str(root / 'apps' / 'notarius-api'))
    os.chdir(root / 'apps' / 'notarius-api')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_piloto'
    os.environ['OPENAI_API_KEY'] = ''
    modules = [
        'tests.test_orcamento_documental',
        'tests.test_preparacao_documental',
        'tests.test_analise_documental',
        'tests.test_piloto_local',
        'tests.test_organizacao_anexos',
        'tests.test_ocr_atendimentos',
        'tests.test_funcao_principal_integrada',
        'tests.test_exportacao_piloto',
    ]
    with patch('socket.create_connection', side_effect=AssertionError('Conexão proibida no ensaio offline')), \
            patch('socket.socket.connect', side_effect=AssertionError('Conexão proibida no ensaio offline')), \
            patch('socket.socket.connect_ex', side_effect=AssertionError('Conexão proibida no ensaio offline')), \
            patch('openai.OpenAI', side_effect=AssertionError('Cliente pago proibido no ensaio offline')), \
            patch('openai.AsyncOpenAI', side_effect=AssertionError('Cliente pago proibido no ensaio offline')):
        import django
        django.setup()
        from django.test.runner import DiscoverRunner
        selected = sys.argv[1:] or modules
        if any(not label.startswith('tests.test_') for label in selected):
            raise SystemExit('Use somente módulos de teste locais nomeados tests.test_*.')
        failures = DiscoverRunner(verbosity=2, interactive=False).run_tests(selected)
    return bool(failures)


if __name__ == '__main__':
    sys.exit(main())
