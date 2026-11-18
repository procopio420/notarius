from getpass import GetPassWarning, getpass
from pathlib import Path
from warnings import catch_warnings, simplefilter

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from apps.profiles.models import UserProfile
from apps.tenancy.models import Tenant


class Command(BaseCommand):
    help = 'Cria uma conta individual do piloto local.'

    def add_arguments(self, parser):
        parser.add_argument('--banco', required=True)
        parser.add_argument('--usuario', required=True)

    def handle(self, *args, **options):
        database = settings.DATABASES['default']
        target = Path(options['banco']).resolve()
        if (not getattr(settings, 'PILOTO_LOCAL', False)
                or database['ENGINE'] != 'django.db.backends.sqlite3'
                or target != Path(database['NAME']).resolve() or not target.is_file()):
            raise CommandError('Informe o arquivo SQLite existente selecionado para o piloto local.')

        users = get_user_model()
        username = users.normalize_username(options['usuario'].strip())
        user = users(username=username)
        try:
            user.username = users._meta.get_field('username').clean(username, user)
        except ValidationError as error:
            raise CommandError(' '.join(error.messages)) from None
        if users.objects.filter(username__iexact=user.username).exists():
            raise CommandError('Já existe uma conta com esse nome de usuário.')

        try:
            with catch_warnings():
                simplefilter('error', GetPassWarning)
                password = getpass('Senha da conta: ')
                confirmation = getpass('Repita a senha: ')
        except (GetPassWarning, EOFError):
            raise CommandError('Abra um terminal interativo para definir a senha.') from None
        if password != confirmation:
            raise CommandError('As senhas não coincidem.')
        try:
            validate_password(password, user)
        except ValidationError as error:
            raise CommandError(' '.join(error.messages)) from None

        try:
            with transaction.atomic():
                tenant, _ = Tenant.objects.get_or_create(nome='Piloto local', uf='')
                user.set_password(password)
                user.save(force_insert=True)
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.tenants.set([tenant])
                profile.default_tenant = tenant
                profile.save(update_fields=['default_tenant'])
        except IntegrityError:
            raise CommandError('Não foi possível criar a conta. Confira se o nome de usuário está disponível.') from None
        self.stdout.write(self.style.SUCCESS('Conta individual do piloto criada.'))
