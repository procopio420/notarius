from getpass import getpass
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.processos.backup_local import make_backup, write_new, BackupInvalido

class Command(BaseCommand):
    help = 'Cria backup local criptografado do SQLite; senha solicitada sem aparecer na tela.'
    def add_arguments(self, parser):
        parser.add_argument('--saida', required=True)
    def handle(self, *args, **options):
        config=settings.DATABASES['default']
        if config['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('Este comando atende somente o piloto SQLite local.')
        target=Path(options['saida']).resolve()
        if target.exists() or not target.parent.is_dir():
            raise CommandError('Escolha um arquivo novo em uma pasta existente.')
        self.stdout.write('Inclui TODOS os cartórios, usuários e anexos no banco. Não inclui .env nem arquivos externos. Guarde a senha: ela não pode ser recuperada.')
        password=getpass('Senha do backup (mínimo 12 caracteres): ')
        if password != getpass('Repita a senha: '):
            raise CommandError('As senhas não coincidem. Nenhum backup foi criado.')
        try:
            content, manifest=make_backup(config['NAME'],password)
            write_new(target,content)
        except (BackupInvalido,OSError) as error:
            raise CommandError(str(error)) from None
        except Exception:
            raise CommandError('Não consegui criar o backup. O banco original foi preservado.') from None
        self.stdout.write('Backup criptografado criado: '+str(target))
        self.stdout.write('Atendimentos na cópia: '+str(manifest['contagens']['atendimentos']))
