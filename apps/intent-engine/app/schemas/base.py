"""
Base schemas and validators for form extraction.
"""

import re
from typing import Optional
from pydantic import BaseModel, validator, Field
from datetime import datetime


class CPFModel(BaseModel):
    """CPF model with validation."""
    cpf: Optional[str] = None
    
    @validator('cpf', pre=True, always=True)
    def normalize_cpf(cls, v):
        if not v:
            return None
        # Remove formatting
        v = re.sub(r'[^\d]', '', str(v))
        # Validate length
        if len(v) != 11:
            raise ValueError('CPF must have 11 digits')
        # Format: XXX.XXX.XXX-XX
        return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"


class CNPJModel(BaseModel):
    """CNPJ model with validation."""
    cnpj: Optional[str] = None
    
    @validator('cnpj', pre=True, always=True)
    def normalize_cnpj(cls, v):
        if not v:
            return None
        # Remove formatting
        v = re.sub(r'[^\d]', '', str(v))
        # Validate length
        if len(v) != 14:
            raise ValueError('CNPJ must have 14 digits')
        # Format: XX.XXX.XXX/XXXX-XX
        return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"


class OABModel(BaseModel):
    """OAB registration model with validation."""
    oab: Optional[str] = None
    
    @validator('oab', pre=True, always=True)
    def normalize_oab(cls, v):
        if not v:
            return None
        # Remove formatting
        v = re.sub(r'[^\w]', '', str(v).upper())
        # Format: SP-123456 or SP123456 -> SP-123456
        if re.match(r'^[A-Z]{2}\d+$', v):
            return f"{v[:2]}-{v[2:]}"
        elif re.match(r'^[A-Z]{2}-\d+$', v):
            return v
        raise ValueError('OAB format must be UF-XXXXXX (e.g., SP-123456)')


class PessoaFisicaModel(BaseModel):
    """Person model with PII."""
    nome: Optional[str] = None
    cpf: Optional[str] = None


class PessoaJuridicaModel(BaseModel):
    """Company model."""
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None

