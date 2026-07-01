from abc import ABC, abstractmethod

from ..parsers.base import ParsedRecord
from .models import NormalizedRecord


class BaseNormalizer(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def normalize(self, records: list[ParsedRecord]) -> list[NormalizedRecord]: ...
