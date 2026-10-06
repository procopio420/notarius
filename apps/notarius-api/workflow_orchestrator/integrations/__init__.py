"""Integration stubs for digital platforms."""

from .enotariado import ENotariadoClient
from .ri_central import RICentralClient
from .rtdpj_central import RTDPJCentralClient
from .protesto_central import ProtestoCentralClient

__all__ = [
    "ENotariadoClient",
    "RICentralClient",
    "RTDPJCentralClient",
    "ProtestoCentralClient",
]

