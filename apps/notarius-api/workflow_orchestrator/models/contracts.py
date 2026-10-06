"""
Pydantic data contracts for workflow orchestrator.
"""

from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Parte(BaseModel):
    """Party involved in the document."""
    
    nome: Optional[str] = None
    cpf_cnpj: Optional[str] = Field(None, description="Never persist without hash")
    papel: Literal[
        "outorgante",
        "outorgado",
        "comprador",
        "vendedor",
        "procurador",
        "genitor",
        "devedor",
        "credor",
        "declarante",
        "oficial",
        "advogado",
        "testador",
        "locador",
        "locatario",
        "proprietario",
        "outros"
    ]


class DocumentoBasico(BaseModel):
    """Basic document information."""
    
    tipo_documento: str = Field(..., description="Slug: escritura_compra_venda, procuracao_ad_judicia, etc.")
    especialidade: Literal[
        "tabelionato_notas",
        "rcpn",
        "registro_imoveis",
        "rtd",
        "rcpj",
        "protesto"
    ]
    uf: str = Field(..., description="State code: SP, RJ, etc.")
    municipio: Optional[str] = None
    partes: List[Parte] = Field(default_factory=list)


class WorkflowInput(BaseModel):
    """Input for workflow orchestration."""
    
    doc: DocumentoBasico
    canais_disponiveis: List[str] = Field(
        default_factory=lambda: ["online", "presencial"],
        description="Available channels: online, presencial"
    )
    assinatura_disponivel: List[str] = Field(
        default_factory=lambda: ["icp_brasil", "e-notariado", "manual"],
        description="Available signature types"
    )
    anexos: List[str] = Field(default_factory=list, description="Attachments: habite_se, itbi, dnv, etc.")
    preferencia_online: bool = True


class Destino(BaseModel):
    """Routing destination for the document."""
    
    autoridade: str = Field(..., description="Authority: Tabelionato de Notas, 1º RI São Paulo/SP, etc.")
    plataforma: Optional[str] = Field(None, description="Platform: e-notariado, registrodeimoveis.org.br, etc.")
    modo: Literal["online", "presencial", "hibrido"]


class Assinatura(BaseModel):
    """Signature requirements."""
    
    quem_assina: List[str] = Field(..., description="Roles that must sign: vendedor, comprador, tabeliao, etc.")
    tipo: Literal["icp_brasil", "e-notariado", "manual"]
    videoconferencia: bool = False


class WorkflowPlan(BaseModel):
    """Complete workflow plan for a document."""
    
    roteamento: Destino
    assinatura: Assinatura
    protocolo: Dict[str, Any] = Field(default_factory=dict, description="Protocol instructions by channel")
    checklist: List[str] = Field(default_factory=list)
    citacoes: List[str] = Field(default_factory=list, description="Legal citations: Lei 6.015/73, CC/2002, etc.")
    bloqueantes: List[str] = Field(default_factory=list, description="Blocking issues that prevent proceeding")
    alerta: List[str] = Field(default_factory=list, description="Warnings that don't block but recommend attention")
    fees_hint: List[str] = Field(default_factory=list, description="Fee hints: ITBI, Emolumentos RI, etc.")
    cache_key: str = Field(..., description="Stable hash (without raw PII)")


class RulePackSummary(BaseModel):
    """Summary of a rulepack."""
    
    uf: Optional[str] = None
    especialidade: Optional[str] = None
    document_types: List[str] = Field(default_factory=list)
    rules_count: int = 0

