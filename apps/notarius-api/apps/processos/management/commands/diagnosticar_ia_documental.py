import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from apps.processos.politica_documental import diagnostico

class Command(BaseCommand):
    help='Diagnóstico local sem chave em saída, sem consultar saldo ou fazer rede. Não ativa IA.'
    def add_arguments(self,parser):
        parser.add_argument('--saida',required=True)
    def handle(self,*args,**options):
        path=Path(options['saida']).resolve()
        if path.exists() or not path.parent.is_dir(): raise CommandError('Use arquivo novo em pasta existente.')
        with path.open('x',encoding='utf-8') as f: json.dump(diagnostico(),f,ensure_ascii=False,indent=2)
        self.stdout.write('Diagnóstico salvo. IA bloqueada; saldo não consultado; nenhuma chamada externa. A chave não é exibida.')
