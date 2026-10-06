"""
Schema for Protesto de Título.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TituloProtestoModel(BaseModel):
    """Title document for protest."""
    especie: Optional[str] = Field(None, description="Type of title (e.g., 'duplicata')")
    numero: Optional[str] = None
    valor: Optional[float] = None
    vencimento: Optional[datetime] = None


class DevedorModel(BaseModel):
    """Debtor model."""
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None


class ProtestoTituloSchema(BaseModel):
    """Schema for Protesto de Título."""
    titulo: Optional[TituloProtestoModel] = None
    devedor: Optional[DevedorModel] = None
    praca: Optional[str] = Field(None, description="Place of protest (e.g., 'Rio de Janeiro/RJ')")

