from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass
class RawData:
    source_name: str
    title: str
    content: str
    url: str
    published_at: datetime | None = None
    fetched_at: datetime = field(default_factory=_utcnow)
    metadata: dict[str, str] | None = None


class BaseCollector(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    def collect(self) -> list[RawData]: ...
