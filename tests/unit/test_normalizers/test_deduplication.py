from datetime import date

from player_availability.domain.enums import AvailabilityStatus, ConfidenceLevel, EventType
from player_availability.normalizers.deduplication import Deduplicator
from player_availability.normalizers.models import NormalizedRecord


class TestDeduplicator:
    def _make(self, **overrides: object) -> NormalizedRecord:
        defaults: dict[str, object] = {
            "player_name": "Virat Kohli",
            "event_type": EventType.INJURY,
            "availability_status": AvailabilityStatus.UNAVAILABLE,
            "confidence": ConfidenceLevel.MEDIUM,
            "source_name": "ipl_official",
            "source_url": "https://example.com",
            "published_at": date(2026, 4, 1),
            "effective_date": date(2026, 4, 1),
            "team_name": None,
            "injury_type": None,
            "replaced_player_name": None,
            "replacement_player_name": None,
            "title": "Test",
            "body": "Test body",
        }
        defaults.update(overrides)
        return NormalizedRecord(**defaults)

    def test_no_duplicates_returns_all(self) -> None:
        a = self._make(player_name="Virat Kohli")
        b = self._make(player_name="MS Dhoni", team_name="Chennai Super Kings")
        result = Deduplicator().deduplicate([a, b])
        assert len(result) == 2

    def test_exact_duplicate_keeps_highest_confidence(self) -> None:
        a = self._make(confidence=ConfidenceLevel.LOW)
        b = self._make(confidence=ConfidenceLevel.HIGH)
        result = Deduplicator().deduplicate([a, b])
        assert len(result) == 1
        assert result[0].confidence == ConfidenceLevel.HIGH

    def test_same_key_keeps_highest_confidence(self) -> None:
        a = self._make(confidence=ConfidenceLevel.MEDIUM)
        b = self._make(confidence=ConfidenceLevel.HIGH)
        c = self._make(confidence=ConfidenceLevel.LOW)
        result = Deduplicator().deduplicate([a, b, c])
        assert len(result) == 1
        assert result[0].confidence == ConfidenceLevel.HIGH

    def test_tie_same_confidence_keeps_more_fields(self) -> None:
        a = self._make(confidence=ConfidenceLevel.HIGH, team_name=None, injury_type=None)
        b = self._make(confidence=ConfidenceLevel.HIGH, team_name="RCB", injury_type="Knee")
        result = Deduplicator().deduplicate([a, b])
        assert len(result) == 1
        assert result[0].team_name == "RCB"

    def test_different_event_types_kept_separate(self) -> None:
        a = self._make(event_type=EventType.INJURY)
        b = self._make(event_type=EventType.RECOVERY)
        result = Deduplicator().deduplicate([a, b])
        assert len(result) == 2

    def test_different_source_names_kept_separate(self) -> None:
        a = self._make(source_name="ipl_official")
        b = self._make(source_name="espn_cricinfo")
        result = Deduplicator().deduplicate([a, b])
        assert len(result) == 2

    def test_different_effective_dates_kept_separate(self) -> None:
        a = self._make(effective_date=date(2026, 4, 1))
        b = self._make(effective_date=date(2026, 4, 15))
        result = Deduplicator().deduplicate([a, b])
        assert len(result) == 2

    def test_none_effective_date_uses_published_at(self) -> None:
        a = self._make(effective_date=None, published_at=date(2026, 4, 1))
        b = self._make(effective_date=None, published_at=date(2026, 4, 1))
        result = Deduplicator().deduplicate([a, b])
        assert len(result) == 1

    def test_different_event_types_same_player_kept(self) -> None:
        dedup = Deduplicator()
        records = [
            self._make(player_name="Virat Kohli", event_type=EventType.INJURY),
            self._make(player_name="Virat Kohli", event_type=EventType.RECOVERY),
        ]
        result = dedup.deduplicate(records)
        assert len(result) == 2

    def test_case_insensitive_player_name(self) -> None:
        a = self._make(player_name="Virat Kohli", event_type=EventType.INJURY)
        b = self._make(player_name="virat kohli", event_type=EventType.INJURY, confidence=ConfidenceLevel.HIGH)
        result = Deduplicator().deduplicate([a, b])
        assert len(result) == 1
        assert result[0].player_name == "virat kohli"

    def test_empty_input_returns_empty(self) -> None:
        result = Deduplicator().deduplicate([])
        assert result == []

    def test_single_record_returned(self) -> None:
        a = self._make()
        result = Deduplicator().deduplicate([a])
        assert len(result) == 1
        assert result[0] is a
