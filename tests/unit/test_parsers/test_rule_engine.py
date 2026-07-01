from datetime import date

from player_availability.domain.enums import (
    AvailabilityStatus,
    ConfidenceLevel,
    EventType,
)
from player_availability.parsers.rule_engine import (
    _find_all_keyword_matches,
    detect_event_type,
    determine_confidence,
    extract_effective_date,
    extract_injury_type,
    extract_player_name,
    extract_player_name_from_title,
    extract_replacement,
    extract_team_name,
    map_event_to_status,
)


class TestDetectEventType:
    def test_injury(self) -> None:
        assert detect_event_type("suffered a knee injury") == EventType.INJURY

    def test_ruled_out_higher_priority(self) -> None:
        text = "ruled out due to a hamstring injury"
        assert detect_event_type(text) == EventType.RULED_OUT

    def test_replacement_signed(self) -> None:
        assert detect_event_type("signed as replacement for") == EventType.REPLACEMENT_SIGNED

    def test_recovery(self) -> None:
        assert detect_event_type("recovered from injury") == EventType.RECOVERY

    def test_available_again(self) -> None:
        assert detect_event_type("declared fit for selection") == EventType.AVAILABLE_AGAIN

    def test_suspension(self) -> None:
        assert detect_event_type("suspended for 2 matches") == EventType.SUSPENSION

    def test_illness(self) -> None:
        assert detect_event_type("misses match due to illness") == EventType.ILLNESS

    def test_national_duty(self) -> None:
        assert detect_event_type("called up for national duty") == EventType.NATIONAL_DUTY

    def test_rested(self) -> None:
        assert detect_event_type("rested for the next match") == EventType.RESTED

    def test_personal_leave(self) -> None:
        assert detect_event_type("granted personal leave") == EventType.PERSONAL_LEAVE

    def test_no_match_returns_none(self) -> None:
        assert detect_event_type("match preview and analysis") is None


class TestExtractPlayerName:
    def test_basic_name_in_text(self) -> None:
        text = "MS Dhoni suffered a knee injury during training"
        assert extract_player_name(text) == "MS Dhoni"

    def test_multiple_candidates_picks_closest_to_keyword(self) -> None:
        text = "Rohit Sharma scored a century while Jasprit Bumrah suffered a back injury"
        assert extract_player_name(text) == "Jasprit Bumrah"

    def test_no_event_keyword_still_finds_name(self) -> None:
        text = "Virat Kohli is playing well this season"
        assert extract_player_name(text) == "Virat Kohli"

    def test_no_player_name_returns_none(self) -> None:
        assert extract_player_name("the match was very exciting") is None

    def test_knows_non_player_phrases(self) -> None:
        assert extract_player_name("Indian Premier League cricket") is None


class TestExtractPlayerNameFromTitle:
    def test_name_before_event(self) -> None:
        title = "MS Dhoni suffers knee injury during training"
        assert extract_player_name_from_title(title) == "MS Dhoni"

    def test_name_before_ruled_out(self) -> None:
        title = "Jasprit Bumrah ruled out of IPL 2026 due to back injury"
        assert extract_player_name_from_title(title) == "Jasprit Bumrah"

    def test_name_with_colon(self) -> None:
        title = "Virat Kohli: declared fit for IPL 2026"
        assert extract_player_name_from_title(title) == "Virat Kohli"

    def test_no_event_returns_none(self) -> None:
        assert extract_player_name_from_title("Match Preview: CSK vs MI") is None

    def test_initial_based_name(self) -> None:
        title = "KL Rahul suffers side strain during practice"
        assert extract_player_name_from_title(title) == "KL Rahul"


class TestExtractTeamName:
    def test_full_name(self) -> None:
        assert extract_team_name("Chennai Super Kings") == "Chennai Super Kings"

    def test_short_code(self) -> None:
        assert extract_team_name("CSK") == "Chennai Super Kings"

    def test_partial_name(self) -> None:
        assert extract_team_name("Mumbai Indians") == "Mumbai Indians"

    def test_lowercase(self) -> None:
        assert extract_team_name("rcb") == "Royal Challengers Bengaluru"

    def test_no_team_returns_none(self) -> None:
        assert extract_team_name("no team mentioned") is None


class TestExtractInjuryType:
    def test_knee(self) -> None:
        assert extract_injury_type("knee injury") == "knee"

    def test_hamstring(self) -> None:
        assert extract_injury_type("hamstring strain") == "hamstring"

    def test_back(self) -> None:
        assert extract_injury_type("back problem") == "back"

    def test_no_injury(self) -> None:
        assert extract_injury_type("no injury mentioned") is None

    def test_case_insensitive(self) -> None:
        assert extract_injury_type("Groin Strain") == "groin"


class TestExtractReplacement:
    def test_replacement_found(self) -> None:
        text = "CSK signs Urvil Patel as replacement for MS Dhoni"
        assert extract_replacement(text) == "MS Dhoni"

    def test_no_replacement_returns_none(self) -> None:
        assert extract_replacement("no replacement mentioned") is None


class TestDetermineConfidence:
    def test_high_confidence(self) -> None:
        assert determine_confidence("ruled out officially") == ConfidenceLevel.HIGH

    def test_medium_confidence(self) -> None:
        assert determine_confidence("expected to miss") == ConfidenceLevel.MEDIUM

    def test_low_confidence(self) -> None:
        assert determine_confidence("speculation about injury") == ConfidenceLevel.LOW

    def test_medium_without_high_or_low(self) -> None:
        text = "expected to be out"
        assert determine_confidence(text) == ConfidenceLevel.MEDIUM

    def test_low_overrides_all(self) -> None:
        text = "speculation that he is ruled out"
        assert determine_confidence(text) == ConfidenceLevel.LOW


class TestMapEventToStatus:
    def test_injury_unavailable(self) -> None:
        assert map_event_to_status(EventType.INJURY) == AvailabilityStatus.UNAVAILABLE

    def test_ruled_out_unavailable(self) -> None:
        assert map_event_to_status(EventType.RULED_OUT) == AvailabilityStatus.UNAVAILABLE

    def test_recovery_available(self) -> None:
        assert map_event_to_status(EventType.RECOVERY) == AvailabilityStatus.AVAILABLE

    def test_available_again_available(self) -> None:
        assert map_event_to_status(EventType.AVAILABLE_AGAIN) == AvailabilityStatus.AVAILABLE

    def test_replacement_signed_available(self) -> None:
        assert map_event_to_status(EventType.REPLACEMENT_SIGNED) == AvailabilityStatus.AVAILABLE


class TestFindAllKeywordMatches:
    def test_finds_event_keywords(self) -> None:
        from player_availability.domain.enums import EventType

        text = "ruled out due to injury"
        matches = _find_all_keyword_matches(text)
        match_types = {m[0] for m in matches}
        assert EventType.RULED_OUT in match_types
        assert EventType.INJURY in match_types


class TestExtractEffectiveDate:
    def test_on_date_format(self) -> None:
        text = "expected to return on April 15 2026"
        result = extract_effective_date(text, date(2026, 4, 1))
        assert result == date(2026, 4, 15)

    def test_no_date_returns_none(self) -> None:
        assert extract_effective_date("no date mentioned", date(2026, 4, 1)) is None
