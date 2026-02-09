# ======================================================================
# HVAC/hydronics_v3/catalogues/valve_catalogue.py
# ======================================================================

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable


class ValveCandidate:
    def __init__(self, ref: str, kv: float):
        self.ref = ref
        self.kv = kv


class ValveCatalogue(ABC):
    """
    Abstract valve catalogue.
    """

    @abstractmethod
    def candidates(self) -> Iterable[ValveCandidate]:
        ...
