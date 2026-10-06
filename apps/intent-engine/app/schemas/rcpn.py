"""
Schemas for RCPN (Registro Civil de Pessoas Naturais).
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class GenitorModel(BaseModel):
    """Genitor (parent) model."""
    parentesco: str = Field(..., description="Relationship: 'mae' or 'pai'")
    nome: Optional[str] = None
    cpf: Optional[str] = None


class NascidoModel(BaseModel):
    """Nascido (newborn) model."""
    nome: Optional[str] = None
    data_nascimento: Optional[datetime] = None
    local: Optional[str] = None  # e.g., "Barra Mansa/RJ"


class AssentoNascimentoSchema(BaseModel):
    """Schema for Assento de Nascimento."""
    nascido: Optional[NascidoModel] = None
    genitores: Optional[List[GenitorModel]] = Field(default_factory=list)


class CasalModel(BaseModel):
    """Couple model for divorce."""
    conjuge_1: Optional[str] = None
    conjuge_2: Optional[str] = None


class EfeitosNomeModel(BaseModel):
    """Name effects model for divorce."""
    renomeacao: Optional[str] = Field(None, description="New name after divorce")


class AverbacaoDivorcioSchema(BaseModel):
    """Schema for Averbação de Divórcio."""
    casal: Optional[CasalModel] = None
    transito_em_julgado: Optional[datetime] = None
    efeitos_nome: Optional[EfeitosNomeModel] = None

