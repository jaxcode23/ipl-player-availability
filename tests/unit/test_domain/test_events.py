from datetime import date, datetime

from player_availability.domain.enums import ConfidenceLevel, EventType
from player_availability.domain.events import (
    AvailabilityEvent,
    EventCreate,
    PlayerStatus,
)


class TestEventCreate:
    def test_defaults(self) -> None:
        event = EventCreate(
            player_id=1,
            event_type=EventType.INJURY,
            source_name="manual",
            event_date=date(2026, 4, 1),
        )
        assert event.confidence == ConfidenceLevel.MEDIUM
        assert event.description is None
        assert event.source_url is None
        assert event.start_date is None
        assert event.end_date is None

    def test_full_construction(self) -> None:
        event = EventCreate(
            player_id=1,
            event_type=EventType.INJURY,
            description="Hamstring strain",
            source_name="espn_cricinfo",
            source_url="https://example.com/article",
            confidence=ConfidenceLevel.HIGH,
            event_date=date(2026, 4, 1),
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 15),
        )
        assert event.description == "Hamstring strain"
        assert event.end_date == date(2026, 4, 15)


class TestAvailabilityEvent:
    def test_from_attributes(self) -> None:
        event = AvailabilityEvent(
            id=1,
            player_id=1,
            event_type=EventType.INJURY,
            source_name="manual",
            confidence=ConfidenceLevel.CONFIRMED,
            event_date=date(2026, 4, 1),
            is_active=True,
            created_at=datetime(2026, 4, 1, 12, 0, 0),
            updated_at=datetime(2026, 4, 1, 12, 0, 0),
        )
        assert isinstance(event, AvailabilityEvent)
        assert event.event_type == EventType.INJURY


class TestPlayerStatus:
    def test_unavailable(self) -> None:
        status = PlayerStatus(
            player_id=1,
            player_name="MS Dhoni",
            team_name="CSK",
            status="unavailable",
            reason="Knee strain",
            since=date(2026, 4, 1),
            expected_return=date(2026, 4, 15),
        )
        assert status.status == "unavailable"
        assert status.expected_return == date(2026, 4, 15)

    def test_available(self) -> None:
        status = PlayerStatus(
            player_id=2,
            player_name="Virat Kohli",
            team_name="RCB",
            status="available",
        )
        assert status.reason is None
        assert status.since is None
        assert status.expected_return is None
