from datetime import date

from player_availability.domain.enums import (
    AvailabilityStatus,
    ConfidenceLevel,
    EventType,
)
from player_availability.parsers.rule_engine import (
    _clean_player_name,
    _find_all_keyword_matches,
    _is_team_name_exact,
    _is_valid_player_candidate,
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

    def test_high_takes_precedence_over_ruling_out_low(self) -> None:
        text = "speculation that he is ruled out"
        assert determine_confidence(text) == ConfidenceLevel.HIGH

    def test_low_takes_precedence_when_no_high_phrase(self) -> None:
        text = "speculation that he may miss the match"
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


class TestPublisherRejection:
    def test_cricinfo_rejected(self) -> None:
        assert extract_player_name("Cricinfo") is None

    def test_google_news_rejected(self) -> None:
        assert extract_player_name("Google News") is None

    def test_yahoo_sports_rejected(self) -> None:
        assert extract_player_name("Yahoo Sports") is None

    def test_sportstar_rejected(self) -> None:
        assert extract_player_name("Sportstar") is None

    def test_rediff_rejected(self) -> None:
        assert extract_player_name("Rediff") is None

    def test_generic_noun_rejected(self) -> None:
        assert extract_player_name("Latest") is None
        assert extract_player_name("This") is None
        assert extract_player_name("Full") is None

    def test_player_name_near_keyword_still_found(self) -> None:
        assert extract_player_name("Virat Kohli ruled out") == "Virat Kohli"

    def test_publisher_in_body_does_not_block_real_player(self) -> None:
        text = "Cricinfo reports that MS Dhoni suffered a knee injury"
        result = extract_player_name(text)
        assert result is not None
        assert "Dhoni" in result


class TestReplacementExtraction:
    def test_replaces_verb(self) -> None:
        text = "Akash Madhwal replaces Ayush Mhatre"
        from player_availability.parsers.rule_engine import _extract_replacement_pair

        incoming, outgoing = _extract_replacement_pair(text)
        assert incoming == "Akash Madhwal"
        assert outgoing == "Ayush Mhatre"

    def test_replaces_middle_initial(self) -> None:
        text = "Gerald Coetzee replaces David Payne"
        from player_availability.parsers.rule_engine import _extract_replacement_pair

        incoming, outgoing = _extract_replacement_pair(text)
        assert incoming == "Gerald Coetzee"
        assert outgoing == "David Payne"

    def test_signed_as_replacement_for(self) -> None:
        text = "CSK signs Richard Gleeson as replacement for Deepak Chahar"
        from player_availability.parsers.rule_engine import _extract_replacement_pair

        incoming, outgoing = _extract_replacement_pair(text)
        assert incoming == "Richard Gleeson"
        assert outgoing == "Deepak Chahar"

    def test_named_as_replacement_for(self) -> None:
        text = "MI names Lizaad Williams as replacement for Jasprit Bumrah"
        from player_availability.parsers.rule_engine import _extract_replacement_pair

        incoming, outgoing = _extract_replacement_pair(text)
        assert incoming == "Lizaad Williams"
        assert outgoing == "Jasprit Bumrah"

    def test_brought_in_for(self) -> None:
        text = "RCB brings in Will Jacks for Glenn Maxwell"
        from player_availability.parsers.rule_engine import _extract_replacement_pair

        incoming, outgoing = _extract_replacement_pair(text)
        assert incoming == "Will Jacks"
        assert outgoing == "Glenn Maxwell"

    def test_drafted_in_for(self) -> None:
        text = "KKR drafts in Rahmanullah Gurbaz for Phil Salt"
        from player_availability.parsers.rule_engine import _extract_replacement_pair

        incoming, outgoing = _extract_replacement_pair(text)
        assert incoming == "Rahmanullah Gurbaz"
        assert outgoing == "Phil Salt"

    def test_replacement_for_colon_format(self) -> None:
        text = "replacement for MS Dhoni: Urvil Patel named in CSK squad"
        from player_availability.parsers.rule_engine import _extract_replacement_pair

        incoming, outgoing = _extract_replacement_pair(text)
        assert incoming == "Urvil Patel"
        assert outgoing == "MS Dhoni"

    def test_self_replacement_returns_none(self) -> None:
        from player_availability.parsers.rule_engine import _extract_replacement_pair

        incoming, outgoing = _extract_replacement_pair("X replaces X")
        assert incoming is None
        assert outgoing is None

    def test_sign_without_s_detected_by_signed_name(self) -> None:
        from player_availability.parsers.rule_engine import _extract_replacement_signed_name

        text = "SK sign Akash Madhwal as replacement for"
        result = _extract_replacement_signed_name(text)
        assert result == "Akash Madhwal"

    def test_ropes_verb_detected_by_signed_name(self) -> None:
        from player_availability.parsers.rule_engine import _extract_replacement_signed_name

        text = "MI rope in Nuwan Thushara as replacement for"
        result = _extract_replacement_signed_name(text)
        assert result == "Nuwan Thushara"


class TestNewKeywords:
    def test_withdraws_detected(self) -> None:
        assert detect_event_type("withdraws from IPL") == EventType.RULED_OUT

    def test_unavailable_detected(self) -> None:
        assert detect_event_type("unavailable for selection") == EventType.RULED_OUT

    def test_ruled_available_detected(self) -> None:
        assert detect_event_type("ruled available for selection") == EventType.AVAILABLE_AGAIN

    def test_replaces_detected(self) -> None:
        assert detect_event_type("replaces injured player") == EventType.REPLACEMENT_SIGNED

    def test_sidelined_detected(self) -> None:
        assert detect_event_type("sidelined with injury") == EventType.INJURY

    def test_will_miss_detected(self) -> None:
        assert detect_event_type("will miss the season") == EventType.RULED_OUT

    def test_roped_in_detected(self) -> None:
        assert detect_event_type("roped in as replacement") == EventType.REPLACEMENT_SIGNED

    def test_emergency_signing_detected(self) -> None:
        assert detect_event_type("emergency signing for") == EventType.REPLACEMENT_SIGNED

    def test_hurt_detected(self) -> None:
        assert detect_event_type("hurt during training") == EventType.INJURY

    def test_niggle_detected(self) -> None:
        assert detect_event_type("hamstring niggle") == EventType.INJURY

    def test_scan_detected(self) -> None:
        assert detect_event_type("scan reveals injury") == EventType.INJURY

    def test_surgery_detected(self) -> None:
        assert detect_event_type("undergoes surgery") == EventType.INJURY

    def test_back_in_training_detected(self) -> None:
        assert detect_event_type("back in training") == EventType.RECOVERY

    def test_in_contention_detected(self) -> None:
        assert detect_event_type("in contention for selection") == EventType.RECOVERY

    def test_close_to_return_detected(self) -> None:
        assert detect_event_type("close to return from injury") == EventType.RECOVERY

    def test_all_clear_detected(self) -> None:
        assert detect_event_type("given all clear") == EventType.AVAILABLE_AGAIN

    def test_passed_medical_detected(self) -> None:
        assert detect_event_type("passed medical") == EventType.AVAILABLE_AGAIN

    def test_rejoins_squad_detected(self) -> None:
        assert detect_event_type("rejoins squad") == EventType.AVAILABLE_AGAIN

    def test_international_break_detected(self) -> None:
        assert detect_event_type("international break duty") == EventType.NATIONAL_DUTY

    def test_family_emergency_detected(self) -> None:
        assert detect_event_type("family emergency") == EventType.PERSONAL_LEAVE

    def test_rotation_detected(self) -> None:
        assert detect_event_type("rotation policy") == EventType.RESTED

    def test_sanction_detected(self) -> None:
        assert detect_event_type("handed a sanction") == EventType.SUSPENSION


class TestTeamNameExact:
    def test_full_team_name(self) -> None:
        assert _is_team_name_exact("chennai super kings") is True

    def test_team_abbreviation(self) -> None:
        assert _is_team_name_exact("csk") is True

    def test_partial_variant(self) -> None:
        assert _is_team_name_exact("chennai") is True

    def test_not_a_team(self) -> None:
        assert _is_team_name_exact("virat kohli") is False

    def test_empty_string(self) -> None:
        assert _is_team_name_exact("") is False

    def test_team_word_fragment_kings(self) -> None:
        assert _is_team_name_exact("kings") is True

    def test_team_word_fragment_indians(self) -> None:
        assert _is_team_name_exact("indians") is True

    def test_team_word_fragment_titans(self) -> None:
        assert _is_team_name_exact("titans") is True

    def test_team_word_fragment_royals(self) -> None:
        assert _is_team_name_exact("royals") is True

    def test_non_team_word_not_rejected(self) -> None:
        assert _is_team_name_exact("dhoni") is False
        assert _is_team_name_exact("kohli") is False


class TestIsValidPlayerCandidate:
    def test_valid_name(self) -> None:
        assert _is_valid_player_candidate("Virat Kohli") is True

    def test_valid_initial_name(self) -> None:
        assert _is_valid_player_candidate("MS Dhoni") is True

    def test_too_short(self) -> None:
        assert _is_valid_player_candidate("A") is False

    def test_publisher_name(self) -> None:
        assert _is_valid_player_candidate("Cricinfo") is False

    def test_generic_noun(self) -> None:
        assert _is_valid_player_candidate("Latest") is False

    def test_excellence_rejected(self) -> None:
        assert _is_valid_player_candidate("Excellence") is False

    def test_country_name(self) -> None:
        assert _is_valid_player_candidate("India") is False

    def test_headline_fragment_the(self) -> None:
        assert _is_valid_player_candidate("The") is False

    def test_headline_fragment_his(self) -> None:
        assert _is_valid_player_candidate("His") is False

    def test_headline_fragment_as(self) -> None:
        assert _is_valid_player_candidate("As") is False

    def test_region_name_karnataka(self) -> None:
        assert _is_valid_player_candidate("Karnataka") is False

    def test_region_name_south_african(self) -> None:
        assert _is_valid_player_candidate("South African") is False

    def test_headline_boilerplate(self) -> None:
        assert _is_valid_player_candidate("Injured Players List") is False

    def test_team_name_rejected(self) -> None:
        assert _is_valid_player_candidate("Chennai Super Kings") is False

    def test_team_abbreviation_rejected(self) -> None:
        assert _is_valid_player_candidate("CSK") is False

    def test_team_variant_rejected(self) -> None:
        assert _is_valid_player_candidate("Super Kings") is False

    def test_captain_rejected(self) -> None:
        assert _is_valid_player_candidate("Captain") is False

    def test_player_rejected(self) -> None:
        assert _is_valid_player_candidate("Player") is False

    def test_league_rejected(self) -> None:
        assert _is_valid_player_candidate("League") is False

    def test_centre_rejected(self) -> None:
        assert _is_valid_player_candidate("Centre") is False

    def test_april_rejected(self) -> None:
        assert _is_valid_player_candidate("April") is False

    def test_deepens_rejected(self) -> None:
        assert _is_valid_player_candidate("Deepens") is False

    def test_he_rejected(self) -> None:
        assert _is_valid_player_candidate("He") is False

    def test_still_rejected(self) -> None:
        assert _is_valid_player_candidate("Still") is False

    def test_played_rejected(self) -> None:
        assert _is_valid_player_candidate("Played") is False

    def test_month_name_january_rejected(self) -> None:
        assert _is_valid_player_candidate("January") is False

    def test_kings_team_word_rejected(self) -> None:
        assert _is_valid_player_candidate("Kings") is False

    def test_indians_team_word_rejected(self) -> None:
        assert _is_valid_player_candidate("Indians") is False


class TestCleanPlayerName:
    def test_none_input(self) -> None:
        assert _clean_player_name("") is None

    def test_valid_name_unchanged(self) -> None:
        assert _clean_player_name("Virat Kohli") == "Virat Kohli"

    def test_initial_name_unchanged(self) -> None:
        assert _clean_player_name("MS Dhoni") == "MS Dhoni"

    def test_single_word_valid_name_unchanged(self) -> None:
        assert _clean_player_name("Kohli") == "Kohli"

    def test_strips_headline_fragment_prefix(self) -> None:
        assert _clean_player_name("The Virat Kohli") == "Virat Kohli"

    def test_strips_headline_fragment_suffix(self) -> None:
        assert _clean_player_name("Forrester As") == "Forrester"

    def test_strips_country_prefix(self) -> None:
        assert _clean_player_name("India Ayush Mhatre") == "Ayush Mhatre"

    def test_strips_publisher_prefix(self) -> None:
        assert _clean_player_name("Cricket Country Bad") is None

    def test_strips_event_fragment_prefix(self) -> None:
        result = _clean_player_name("SK Sign Akash Madhwal")
        assert result == "Akash Madhwal"

    def test_strips_event_fragment_suffix(self) -> None:
        assert _clean_player_name("RS Ambrish As Injury") == "RS Ambrish"

    def test_strips_rope_in_prefix(self) -> None:
        assert _clean_player_name("Rope In Dian") == "Dian"

    def test_strips_boilerplate_prefix(self) -> None:
        assert _clean_player_name("A Former Rajasthan Royals") is None

    def test_strips_meet_prefix(self) -> None:
        assert _clean_player_name("Meet Macneil Hadley") == "Macneil Hadley"

    def test_strips_multi_region_prefix(self) -> None:
        assert _clean_player_name("South African Cricketer") == "Cricketer"

    def test_strips_multi_country_prefix(self) -> None:
        assert _clean_player_name("India Big") is None

    def test_strips_multi_noise(self) -> None:
        assert _clean_player_name("In Pakistan Super") is None

    def test_strips_tv_sports_publisher(self) -> None:
        assert _clean_player_name("TV Sports Chennai Super") is None

    def test_strips_still_suffix(self) -> None:
        assert _clean_player_name("Dhoni Still") == "Dhoni"

    def test_strips_he_and_played(self) -> None:
        assert _clean_player_name("He Last Played") is None

    def test_strips_month_prefix(self) -> None:
        assert _clean_player_name("April Dhoni") == "Dhoni"

    def test_strips_month_suffix(self) -> None:
        assert _clean_player_name("Dhoni April") == "Dhoni"

    def test_full_pipeline_contaminated_names(self) -> None:
        cases: list[tuple[str, str | None]] = [
            # (input, expected_output or None if fully rejected)
            # "Excellence" passes through cleanup; caught by _is_valid_player_candidate later
            ("Excellence", "Excellence"),
            ("The", None),
            ("His", None),
            ("Karnataka", None),
            ("South African", None),
            ("India Big", None),
            ("In Pakistan Super", None),
            ("TV Sports Chennai Super", None),
            ("Cricket Country Bad", None),
            ("SK Sign Akash Madhwal", "Akash Madhwal"),
            ("RS Ambrish As Injury", "RS Ambrish"),
            ("Forrester As", "Forrester"),
            ("Rope In Dian", "Dian"),
            ("Meet Macneil Hadley", "Macneil Hadley"),
            ("A Former Rajasthan Royals", None),
            ("Injured Players List", None),
            ("India Ayush Mhatre", "Ayush Mhatre"),
        ]
        for input_name, expected in cases:
            result = _clean_player_name(input_name)
            assert result == expected, f"_clean_player_name({input_name!r}) = {result!r}, expected {expected!r}"


class TestInvalidPlayerNameRejection:
    def test_excellence_rejected(self) -> None:
        assert extract_player_name("Excellence") is None

    def test_the_rejected(self) -> None:
        assert extract_player_name("The") is None

    def test_his_rejected(self) -> None:
        assert extract_player_name("His") is None

    def test_karnataka_rejected(self) -> None:
        assert extract_player_name("Karnataka") is None

    def test_south_african_rejected(self) -> None:
        assert extract_player_name("South African") is None

    def test_injured_players_list_rejected(self) -> None:
        assert extract_player_name("Injured Players List") is None

    def test_csk_team_name_rejected(self) -> None:
        assert extract_player_name("CSK") is None

    def test_clean_contaminated_name_finds_player(self) -> None:
        text = "India Ayush Mhatre ruled out of IPL"
        result = extract_player_name(text)
        assert result is not None
        assert "Ayush" in result

    def test_sk_sign_cleaned(self) -> None:
        text = "SK Sign Akash Madhwal named as replacement"
        result = extract_player_name(text)
        assert result is not None
        assert result == "Akash Madhwal"

    def test_meet_cleaned(self) -> None:
        text = "Meet Macneil Hadley signs for CSK"
        result = extract_player_name(text)
        assert result is not None
        assert result == "Macneil Hadley"

    def test_a_former_team_rejected(self) -> None:
        text = "A Former Rajasthan Royals replacement"
        assert extract_player_name(text) is None

    def test_in_pakistan_super_rejected(self) -> None:
        text = "In Pakistan Super injury replacement"
        assert extract_player_name(text) is None

    def test_forrester_as_cleaned(self) -> None:
        text = "Forrester As replacement for"
        result = extract_player_name(text)
        assert result is not None
        assert "Forrester" in result

    def test_country_prefix_cleaned(self) -> None:
        text = "India Ayush Mhatre injury"
        result = extract_player_name(text)
        assert result is not None
        assert result == "Ayush Mhatre"

    def test_dhoni_still_cleaned_to_dhoni(self) -> None:
        result = extract_player_name("Dhoni Still")
        assert result is not None
        assert result == "Dhoni"

    def test_he_last_played_rejected(self) -> None:
        assert extract_player_name("He Last Played") is None

    def test_captain_rejected(self) -> None:
        assert extract_player_name("Captain") is None

    def test_league_rejected(self) -> None:
        assert extract_player_name("League") is None

    def test_centre_rejected(self) -> None:
        assert extract_player_name("Centre") is None

    def test_april_rejected(self) -> None:
        assert extract_player_name("April") is None

    def test_deepens_rejected(self) -> None:
        assert extract_player_name("Deepens") is None

    def test_kings_rejected_by_team_word(self) -> None:
        assert extract_player_name("Kings") is None

    def test_indians_rejected_by_team_word(self) -> None:
        assert extract_player_name("Indians") is None

    def test_who_rejected(self) -> None:
        assert extract_player_name("Who") is None

    def test_world_cup_rejected(self) -> None:
        assert extract_player_name("World Cup") is None
