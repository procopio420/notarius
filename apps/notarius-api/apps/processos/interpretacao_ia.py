"""Local deterministic simulation. No provider client or network access."""
from .conferencia import extrair_rotulos
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum
from .ficha import CAMPOS

CampoProposta = Enum('CampoProposta', {key: key for key in CAMPOS}, type=str)

# Retained for the existing offline evaluation harness.
class Proposta(BaseModel):
    model_config = ConfigDict(extra='forbid')
    campo: CampoProposta
    valor: str = Field(min_length=1, max_length=2000)
    trecho: str = Field(min_length=1, max_length=4000)

class Interpretacao(BaseModel):
    model_config = ConfigDict(extra='forbid')
    propostas: list[Proposta] = Field(max_length=20)
    duvidas: list[str] = Field(max_length=20)

PROMPT = 'SIMULAÇÃO LOCAL: copiar campos explicitamente rotulados; encaminhar demais linhas à revisão humana. Não é IA.'

class AnaliseIndisponivel(Exception):
    pass

def analisar_mensagem(text):
    if not text.strip() or len(text) > 10000:
        raise AnaliseIndisponivel('Mensagem fora do limite de análise.')
    proposals, doubts = [], []
    for line in text.splitlines():
        if not line.strip():
            continue
        matches = list(extrair_rotulos(line))
        if matches:
            key, value, excerpt = matches[0]
            proposals.append({'campo': key, 'valor': value, 'trecho': excerpt})
        else:
            doubts.append(line)
    return {'propostas': proposals, 'duvidas': doubts}
