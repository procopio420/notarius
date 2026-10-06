"""
Schemas for RTD (Registro de Títulos e Documentos).
"""

from typing import Optional
from pydantic import BaseModel, Field


class LocadorModel(BaseModel):
    """Landlord model."""
    nome: Optional[str] = None
    cpf: Optional[str] = None


class LocatarioModel(BaseModel):
    """Tenant model."""
    nome: Optional[str] = None
    cpf: Optional[str] = None


class ImovelLocacaoModel(BaseModel):
    """Property for rental model."""
    cidade: Optional[str] = None
    uf: Optional[str] = None


class RegistroContratoLocacaoSchema(BaseModel):
    """Schema for Registro de Contrato de Locação."""
    locador: Optional[LocadorModel] = None
    locatario: Optional[LocatarioModel] = None
    prazo_meses: Optional[int] = None
    garantia: Optional[str] = Field(None, description="e.g., 'caucao_3_alugueis'")
    imovel: Optional[ImovelLocacaoModel] = None


class NotificacaoExtrajudicialSchema(BaseModel):
    """Schema for Notificação Extrajudicial."""
    notificante: Optional[str] = Field(None, description="Notifying party")
    notificado: Optional[str] = Field(None, description="Notified party")
    fundamento: Optional[str] = Field(None, description="Legal basis (e.g., 'inadimplemento')")
    prazo: Optional[str] = Field(None, description="Deadline (e.g., '10 dias')")

