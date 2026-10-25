import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from apps.tenancy.models import Tenant
from apps.processos.cenarios_homologacao import preparar, especificacao, arquivos


class Command(BaseCommand):
    help = 'Prepara dois cenários fictícios sem aprovar modelos nem confirmar dados.'

    def add_arguments(self, parser):
        parser.add_argument('--cartorio-id', required=True)
        parser.add_argument('--usuario-id', required=True)
        parser.add_argument('--saida', required=True)

    def handle(self, *args, **options):
        def write_preserving(path, text):
            if path.exists() and path.read_text(encoding='utf-8') != text:
                raise CommandError(f'Arquivo alterado anteriormente; preservado sem sobrescrever: {path}')
            if not path.exists():
                path.write_text(text, encoding='utf-8')
        try:
            tenant = Tenant.objects.get(id=options['cartorio_id'])
            user = get_user_model().objects.get(id=options['usuario_id'])
            result = []
            for variant in ['direta', 'procuracao']:
                manifest, _ = preparar(tenant, user, variant)
                result.append(manifest)
            target = Path(options['saida']).resolve()
            target.mkdir(parents=True, exist_ok=True)
            for manifest in result:
                spec = especificacao(manifest['variante'])
                folder = target / manifest['variante']; folder.mkdir(exist_ok=True)
                for name, text in arquivos(spec).items():
                    write_preserving(folder / name, text)
                write_preserving(folder / 'mensagem-ficticia.txt', spec['mensagem'])
                write_preserving(folder / 'modelo-rascunho.txt', spec['modelo']['corpo'])
            write_preserving(target / 'manifesto-ficticio.json', json.dumps(result, ensure_ascii=False, indent=2))
            for manifest in result:
                self.stdout.write(f"{manifest['variante']}: {manifest['atendimento_id']} — material fictício inicial preservado; consultar o estado atual no atendimento")
        except (Tenant.DoesNotExist, get_user_model().DoesNotExist, ValidationError) as error:
            raise CommandError(str(error)) from error
