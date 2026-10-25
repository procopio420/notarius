from getpass import getpass
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.processos.backup_local import read_backup, write_new, MAX_DB, BackupInvalido

class Command(BaseCommand):
    help = 'Verifica backup e opcionalmente recupera uma cópia SQLite NOVA, sem substituir o banco ativo.'
    def add_arguments(self,parser):
        parser.add_argument('--arquivo',required=True)
        parser.add_argument('--recuperar-em')
    def handle(self,*args,**options):
        source=Path(options['arquivo']).resolve()
        destination=Path(options['recuperar_em']).resolve() if options['recuperar_em'] else None
        if destination and (destination.exists() or destination == Path(settings.DATABASES['default']['NAME']).resolve() or not destination.parent.is_dir()):
            raise CommandError('A recuperação exige um arquivo NOVO e não pode substituir o banco ativo.')
        if not source.is_file() or source.stat().st_size > MAX_DB+65536:
            raise CommandError('Backup ausente ou acima do limite de tamanho.')
        try:
            database, manifest=read_backup(source.read_bytes(),getpass('Senha do backup: '))
            if destination:
                write_new(destination,database)
        except (BackupInvalido,OSError) as error:
            raise CommandError(str(error)) from None
        self.stdout.write('Backup verificado. Data UTC: '+manifest['criado_em'])
        for name,count in manifest['contagens'].items():
            self.stdout.write(f'{name}: {count}')
        if destination:
            self.stdout.write('Cópia recuperada: '+str(destination))
            self.stdout.write('ATENÇÃO: essa cópia contém dados sem criptografia. O banco ativo não foi alterado.')
        else:
            self.stdout.write('Somente verificação; nenhum banco foi gravado ou substituído.')
