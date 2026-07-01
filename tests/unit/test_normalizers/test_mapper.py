from datetime import date

import pytest

from player_availability.domain.enums import AvailabilityStatus, ConfidenceLevel, EventType
from player_availability.normalizers.exceptions import UnresolvedPlayerError
from player_availability.normalizers.mapper import normalized_to_event_create
from player_availability.normalizers.models import NormalizedRecord
from player_availability.normalizers.resolver import DictPlayerResolver


class TestNormalizedToEventCreate:
    def _make_record(self, **overrides: object) -> NormalizedRecord:
        defaults: dict[str, object] = {
            "player_name": "Virat Kohli",
            "event_type": EventType.INJURY,
            "availability_status": AvailabilityStatus.UNAVAILABLE,
            "confidence": ConfidenceLevel.HIGH,
            "source_name": "ipl_official",
            "source_url": "https://example.com",
            "published_at": date(2026, 4, 1),
            "effective_date": date(2026, 4, 1),
            "team_name": "Royal Challengers Bengaluru",
            "injury_type": "Knee Injury",
            "replaced_player_name": None,
            "replacement_player_name": None,
            "title": "Test",
            "body": "Test body",
        }
        defaults.update(overrides)
        return NormalizedRecord(**defaults)

    def test_returns_event_create(self) -> None:
        resolver = DictPlayerResolver({"virat kohli": 1})
        record = self._make_record()
        event = normalized_to_event_create(record, resolver)
        assert event.player_id == 1
        assert event.event_type == EventType.INJURY
        assert event.confidence == ConfidenceLevel.HIGH
        assert event.event_date == date(2026, 4, 1)
        assert event.start_date == date(2026, 4, 1)

    def test_description_includes_injury(self) -> None:
        resolver = DictPlayerResolver({"virat kohli": 1})
        record = self._make_record()
        event = normalized_to_event_create(record, resolver)
        assert "Injury: Knee Injury" in event.description
        assert "Team: Royal Challengers Bengaluru" in event.description

    def test_description_includes_replaced_player(self) -> None:
        resolver = DictPlayerResolver({"urvil patel": 42})
        record = self._make_record(
            player_name="Urvil Patel",
            team_name="Chennai Super Kings",
            injury_type=None,
            replaced_player_name="MS Dhoni",
        )
        event = normalized_to_event_create(record, resolver)
        assert "Replacement for MS Dhoni" in event.description

    def test_description_includes_replacement_player(self) -> None:
        resolver = DictPlayerResolver({"ms dhoni": 7})
        record = self._make_record(
            player_name="MS Dhoni",
            team_name="Chennai Super Kings",
            injury_type="Knee Injury",
            replacement_player_name="Urvil Patel",
        )
        event = normalized_to_event_create(record, resolver)
        assert "Replacement: Urvil Patel" in event.description

    def test_description_none_when_no_extra_info(self) -> None:
        resolver = DictPlayerResolver({"virat kohli": 1})
        record = self._make_record(
            injury_type=None,
            replaced_player_name=None,
            replacement_player_name=None,
            team_name=None,
        )
        event = normalized_to_event_create(record, resolver)
        assert event.description is None

    def test_unresolved_player_raises(self) -> None:
        resolver = DictPlayerResolver({})
        record = self._make_record()
        with pytest.raises(UnresolvedPlayerError, match="Could not resolve player"):
            normalized_to_event_create(record, resolver)

    def test_event_date_falls_back_to_published_at(self) -> None:
        resolver = DictPlayerResolver({"virat kohli": 1})
        record = self._make_record(effective_date=None)
        event = normalized_to_event_create(record, resolver)
        assert event.event_date == date(2026, 4, 1)

    def test_source_fields_mapped(self) -> None:
        resolver = DictPlayerResolver({"virat kohli": 1})
        record = self._make_record()
        event = normalized_to_event_create(record, resolver)
        assert event.source_name == "ipl_official"
        assert event.source_url == "https://example.com"
