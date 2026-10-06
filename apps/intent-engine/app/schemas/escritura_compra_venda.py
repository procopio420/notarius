"""
Schema for Escritura de Compra e Venda.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class VendedorModel(BaseModel):
    """Vendedor (seller) model."""
    nome: Optional[str] = None
    cpf: Optional[str] = None
    cnpj: Optional[str] = None


class CompradorModel(BaseModel):
    """Comprador (buyer) model."""
    nome: Optional[str] = None
    cpf: Optional[str] = None
    cnpj: Optional[str] = None


class ImovelModel(BaseModel):
    """Real estate property model."""
    matricula: Optional[str] = None
    ri: Optional[str] = None  # e.g., "2º RI Curitiba/PR"


class FinanceiroModel(BaseModel):
    """Financial information model."""
    preco: Optional[float] = None
    moeda: str = Field(default="BRL", description="Currency code")
    condicao: Optional[str] = None  # "avista", "parcelado", etc.


class EscrituraCompraVendaSchema(BaseModel):
    """Schema for Escritura de Compra e Venda."""
    vendedor: Optional[VendedorModel] = None
    comprador: Optional[CompradorModel] = None
    imovel: Optional[ImovelModel] = None
    financeiro: Optional[FinanceiroModel] = None

