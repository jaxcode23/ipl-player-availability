from datetime import datetime

import pytest

from player_availability.collectors.base import RawData
from player_availability.domain.enums import (
    AvailabilityStatus,
    ConfidenceLevel,
    EventType,
)
from player_availability.parsers.espn_cricinfo import ESPNCricinfoParser
from player_availability.parsers.ipl_official import IPLOfficialParser

_INJURY_HTML = "<p>MS Dhoni suffered a knee injury during training at Chepauk.</p>"
_RULED_OUT_HTML = "<p>Jasprit Bumrah has been ruled out of IPL 2026 due to a back injury.</p>"
_REPLACEMENT_HTML = "<p>CSK signs Urvil Patel as replacement for MS Dhoni.</p>"
_RECOVERY_HTML = "<p>Virat Kohli has recovered from his hamstring injury and is fit again.</p>"
_AVAILABLE_HTML = "<p>Shubman Gill has been declared fit for IPL 2026.</p>"
_SUSPENSION_HTML = "<p>Player X has been suspended for 2 matches for misconduct.</p>"
_ILLNESS_HTML = "<p>Rohit Sharma misses training due to illness.</p>"
_NON_AVAIL_HTML = "<p>Match preview: CSK vs MI in the upcoming clash at Wankhede.</p>"
_EMPTY_HTML = ""
_MULTIPLE_HTML = "<p>MS Dhoni has been ruled out due to injury. CSK signs Urvil Patel as replacement for MS Dhoni.</p>"


@pytest.fixture
def raw_injury() -> RawData:
    return RawData(
        source_name="ipl_official",
        title="MS Dhoni suffers knee injury during training",
        content=_INJURY_HTML,
        url="https://example.com/dhoni-injury",
        published_at=datetime(2026, 4, 1, 10, 30, 0),
    )


@pytest.fixture
def raw_ruled_out() -> RawData:
    return RawData(
        source_name="ipl_official",
        title="Jasprit Bumrah ruled out of IPL 2026 due to back injury",
        content=_RULED_OUT_HTML,
        url="https://example.com/bumrah-out",
        published_at=datetime(2026, 4, 2, 9, 0, 0),
    )


@pytest.fixture
def raw_replacement() -> RawData:
    return RawData(
        source_name="espn_cricinfo",
        title="CSK signs Urvil Patel as replacement for Dhoni",
        content=_REPLACEMENT_HTML,
        url="https://example.com/replacement",
        published_at=datetime(2026, 4, 3, 14, 0, 0),
    )


@pytest.fixture
def raw_recovery() -> RawData:
    return RawData(
        source_name="ipl_official",
        title="Virat Kohli recovers from hamstring injury",
        content=_RECOVERY_HTML,
        url="https://example.com/kohli-recovery",
        published_at=datetime(2026, 4, 4, 11, 0, 0),
    )


@pytest.fixture
def raw_available() -> RawData:
    return RawData(
        source_name="espn_cricinfo",
        title="Shubman Gill declared fit for IPL 2026",
        content=_AVAILABLE_HTML,
        url="https://example.com/gill-fit",
        published_at=datetime(2026, 4, 5, 16, 0, 0),
    )


@pytest.fixture
def raw_suspension() -> RawData:
    return RawData(
        source_name="ipl_official",
        title="Player X suspended for misconduct",
        content=_SUSPENSION_HTML,
        url="https://example.com/suspension",
        published_at=datetime(2026, 4, 6, 8, 0, 0),
    )


@pytest.fixture
def raw_illness() -> RawData:
    return RawData(
        source_name="espn_cricinfo",
        title="Rohit Sharma misses training due to illness",
        content=_ILLNESS_HTML,
        url="https://example.com/illness",
        published_at=datetime(2026, 4, 7, 7, 0, 0),
    )


@pytest.fixture
def raw_non_availability() -> RawData:
    return RawData(
        source_name="ipl_official",
        title="Match Preview: CSK vs MI",
        content=_NON_AVAIL_HTML,
        url="https://example.com/preview",
        published_at=datetime(2026, 4, 8, 12, 0, 0),
    )


@pytest.fixture
def raw_multi_event() -> RawData:
    return RawData(
        source_name="espn_cricinfo",
        title="MS Dhoni ruled out, Urvil Patel named replacement",
        content=_MULTIPLE_HTML,
        url="https://example.com/multi",
        published_at=datetime(2026, 4, 9, 15, 0, 0),
    )


