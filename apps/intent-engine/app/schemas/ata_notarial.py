"""
Schema for Ata Notarial de Constatação.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AtaNotarialConstatacaoSchema(BaseModel):
    """Schema for Ata Notarial de Constatação."""
    objeto: Optional[str] = Field(None, description="Object of constatation (e.g., 'conteudo_web')")
    perfil: Optional[str] = Field(None, description="Social media profile (e.g., '@lojax')")
    data_observacao: Optional[datetime] = Field(None, description="Observation date and time")
    urls: Optional[list] = Field(default_factory=list, description="List of URLs")
    prints: Optional[bool] = Field(False, description="Whether prints/screenshots are included")

