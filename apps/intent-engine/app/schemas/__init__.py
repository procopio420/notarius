"""
Pydantic schemas for document form extraction.
"""

from .escritura_compra_venda import EscrituraCompraVendaSchema
from .procuracao_ad_judicia import ProcuracaoAdJudiciaSchema
from .procuracao_veiculo import ProcuracaoVeiculoSchema
from .ata_notarial import AtaNotarialConstatacaoSchema
from .rcpn import AssentoNascimentoSchema, AverbacaoDivorcioSchema
from .registro_imoveis import (
    RegistroCompraVendaRISchema,
    AverbacaoConstrucaoSchema,
    CertidaoOnusReaisSchema
)
from .rtd import (
    RegistroContratoLocacaoSchema,
    NotificacaoExtrajudicialSchema
)
from .protesto import ProtestoTituloSchema

__all__ = [
    "EscrituraCompraVendaSchema",
    "ProcuracaoAdJudiciaSchema",
    "ProcuracaoVeiculoSchema",
    "AtaNotarialConstatacaoSchema",
    "AssentoNascimentoSchema",
    "AverbacaoDivorcioSchema",
    "RegistroCompraVendaRISchema",
    "AverbacaoConstrucaoSchema",
    "CertidaoOnusReaisSchema",
    "RegistroContratoLocacaoSchema",
    "NotificacaoExtrajudicialSchema",
    "ProtestoTituloSchema",
]

