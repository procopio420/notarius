"""
Enums for core domain models.
"""

from enum import Enum


class ActType(str, Enum):
    """Types of notarial acts."""
    PROCURACAO = "procuracao"
    ESCRITURA = "escritura"
    AUTENTICACAO = "autenticacao"
    RECONHECIMENTO = "reconhecimento"
    TESTAMENTO = "testamento"
    CONTRATO = "contrato"
    OUTRO = "outro"


class PartyRole(str, Enum):
    """Roles of parties in notarial acts."""
    OUTORGANTE = "outorgante"
    OUTORGADO = "outorgado"
    TESTEMUNHA = "testemunha"
    INTERVENIENTE = "interveniente"
    TABELIAO = "tabeliao"
    ESCREVENTE = "escrevente"
    OUTRO = "outro"


class DocumentStatus(str, Enum):
    """Status of documents in the workflow."""
    RASCUNHO = "rascunho"
    PROCESSANDO = "processando"
    PRONTO = "pronto"
    APROVADO = "aprovado"
    FINALIZADO = "finalizado"
    ERRO = "erro"
    CANCELADO = "cancelado"


class Jurisdiction(str, Enum):
    """Brazilian jurisdictions."""
    FEDERAL = "federal"
    SP = "SP"
    RJ = "RJ"
    MG = "MG"
    RS = "RS"
    PR = "PR"
    SC = "SC"
    BA = "BA"
    GO = "GO"
    PE = "PE"
    CE = "CE"
    PA = "PA"
    MA = "MA"
    AM = "AM"
    MT = "MT"
    MS = "MS"
    AL = "AL"
    PB = "PB"
    RN = "RN"
    SE = "SE"
    RO = "RO"
    AC = "AC"
    AP = "AP"
    RR = "RR"
    TO = "TO"
    DF = "DF"


class PIIEntityType(str, Enum):
    """Types of PII entities."""
    CPF = "cpf"
    CNPJ = "cnpj"
    NAME = "name"
    ADDRESS = "address"
    PHONE = "phone"
    EMAIL = "email"
    RG = "rg"
    PASSPORT = "passport"
    BIRTH_DATE = "birth_date"


class AuditAction(str, Enum):
    """Actions that can be audited."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    DOWNLOAD = "download"
    SEAL = "seal"
    SIGN = "sign"
    TOKENIZE = "tokenize"
    DETOKENIZE = "detokenize"
    APPROVE = "approve"
    REJECT = "reject"
    FINALIZE = "finalize"


class LLMProvider(str, Enum):
    """LLM providers for routing."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    LOCAL_LLAMA = "local_llama"
    ANTHROPIC = "anthropic"


class KMSProvider(str, Enum):
    """KMS providers for encryption."""
    LOCAL = "local"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class CacheStrategy(str, Enum):
    """Cache strategies for different data types."""
    SKELETON = "skeleton"  # Legal skeleton (no PII)
    EMBEDDING = "embedding"  # Vector embeddings
    TEMPLATE = "template"  # Jinja2 templates
    CITATION = "citation"  # Legal citations
