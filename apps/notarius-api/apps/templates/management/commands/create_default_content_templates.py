from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.documentos.models import Template
from apps.tenancy.models import Tenant

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default content templates for document generation'

    def handle(self, *args, **options):
        # Get or create default tenant
        tenant, created = Tenant.objects.get_or_create(
            nome="Escritório SP",
            uf="SP",
            defaults={'settings': {'timezone': 'America/Sao_Paulo'}}
        )
        
        # Get or create a user for created_by
        user, created = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@notarius.com',
                'first_name': 'System',
                'last_name': 'User',
                'is_staff': True
            }
        )
        
        # Create procuracao template with improved Portuguese grammar
        procuracao_template, created = Template.objects.get_or_create(
            tenant=tenant,
            name='procuracao',
            document_type='procuracao',
            defaults={
                'corpo_template': '''PROCURAÇÃO

Eu, {{OUTORGANTE}}, brasileiro(a), {{ESTADO_CIVIL_OUTORGANTE}}, portador(a) da Cédula de Identidade RG nº {{PLACEHOLDER_RG}}, CPF nº {{PLACEHOLDER_CPF}}, residente e domiciliado(a) na {{PLACEHOLDER_ENDERECO}}, {{PLACEHOLDER_CIDADE}}, Estado de {{PLACEHOLDER_ESTADO}}.

OUTORGO poderes a {{OUTORGADO}}, brasileiro(a), {{ESTADO_CIVIL_OUTORGADO}}, portador(a) da Cédula de Identidade RG nº {{PLACEHOLDER_RG}}, CPF nº {{PLACEHOLDER_CPF}}, residente e domiciliado(a) na {{PLACEHOLDER_ENDERECO}}, {{PLACEHOLDER_CIDADE}}, Estado de {{PLACEHOLDER_ESTADO}}.

OBJETO: {{OBJETO_PROCURACAO}}

PODERES OUTORGADOS:
1. Firmar contratos de compra e venda, recibos e demais documentos pertinentes;
2. Representar o OUTORGANTE perante cartórios, órgãos públicos e instituições financeiras;
3. Receber valores em nome do OUTORGANTE e dar quitação;
4. Praticar todos os atos necessários ao cumprimento dos poderes outorgados;
5. Constituir advogado para representação judicial, se necessário.

CLÁUSULAS ESPECIAIS:
- O presente instrumento é irrevogável e irretratável;
- O outorgado poderá praticar todos os atos necessários ao cumprimento dos poderes outorgados;
- O outorgado poderá constituir advogado para representação judicial, se necessário;
- O outorgado poderá receber valores em meu nome e dar quitação.

VIGÊNCIA: O presente instrumento terá vigência de {{VIGENCIA}} a contar da data de sua assinatura.

FORO: Fica eleito o foro da comarca de {{FORO}} para dirimir quaisquer dúvidas oriundas do presente instrumento.

{{CIDADE}}, {{DATA_ATUAL}}.

_________________________________
{{OUTORGANTE}}
RG: {{PLACEHOLDER_RG}}
CPF: {{PLACEHOLDER_CPF}}

_________________________________
{{OUTORGADO}}
RG: {{PLACEHOLDER_RG}}
CPF: {{PLACEHOLDER_CPF}}''',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'OUTORGANTE': {'type': 'string', 'description': 'Nome do outorgante'},
                        'OUTORGADO': {'type': 'string', 'description': 'Nome do outorgado'},
                        'ESTADO_CIVIL_OUTORGANTE': {'type': 'string', 'description': 'Estado civil do outorgante'},
                        'ESTADO_CIVIL_OUTORGADO': {'type': 'string', 'description': 'Estado civil do outorgado'},
                        'OBJETO_PROCURACAO': {'type': 'string', 'description': 'Objeto da procuração'},
                        'VIGENCIA': {'type': 'string', 'description': 'Vigência do documento'},
                        'FORO': {'type': 'string', 'description': 'Foro competente'},
                        'CIDADE': {'type': 'string', 'description': 'Cidade do documento'},
                        'DATA_ATUAL': {'type': 'string', 'description': 'Data atual'},
                        'PLACEHOLDER_RG': {'type': 'string', 'description': 'Número do RG'},
                        'PLACEHOLDER_CPF': {'type': 'string', 'description': 'Número do CPF'},
                        'PLACEHOLDER_ENDERECO': {'type': 'string', 'description': 'Endereço'},
                        'PLACEHOLDER_CIDADE': {'type': 'string', 'description': 'Cidade'},
                        'PLACEHOLDER_ESTADO': {'type': 'string', 'description': 'Estado'}
                    },
                    'required': ['OUTORGANTE', 'OUTORGADO', 'OBJETO_PROCURACAO']
                },
                'description': 'Template para geração de procurações com gramática portuguesa corrigida',
                'is_active': True,
                'created_by': user
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created procuracao template: {procuracao_template.name}')
            )
        else:
            self.stdout.write(f'Procuracao template already exists: {procuracao_template.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                'Default content templates created successfully!'
            )
        )
