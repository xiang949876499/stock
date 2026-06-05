"""研究层"""

from .factors.base import Factor, FactorRegistry, create_default_registry, BuiltinFactors
from .signals.generator import SignalGenerator, Signal, SignalStatus, SignalSource
from .service import ResearchService

__all__ = [
    "Factor",
    "FactorRegistry",
    "create_default_registry",
    "BuiltinFactors",
    "SignalGenerator",
    "Signal",
    "SignalStatus",
    "SignalSource",
    "ResearchService",
]
