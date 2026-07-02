from datetime import date

import pytest

from player_availability.domain.enums import AvailabilityStatus, ConfidenceLevel, EventType
from player_availability.normalizers.exceptions import ValidationError
from player_availability.normalizers.models import NormalizedRecord
from player_availability.normalizers.utils import (
    count_non_none_fields,
    normalize_whitespace,
    strip_parenthetical_suffix,
    to_proper_case,
    validate_record,
)


class TestNormalizeWhitespace:
    def test_multiple_spaces(self) -> None:
        assert normalize_whitespace("Virat   Kohli") == "Virat Kohli"

    def test_leading_trailing_spaces(self) -> None:
        assert normalize_whitespace("  Virat Kohli  ") == "Virat Kohli"

    def test_tabs_and_newlines(self) -> None:
        assert normalize_whitespace("Virat\tKohli\nCaptain") == "Virat Kohli Captain"

    def test_empty_string(self) -> None:
        assert normalize_whitespace("") == ""

    def test_single_word(self) -> None:
        assert normalize_whitespace("  Hello  ") == "Hello"


class TestStripParentheticalSuffix:
    def test_basic_suffix(self) -> None:
        assert strip_parenthetical_suffix("Virat Kohli (India)") == "Virat Kohli"

    def test_no_parenthetical(self) -> None:
        assert strip_parenthetical_suffix("Virat Kohli") == "Virat Kohli"

    def test_multiple_words_in_parentheses(self) -> None:
        assert strip_parenthetical_suffix("KL Rahul (captain)") == "KL Rahul"

    def test_whitespace_before_parentheses(self) -> None:
        assert strip_parenthetical_suffix("Virat Kohli(India)") == "Virat Kohli"

    def test_only_parenthetical_returns_empty(self) -> None:
        assert strip_parenthetical_suffix("(India)") == ""

    def test_empty_string(self) -> None:
        assert strip_parenthetical_suffix("") == ""


class TestToProperCase:
    def test_basic_proper_case(self) -> None:
        assert to_proper_case("virat kohli") == "Virat Kohli"

    def test_preserve_short_initials(self) -> None:
        assert to_proper_case("MS Dhoni") == "MS Dhoni"

    def test_single_letter_initials(self) -> None:
        assert to_proper_case("V Kohli") == "V Kohli"

    def test_three_letter_initials(self) -> None:
        assert to_proper_case("ABD") == "ABD"

    def test_full_uppercase_longer_word_capitalized(self) -> None:
        result = to_proper_case("VIRAT KOHLI")
        assert result == "Virat Kohli"

    def test_mixed_case(self) -> None:
        assert to_proper_case("vIrAt kOhLi") == "Virat Kohli"

    def test_de_particles_preserved(self) -> None:
        assert to_proper_case("AB de Villiers") == "AB de Villiers"

    def test_du_plessis(self) -> None:
        assert to_proper_case("Faf du Plessis") == "Faf du Plessis"

    def test_empty_string(self) -> None:
        assert to_proper_case("") == ""


class TestValidateRecord:
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
            "title": "Virat Kohli injury update",
            "body": "Virat Kohli suffered a knee injury",
        }
        defaults.update(overrides)
        return NormalizedRecord(**defaults)

    def test_valid_record_passes(self) -> None:
        record = self._make_record()
        validate_record(record)

    def test_empty_player_name_raises(self) -> None:
        record = self._make_record(player_name="")
        with pytest.raises(ValidationError, match="player_name is empty"):
            validate_record(record)

    def test_none_event_type_raises(self) -> None:
        record = self._make_record(event_type=None)
        with pytest.raises(ValidationError, match="event_type is None"):
            validate_record(record)

    def test_none_availability_status_raises(self) -> None:
        record = self._make_record(availability_status=None)
        with pytest.raises(ValidationError, match="availability_status is None"):
            validate_record(record)

    def test_none_confidence_raises(self) -> None:
        record = self._make_record(confidence=None)
        with pytest.raises(ValidationError, match="confidence is None"):
            validate_record(record)

    def test_empty_source_name_raises(self) -> None:
        record = self._make_record(source_name="")
        with pytest.raises(ValidationError, match="source_name is empty"):
            validate_record(record)

    def test_none_published_at_raises(self) -> None:
        record = self._make_record(published_at=None)
        with pytest.raises(ValidationError, match="published_at is None"):
            validate_record(record)

    def test_replaced_player_same_as_player_raises(self) -> None:
        record = self._make_record(replaced_player_name="Virat Kohli")
        with pytest.raises(ValidationError, match="replaced_player_name cannot be the same"):
            validate_record(record)

    def test_replacement_player_same_as_player_raises(self) -> None:
        record = self._make_record(replacement_player_name="Virat Kohli")
        with pytest.raises(ValidationError, match="replacement_player_name cannot be the same"):
            validate_record(record)

    def test_multiple_errors_reported(self) -> None:
        record = self._make_record(player_name="", event_type=None)
        with pytest.raises(ValidationError) as exc:
            validate_record(record)
        assert "player_name is empty" in str(exc.value)
        assert "event_type is None" in str(exc.value)

    def test_publisher_name_rejected(self) -> None:
        record = self._make_record(player_name="Cricbuzz")
        with pytest.raises(ValidationError, match="matches a publisher name"):
            validate_record(record)

    def test_generic_noun_rejected(self) -> None:
        record = self._make_record(player_name="Highlights")
        with pytest.raises(ValidationError, match="matches a generic noun"):
            validate_record(record)

    def test_country_name_rejected(self) -> None:
        record = self._make_record(player_name="India")
        with pytest.raises(ValidationError, match="matches a country name"):
            validate_record(record)

    def test_low_confidence_alone_does_not_raise(self) -> None:
        record = self._make_record(confidence=ConfidenceLevel.LOW)
        validate_record(record)

    def test_low_confidence_with_other_errors_appended(self) -> None:
        record = self._make_record(confidence=ConfidenceLevel.LOW, player_name="")
        with pytest.raises(ValidationError) as exc:
            validate_record(record)
        assert "confidence is LOW" in str(exc.value)
        assert "player_name is empty" in str(exc.value)


class TestCountNonNoneFields:
    def test_all_fields_set(self) -> None:
        record = NormalizedRecord(
            player_name="Virat Kohli",
            event_type=EventType.INJURY,
            availability_status=AvailabilityStatus.UNAVAILABLE,
            confidence=ConfidenceLevel.HIGH,
            source_name="ipl_official",
            source_url="https://example.com",
            published_at=date(2026, 4, 1),
            effective_date=date(2026, 4, 1),
            team_name="RCB",
            injury_type="Knee",
            replaced_player_name=None,
            replacement_player_name=None,
            title="Test",
            body="Body",
        )
        # 14 fields total, 12 set (2 are None)
        assert count_non_none_fields(record) == 12

    def test_minimal_record(self) -> None:
        record = NormalizedRecord(
            player_name="Test",
            event_type=EventType.INJURY,
            availability_status=AvailabilityStatus.UNAVAILABLE,
            confidence=ConfidenceLevel.LOW,
            source_name="test",
            source_url=None,
            published_at=date(2026, 4, 1),
            effective_date=None,
            team_name=None,
            injury_type=None,
            replaced_player_name=None,
            replacement_player_name=None,
            title="",
            body="",
        )
        assert count_non_none_fields(record) == 8
