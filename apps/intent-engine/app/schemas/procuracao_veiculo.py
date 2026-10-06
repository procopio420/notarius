"""
Schema for Procuração para Veículo.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ProprietarioModel(BaseModel):
    """Vehicle owner model."""
    nome: Optional[str] = None
    cpf: Optional[str] = None


class ProcuradorVeiculoModel(BaseModel):
    """Attorney for vehicle model."""
    nome: Optional[str] = None
    cpf: Optional[str] = None


class VeiculoModel(BaseModel):
    """Vehicle model."""
    descricao: Optional[str] = None  # e.g., "Honda Civic 2018"
    placa: Optional[str] = None


class ProcuracaoVeiculoSchema(BaseModel):
    """Schema for Procuração para Veículo."""
    proprietario: Optional[ProprietarioModel] = None
    procurador: Optional[ProcuradorVeiculoModel] = None
    veiculo: Optional[VeiculoModel] = None
    validade_dias: Optional[int] = Field(None, description="Validity period in days")

