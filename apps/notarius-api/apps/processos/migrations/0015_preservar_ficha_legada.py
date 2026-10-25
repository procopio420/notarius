from django.db import migrations
from django.db.models import F


def preservar(apps, schema_editor):
    Revision = apps.get_model('processos', 'RevisaoDadoAtendimento')
    Case = apps.get_model('processos', 'Atendimento')
    Object = apps.get_model('processos', 'ObjetoFichaAtendimento')
    alias = schema_editor.connection.alias
    revisions = Revision.objects.using(alias).filter(objeto__isnull=True)
    # No parsing, entity creation from text, reassignment or inherited confirmation.
    revisions.update(valor_original=F('valor'))
    for case in Case.objects.using(alias).filter(pk__in=revisions.values('atendimento_id')).iterator():
        Object.objects.using(alias).get_or_create(atendimento_id=case.id, tipo='legado',
            defaults={'tenant_id': case.tenant_id, 'autor_id': case.criado_por_id})


class Migration(migrations.Migration):
    dependencies = [('processos', '0014_eventofichaatendimento_objetofichaatendimento_and_more')]
    operations = [migrations.RunPython(preservar, migrations.RunPython.noop)]
