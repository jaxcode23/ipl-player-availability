from datetime import date

from player_availability.domain.enums import (
    AvailabilityStatus,
    ConfidenceLevel,
    EventType,
)
from player_availability.normalizers.default_normalizer import DefaultNormalizer
from player_availability.parsers.base import ParsedRecord


class TestDefaultNormalizer:
    def _make_parsed(self, **overrides: object) -> ParsedRecord:
        defaults: dict[str, object] = {
            "source_name": "ipl_official",
            "title": "Virat Kohli suffers knee injury",
            "body": "Virat Kohli suffered a knee injury during training at Chinnaswamy.",
            "url": "https://example.com/kohli-injury",
            "published_at": date(2026, 4, 1),
            "player_name": "Virat Kohli",
            "replacement_player": None,
            "team_name": "Royal Challengers Bengaluru",
            "event_type": EventType.INJURY,
            "availability_status": AvailabilityStatus.UNAVAILABLE,
            "injury_type": "knee",
            "effective_date": date(2026, 4, 1),
            "confidence": ConfidenceLevel.MEDIUM,
            "parser_version": "1.0.0",
        }
        defaults.update(overrides)
        return ParsedRecord(**defaults)

    def test_empty_input(self) -> None:
        normalizer = DefaultNormalizer()
        result = normalizer.normalize([])
        assert result == []

    def test_basic_normalization(self) -> None:
        normalizer = DefaultNormalizer()
        record = self._make_parsed()
        result = normalizer.normalize([record])
        assert len(result) == 1
        nr = result[0]
        assert nr.player_name == "Virat Kohli"
        assert nr.event_type == EventType.INJURY
        assert nr.team_name == "Royal Challengers Bengaluru"
        assert nr.injury_type == "Knee Injury"
        assert nr.confidence == ConfidenceLevel.MEDIUM

    def test_player_alias_resolved(self) -> None:
        normalizer = DefaultNormalizer()
        record = self._make_parsed(player_name="Kohli")
        result = normalizer.normalize([record])
        assert len(result) == 1
        assert result[0].player_name == "Virat Kohli"

    def test_team_alias_resolved(self) -> None:
        normalizer = DefaultNormalizer()
        record = self._make_parsed(team_name="RCB")
        result = normalizer.normalize([record])
        assert len(result) == 1
        assert result[0].team_name == "Royal Challengers Bengaluru"

    def test_replacement_player_normalized(self) -> None:
        normalizer = DefaultNormalizer()
        record = self._make_parsed(
            player_name="Urvil Patel",
            replacement_player="MS Dhoni",
            team_name="CSK",
            event_type=EventType.REPLACEMENT_SIGNED,
            availability_status=AvailabilityStatus.AVAILABLE,
            confidence=ConfidenceLevel.HIGH,
        )
        result = normalizer.normalize([record])
        assert len(result) == 1
        nr = result[0]
        assert nr.player_name == "Urvil Patel"
        assert nr.replaced_player_name == "MS Dhoni"
        assert nr.team_name == "Chennai Super Kings"

    def test_skip_record_with_no_player_name(self) -> None:
        normalizer = DefaultNormalizer()
        record = self._make_parsed(player_name=None)
        result = normalizer.normalize([record])
        assert len(result) == 0

    def test_skip_record_with_empty_player_name(self) -> None:
        normalizer = DefaultNormalizer()
        record = self._make_parsed(player_name="")
        result = normalizer.normalize([record])
        assert len(result) == 0

    def test_deduplication_keeps_highest_confidence(self) -> None:
        normalizer = DefaultNormalizer()
        a = self._make_parsed(confidence=ConfidenceLevel.LOW)
        b = self._make_parsed(confidence=ConfidenceLevel.HIGH)
        result = normalizer.normalize([a, b])
        assert len(result) == 1
        assert result[0].confidence == ConfidenceLevel.HIGH

    def test_multiple_events_different_players(self) -> None:
        normalizer = DefaultNormalizer()
        a = self._make_parsed(player_name="Kohli", title="Kohli injury")
        b = self._make_parsed(player_name="Dhoni", team_name="CSK", title="Dhoni injury")
        result = normalizer.normalize([a, b])
        assert len(result) == 2
        names = {r.player_name for r in result}
        assert "Virat Kohli" in names
        assert "MS Dhoni" in names

    def test_whitespace_normalized(self) -> None:
        normalizer = DefaultNormalizer()
        record = self._make_parsed(player_name="  Virat   Kohli  ")
        result = normalizer.normalize([record])
        assert len(result) == 1
        assert result[0].player_name == "Virat Kohli"

    def test_parenthetical_stripped(self) -> None:
        normalizer = DefaultNormalizer()
        record = self._make_parsed(player_name="Virat Kohli (India)")
        result = normalizer.normalize([record])
        assert len(result) == 1
        assert result[0].player_name == "Virat Kohli"

    def test_injury_type_normalized(self) -> None:
        normalizer = DefaultNormalizer()
        record = self._make_parsed(injury_type="tight hamstring")
        result = normalizer.normalize([record])
        assert len(result) == 1
        assert result[0].injury_type == "Hamstring Injury"

    def test_unknown_normalized_data_passes_through(self) -> None:
        normalizer = DefaultNormalizer()
        record = self._make_parsed(
            player_name="Some Player",
            team_name="Some Team",
            injury_type="some injury",
        )
        result = normalizer.normalize([record])
        assert len(result) == 1
        nr = result[0]
        assert nr.player_name == "Some Player"
        assert nr.team_name == "Some Team"
        assert nr.injury_type == "Some Injury"

    def test_multi_source_multi_event(self) -> None:
        normalizer = DefaultNormalizer()
        records = [
            self._make_parsed(
                player_name="Rohit Sharma",
                team_name="MI",
                source_name="ipl_official",
                event_type=EventType.INJURY,
            ),
            self._make_parsed(
                player_name="MS Dhoni",
                team_name="CSK",
                source_name="espn_cricinfo",
                event_type=EventType.RECOVERY,
                availability_status=AvailabilityStatus.AVAILABLE,
            ),
        ]
        result = normalizer.normalize(records)
        assert len(result) == 2
