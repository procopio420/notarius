# Generated migration for ValidationResult model

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenancy', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ValidationResult',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('document_type', models.CharField(db_index=True, max_length=100)),
                ('extracted_data', models.JSONField(default=dict)),
                ('exigencias', models.JSONField(default=list, help_text='Required items')),
                ('bloqueantes', models.JSONField(default=list, help_text='Blocking issues')),
                ('opcionais', models.JSONField(default=list, help_text='Optional items')),
                ('citacoes', models.JSONField(default=list, help_text='Citations')),
                ('uf', models.CharField(blank=True, max_length=2, null=True)),
                ('validation_date', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='validationresults', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'validation_results',
            },
        ),
        migrations.AddIndex(
            model_name='validationresult',
            index=models.Index(fields=['tenant', 'document_type'], name='validation__tenant__idx'),
        ),
        migrations.AddIndex(
            model_name='validationresult',
            index=models.Index(fields=['tenant', 'validation_date'], name='validation__tenant__validation_date_idx'),
        ),
    ]

