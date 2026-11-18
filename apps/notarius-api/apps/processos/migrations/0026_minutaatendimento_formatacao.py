from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('processos', '0025_respostachatia')]

    operations = [
        migrations.AddField(
            model_name='minutaatendimento',
            name='formatacao',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
