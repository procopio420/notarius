"""
Schema for Procuração Ad Judicia.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class OutorganteModel(BaseModel):
    """Outorgante (grantor) model."""
    nome: Optional[str] = None
    cpf: Optional[str] = None


class ProcuradorModel(BaseModel):
    """Procurador (attorney) model."""
    nome: Optional[str] = None
    oab: Optional[str] = None


class ProcuracaoAdJudiciaSchema(BaseModel):
    """Schema for Procuração Ad Judicia."""
    outorgante: Optional[OutorganteModel] = None
    procurador: Optional[ProcuradorModel] = None
    poderes: Optional[List[str]] = Field(default_factory=list, description="List of granted powers")

