"""
Django management command to create default document templates.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.documentos.models import DocumentTemplate
from apps.tenants.models import Tenant

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default document templates for all tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='Create templates for specific tenant only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing templates',
        )

    def handle(self, *args, **options):
        tenant_id = options.get('tenant_id')
        force = options.get('force', False)
        
        # Get tenants to process
        if tenant_id:
            try:
                tenants = [Tenant.objects.get(id=tenant_id)]
            except Tenant.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Tenant with ID {tenant_id} not found')
                )
                return
        else:
            tenants = Tenant.objects.all()
        
        # Get or create a system user for template creation
        system_user, created = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@notarius.com',
                'first_name': 'System',
                'last_name': 'User',
                'is_active': False,
            }
        )
        
        # Default templates configuration
        default_templates = [
            {
                'name': 'procuracao',
                'document_type': 'procuracao',
                'template_path': 'procuracao.html',
                'description': 'Template padrão para procurações',
                'is_default': True,
            },
            {
                'name': 'certidao',
                'document_type': 'certidao',
                'template_path': 'certidao.html',
                'description': 'Template padrão para certidões',
                'is_default': True,
            },
            {
                'name': 'testamento',
                'document_type': 'testamento',
                'template_path': 'testamento.html',
                'description': 'Template padrão para testamentos',
                'is_default': True,
            },
            {
                'name': 'escritura',
                'document_type': 'escritura',
                'template_path': 'escritura.html',
                'description': 'Template padrão para escrituras',
                'is_default': True,
            },
            {
                'name': 'contrato',
                'document_type': 'contrato',
                'template_path': 'contrato.html',
                'description': 'Template padrão para contratos',
                'is_default': True,
            },
        ]
        
        total_created = 0
        total_updated = 0
        
        for tenant in tenants:
            self.stdout.write(f'Processing tenant: {tenant.nome}')
            
            for template_config in default_templates:
                template, created = DocumentTemplate.objects.get_or_create(
                    tenant=tenant,
                    name=template_config['name'],
                    defaults={
                        'document_type': template_config['document_type'],
                        'template_path': template_config['template_path'],
                        'description': template_config['description'],
                        'is_default': template_config['is_default'],
                        'is_active': True,
                        'created_by': system_user,
                    }
                )
                
                if created:
                    total_created += 1
                    self.stdout.write(
                        f'  Created template: {template.name} ({template.document_type})'
                    )
                elif force:
                    # Update existing template
                    template.document_type = template_config['document_type']
                    template.template_path = template_config['template_path']
                    template.description = template_config['description']
                    template.is_default = template_config['is_default']
                    template.is_active = True
                    template.updated_by = system_user
                    template.save()
                    
                    total_updated += 1
                    self.stdout.write(
                        f'  Updated template: {template.name} ({template.document_type})'
                    )
                else:
                    self.stdout.write(
                        f'  Template already exists: {template.name} ({template.document_type})'
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(tenants)} tenants. '
                f'Created: {total_created}, Updated: {total_updated}'
            )
        )
