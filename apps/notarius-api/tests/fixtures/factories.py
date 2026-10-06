"""
Factory Boy factories for creating test data.
"""
import factory
import factory.fuzzy
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker

from apps.tenancy.models import Tenant
from apps.processos.models import Processo
from apps.partes.models import Parte
from apps.documentos.models import Documento, Minuta
from apps.templates.models import DocumentTemplate

User = get_user_model()
fake = Faker('pt_BR')


class TenantFactory(factory.django.DjangoModelFactory):
    """Factory for creating Tenant instances."""
    
    class Meta:
        model = Tenant
    
    nome = factory.Sequence(lambda n: f"Cartório {n}")
    uf = factory.fuzzy.FuzzyChoice(['RJ', 'SP', 'MG', 'RS', 'PR'])
    settings = factory.LazyFunction(lambda: {
        'cnpj': fake.cnpj(),
        'endereco': fake.address(),
        'telefone': fake.phone_number(),
        'email': fake.email()
    })


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyFunction(lambda: fake.email())
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    is_active = True
    is_staff = False
    is_superuser = False


class ProcessoFactory(factory.django.DjangoModelFactory):
    """Factory for creating Processo instances."""
    
    class Meta:
        model = Processo

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # `created_by` was used in legacy tests; ignore if provided.
        kwargs.pop("created_by", None)
        return super()._create(model_class, *args, **kwargs)
    
    tenant = factory.SubFactory(TenantFactory)
    tipo_ato = factory.fuzzy.FuzzyChoice([
        'compra_e_venda', 'procuracao', 'testamento', 'escritura', 'contrato'
    ])
    status = factory.fuzzy.FuzzyChoice(['rascunho', 'analise', 'assinatura', 'selagem', 'arquivado', 'cancelado'])
    responsavel = factory.SubFactory(UserFactory)
    metadados = factory.LazyFunction(lambda: {})


class ParteFactory(factory.django.DjangoModelFactory):
    """Factory for creating Parte instances with mock PII tokens."""
    
    class Meta:
        model = Parte
    
    tenant = factory.SubFactory(TenantFactory)
    tipo = factory.fuzzy.FuzzyChoice(['pf', 'pj'])
    tipo_pessoa = factory.SelfAttribute('tipo')
    nome_token = factory.LazyFunction(lambda: f"token_{fake.uuid4()}")
    nome_hash = factory.LazyFunction(lambda: fake.binary(length=32))
    cpf_token = factory.LazyFunction(lambda: f"cpf_token_{fake.uuid4()}")
    cpf_hash = factory.LazyFunction(lambda: fake.binary(length=32))
    cnpj_token = factory.LazyFunction(lambda: f"cnpj_token_{fake.uuid4()}")
    cnpj_hash = factory.LazyFunction(lambda: fake.binary(length=32))
    endereco_token = factory.LazyFunction(lambda: f"endereco_token_{fake.uuid4()}")
    email_token = factory.LazyFunction(lambda: f"email_token_{fake.uuid4()}")
    telefone_token = factory.LazyFunction(lambda: f"telefone_token_{fake.uuid4()}")
    created_by = factory.SubFactory(UserFactory)


class DocumentTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for creating DocumentTemplate instances."""
    
    class Meta:
        model = DocumentTemplate
    
    tenant = factory.SubFactory(TenantFactory)
    name = factory.fuzzy.FuzzyChoice(['procuracao', 'certidao', 'testamento', 'escritura', 'contrato'])
    document_type = factory.SelfAttribute('name')
    template_path = factory.LazyAttribute(lambda obj: f"documentos/{obj.document_type}.html")
    is_default = True
    is_active = True
    version = "1.0"
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    created_by = factory.SubFactory(UserFactory)


class MinutaFactory(factory.django.DjangoModelFactory):
    """Factory for creating Minuta instances."""
    
    class Meta:
        model = Minuta
    
    tenant = factory.SubFactory(TenantFactory)
    processo = factory.SubFactory(ProcessoFactory)
    corpo_md = factory.LazyFunction(lambda: fake.text(max_nb_chars=1000))
    variaveis_json = factory.LazyFunction(lambda: {
        "nome_outorgante": f"token_{fake.uuid4()}",
        "nome_outorgado": f"token_{fake.uuid4()}",
        "endereco": f"token_{fake.uuid4()}"
    })
    status = factory.fuzzy.FuzzyChoice(['rascunho', 'aprovado', 'rejeitado', 'finalizado'])
    versao = factory.Sequence(lambda n: n + 1)
    gerada_por = factory.fuzzy.FuzzyChoice(['usuario', 'ai'])
    citations = factory.LazyFunction(lambda: [
        {"source": "Lei 8.935/1994", "article": "Art. 1º"},
        {"source": "Código Civil", "article": "Art. 1.123"}
    ])
    grounding_confidence = factory.fuzzy.FuzzyFloat(0.7, 0.95)
    created_by = factory.SubFactory(UserFactory)


class DocumentoFactory(factory.django.DjangoModelFactory):
    """Factory for creating Documento instances."""
    
    class Meta:
        model = Documento
    
    tenant = factory.SubFactory(TenantFactory)
    processo = factory.SubFactory(ProcessoFactory)
    s3_key = factory.LazyFunction(lambda: f"documents/{fake.uuid4()}.pdf")
    hash_sha256 = factory.LazyFunction(lambda: fake.binary(length=32))
    mime = "application/pdf"
    pages = factory.fuzzy.FuzzyInteger(1, 10)
    status = factory.fuzzy.FuzzyChoice(['novo', 'processando', 'pronto', 'erro'])


# Specialized factories for specific test scenarios
class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""
    is_staff = True
    is_superuser = True


class InactiveUserFactory(UserFactory):
    """Factory for creating inactive users."""
    is_active = False


class ProcessoWithMinutasFactory(ProcessoFactory):
    """Factory for creating Processo with related Minutas."""
    minutas = factory.RelatedFactoryList(
        MinutaFactory,
        factory_related_name='processo',
        size=3
    )


class MinutaRascunhoFactory(MinutaFactory):
    """Factory for creating Minuta in rascunho status."""
    status = 'rascunho'


class MinutaAprovadoFactory(MinutaFactory):
    """Factory for creating Minuta in aprovado status."""
    status = 'aprovado'
    approved_by = factory.SubFactory(UserFactory)
    approved_at = factory.LazyFunction(timezone.now)


class MinutaFinalizadoFactory(MinutaFactory):
    """Factory for creating Minuta in finalizado status."""
    status = 'finalizado'
    approved_by = factory.SubFactory(UserFactory)
    approved_at = factory.LazyFunction(timezone.now)
    finalized_at = factory.LazyFunction(timezone.now)


class PartePessoaFisicaFactory(ParteFactory):
    """Factory for creating Parte with pessoa física."""
    tipo = 'pf'
    tipo_pessoa = 'pf'
    cnpj_token = None
    cnpj_hash = None


class PartePessoaJuridicaFactory(ParteFactory):
    """Factory for creating Parte with pessoa jurídica."""
    tipo = 'pj'
    tipo_pessoa = 'pj'
    cpf_token = None
    cpf_hash = None
