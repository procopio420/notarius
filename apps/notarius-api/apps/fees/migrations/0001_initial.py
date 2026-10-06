# Generated migration for FeeRule model

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
            name='FeeRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('uf', models.CharField(db_index=True, max_length=2)),
                ('document_type', models.CharField(db_index=True, max_length=100)),
                ('fee_type', models.CharField(db_index=True, max_length=50)),
                ('value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('version', models.CharField(default='2024.1', max_length=20)),
                ('effective_date', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='feerules', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'fee_rules',
            },
        ),
        migrations.AddIndex(
            model_name='feerule',
            index=models.Index(fields=['tenant', 'uf', 'document_type'], name='fee_rules_tenant_uf_doc_idx'),
        ),
        migrations.AddIndex(
            model_name='feerule',
            index=models.Index(fields=['uf', 'document_type', 'fee_type', 'is_active'], name='fee_rules_uf_doc_fee_active_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='feerule',
            unique_together={('uf', 'document_type', 'fee_type', 'version')},
        ),
    ]

