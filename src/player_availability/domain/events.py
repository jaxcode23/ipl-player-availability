from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from .enums import ConfidenceLevel, EventType


class AvailabilityEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    event_type: EventType
    description: str | None = None
    source_name: str
    source_url: str | None = None
    confidence: ConfidenceLevel
    event_date: date
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EventCreate(BaseModel):
    player_id: int
    event_type: EventType
    description: str | None = None
    source_name: str
    source_url: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    event_date: date
    start_date: date | None = None
    end_date: date | None = None


class PlayerStatus(BaseModel):
    player_id: int
    player_name: str
    team_name: str
    status: str
    reason: str | None = None
    since: date | None = None
    expected_return: date | None = None
