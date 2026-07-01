from dataclasses import dataclass
from datetime import date

from ..domain.enums import AvailabilityStatus, ConfidenceLevel, EventType


@dataclass
class NormalizedRecord:
    player_name: str
    event_type: EventType
    availability_status: AvailabilityStatus
    confidence: ConfidenceLevel
    source_name: str
    source_url: str | None
    published_at: date
    effective_date: date | None
    team_name: str | None
    injury_type: str | None
    replaced_player_name: str | None
    replacement_player_name: str | None
    title: str
    body: str
