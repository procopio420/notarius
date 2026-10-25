"""Versioned, closed contracts. Text and returned values are untrusted data."""
from typing import Annotated, Literal
from .politica_documental import LIMITES
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Id = Annotated[str, StringConstraints(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')]
Texto = Annotated[str, StringConstraints(min_length=1, max_length=4000)]


class Contrato(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class DocumentoPedido(Contrato):
    documento_id: Id
    leitura_versao: int = Field(ge=1)
    organizacao_versao: int = Field(ge=1)


class PedidoAnalise(Contrato):
    client_id: Id
    documentos: list[DocumentoPedido] = Field(min_length=1, max_length=LIMITES.documentos)


class Fonte(Contrato):
    documento_id: Id
    pagina_id: Id
    pagina: int = Field(ge=1)
    leitura_versao: int = Field(ge=1)
    organizacao_versao: int = Field(ge=1)
    canal: Literal['texto', 'ocr']


class UnidadeEntrada(Contrato):
    unidade_id: str = Field(min_length=1, max_length=90)
    fonte: Fonte
    linha: int = Field(ge=1)
    texto: str = Field(max_length=4000)
    leitura_incerta: bool
    limites: list[str] = Field(max_length=20)
    instrucao_suspeita: bool
    destinatarios: list[Id | None] = Field(max_length=100)


class RegistroEntrada(Contrato):
    id: Id
    tipo: str = Field(min_length=1, max_length=20)
    pessoa_a_id: Id | None
    pessoa_b_id: Id | None
    imovel_id: Id | None


class CampoEntrada(Contrato):
    tipo: str = Field(min_length=1, max_length=20)
    chave: str = Field(min_length=1, max_length=40)
    rotulo: str = Field(min_length=1, max_length=120)
    opcoes: list[Annotated[str, StringConstraints(min_length=1, max_length=120)]] | None


class EntradaDocumental(Contrato):
    contrato: Literal['documental_v1']
    atendimento_id: Id
    contexto_assinatura: str = Field(pattern=r'^[0-9a-f]{64}$')
    unidades: list[UnidadeEntrada] = Field(min_length=1, max_length=LIMITES.unidades)
    registros: list[RegistroEntrada] = Field(max_length=LIMITES.unidades)
    campos: list[CampoEntrada] = Field(max_length=500)


class PropostaDocumental(Contrato):
    fonte: Fonte
    trecho: Texto
    inicio: int = Field(ge=0)
    fim: int = Field(ge=1)
    valor: Texto
    tipo_registro: str = Field(min_length=1, max_length=20)
    campo: str = Field(min_length=1, max_length=40)
    registro_sugerido_id: Id | None
    relacionado_id: Id | None
    associacao: Literal['sugerida', 'incerta']


class UnidadeSaida(Contrato):
    unidade_id: str = Field(min_length=1, max_length=90)
    situacao: Literal['propostas', 'revisao_manual']
    propostas: list[PropostaDocumental] = Field(max_length=10)
    duvidas: list[Annotated[str, StringConstraints(min_length=1, max_length=2000)]] = Field(max_length=10)


class SaidaDocumental(Contrato):
    contrato: Literal['documental_v1']
    contexto_assinatura: str = Field(pattern=r'^[0-9a-f]{64}$')
    unidades: list[UnidadeSaida] = Field(min_length=1, max_length=LIMITES.unidades)
