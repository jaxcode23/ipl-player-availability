from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from ..collectors.base import RawData
from ..domain.enums import AvailabilityStatus, ConfidenceLevel, EventType

_PARSER_VERSION = "1.0.0"


@dataclass
class ParsedRecord:
    source_name: str
    title: str
    body: str
    url: str
    published_at: date
    player_name: str | None = None
    replacement_player: str | None = None
    team_name: str | None = None
    event_type: EventType | None = None
    availability_status: AvailabilityStatus | None = None
    injury_type: str | None = None
    effective_date: date | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    parser_version: str = _PARSER_VERSION


class BaseParser(ABC):
    @property
    @abstractmethod
    def supported_source(self) -> str: ...

    def can_handle(self, source_name: str) -> bool:
        return source_name == self.supported_source

    @abstractmethod
    def parse(self, raw_data: RawData) -> list[ParsedRecord]: ...
