from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('processos', '0026_minutaatendimento_formatacao')]

    operations = [
        migrations.AddField(
            model_name='minutaatendimento', name='assistencia',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
