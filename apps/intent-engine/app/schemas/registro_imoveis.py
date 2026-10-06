"""
Schemas for Registro de Imóveis (RI).
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TituloModel(BaseModel):
    """Title document model."""
    tipo: Optional[str] = Field(None, description="Type of title (e.g., 'escritura_publica')")
    tabelionato: Optional[str] = None  # e.g., "5º Tabelionato de Notas"
    data: Optional[datetime] = None


class PartesRIModel(BaseModel):
    """Parties for RI registration."""
    vendedor: Optional[dict] = None  # Can be PessoaFisica or PessoaJuridica
    comprador: Optional[dict] = None


class RegistroCompraVendaRISchema(BaseModel):
    """Schema for Registro de Compra e Venda RI."""
    matricula: Optional[str] = None
    oficio: Optional[str] = Field(None, description="e.g., '1º RI São Paulo/SP'")
    titulo: Optional[TituloModel] = None
    partes: Optional[PartesRIModel] = None


class AverbacaoConstrucaoSchema(BaseModel):
    """Schema for Averbação de Construção."""
    matricula: Optional[str] = None
    ri: Optional[str] = Field(None, description="e.g., '2º RI Niterói/RJ'")
    conclusao: Optional[datetime] = None
    area_m2: Optional[float] = None
    habite_se: Optional[bool] = Field(None, description="Whether habite-se is attached")


class CertidaoOnusReaisSchema(BaseModel):
    """Schema for Certidão de Ônus Reais."""
    matricula: Optional[str] = None
    ri: Optional[str] = Field(None, description="e.g., '3º RI Porto Alegre/RS'")