class TestIPLOfficialParser:
    def test_parse_injury(self, raw_injury: RawData) -> None:
        parser = IPLOfficialParser()
        results = parser.parse(raw_injury)
        assert len(results) == 1
        rec = results[0]
        assert rec.event_type == EventType.INJURY
        assert rec.player_name == "MS Dhoni"
        assert rec.injury_type == "knee"
        assert rec.availability_status == AvailabilityStatus.UNAVAILABLE
        assert rec.confidence == ConfidenceLevel.MEDIUM
        assert rec.source_name == "ipl_official"
        assert rec.parser_version == "1.0.0"

    def test_parse_ruled_out(self, raw_ruled_out: RawData) -> None:
        parser = IPLOfficialParser()
        results = parser.parse(raw_ruled_out)
        assert len(results) == 1
        rec = results[0]
        assert rec.event_type == EventType.RULED_OUT
        assert rec.player_name == "Jasprit Bumrah"
        assert rec.injury_type == "back"
        assert rec.availability_status == AvailabilityStatus.UNAVAILABLE
        assert rec.confidence == ConfidenceLevel.HIGH

    def test_parse_recovery(self, raw_recovery: RawData) -> None:
        parser = IPLOfficialParser()
        results = parser.parse(raw_recovery)
        assert len(results) == 1
        rec = results[0]
        assert rec.event_type == EventType.RECOVERY
        assert rec.player_name == "Virat Kohli"
        assert rec.availability_status == AvailabilityStatus.AVAILABLE

    def test_non_availability_returns_empty(self, raw_non_availability: RawData) -> None:
        parser = IPLOfficialParser()
        results = parser.parse(raw_non_availability)
        assert results == []

    def test_empty_content_does_not_crash(self) -> None:
        raw = RawData(
            source_name="ipl_official",
            title="",
            content="",
            url="https://example.com/empty",
        )
        parser = IPLOfficialParser()
        assert parser.parse(raw) == []

    def test_supported_source(self) -> None:
        parser = IPLOfficialParser()
        assert parser.can_handle("ipl_official") is True
        assert parser.can_handle("espn_cricinfo") is False
        assert parser.can_handle("mock") is False

    def test_parse_suspension(self, raw_suspension: RawData) -> None:
        parser = IPLOfficialParser()
        results = parser.parse(raw_suspension)
        assert len(results) == 1
        rec = results[0]
        assert rec.event_type == EventType.SUSPENSION
        assert rec.availability_status == AvailabilityStatus.UNAVAILABLE
        assert rec.confidence == ConfidenceLevel.HIGH


class TestESPNCricinfoParser:
    def test_parse_replacement(self, raw_replacement: RawData) -> None:
        parser = ESPNCricinfoParser()
        results = parser.parse(raw_replacement)
        assert len(results) == 1
        rec = results[0]
        assert rec.event_type == EventType.REPLACEMENT_SIGNED
        assert rec.player_name == "Urvil Patel"
        assert rec.replacement_player == "Dhoni"
        assert rec.team_name == "Chennai Super Kings"
        assert rec.availability_status == AvailabilityStatus.AVAILABLE

    def test_parse_available(self, raw_available: RawData) -> None:
        parser = ESPNCricinfoParser()
        results = parser.parse(raw_available)
        assert len(results) == 1
        rec = results[0]
        assert rec.event_type == EventType.AVAILABLE_AGAIN
        assert rec.player_name == "Shubman Gill"
        assert rec.availability_status == AvailabilityStatus.AVAILABLE
        assert rec.confidence == ConfidenceLevel.HIGH
        assert rec.source_name == "espn_cricinfo"

    def test_parse_illness(self, raw_illness: RawData) -> None:
        parser = ESPNCricinfoParser()
        results = parser.parse(raw_illness)
        assert len(results) == 1
        rec = results[0]
        assert rec.event_type == EventType.ILLNESS
        assert rec.player_name == "Rohit Sharma"
        assert rec.availability_status == AvailabilityStatus.UNAVAILABLE

    def test_non_availability_returns_empty(self) -> None:
        raw = RawData(
            source_name="espn_cricinfo",
            title="Cricket News Roundup",
            content="<p>Today in cricket news from around the world.</p>",
            url="https://example.com/roundup",
            published_at=datetime(2026, 4, 10, 6, 0, 0),
        )
        parser = ESPNCricinfoParser()
        assert parser.parse(raw) == []

    def test_supported_source(self) -> None:
        parser = ESPNCricinfoParser()
        assert parser.can_handle("espn_cricinfo") is True
        assert parser.can_handle("ipl_official") is False
        assert parser.can_handle("mock") is False


class TestMultiEventParsing:
    def test_multiple_events_in_one_article(self, raw_multi_event: RawData) -> None:
        parser = ESPNCricinfoParser()
        results = parser.parse(raw_multi_event)
        assert len(results) == 2

        player_names = {r.player_name for r in results}
        assert "MS Dhoni" in player_names
        assert "Urvil Patel" in player_names

        for rec in results:
            assert rec.source_name == "espn_cricinfo"
            assert rec.parser_version == "1.0.0"

    def test_multiple_events_produces_multiple_records(self, raw_multi_event: RawData) -> None:
        parser = ESPNCricinfoParser()
        results = parser.parse(raw_multi_event)
        assert len(results) == 2
