from abc import ABC, abstractmethod

from ..domain.events import EventCreate
from ..parsers.base import ParsedRecord


class BaseNormalizer(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def normalize(self, records: list[ParsedRecord]) -> list[EventCreate]: ...
