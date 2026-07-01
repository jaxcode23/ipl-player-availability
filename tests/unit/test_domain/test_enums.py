from player_availability.domain.enums import (
    AvailabilityStatus,
    ConfidenceLevel,
    EventType,
    PlayerRole,
    SourceType,
)


class TestEventType:
    def test_values(self) -> None:
        assert EventType.INJURY.value == "injury"
        assert EventType.RECOVERY.value == "recovery"
        assert EventType.RULED_OUT.value == "ruled_out"
        assert EventType.REPLACEMENT_SIGNED.value == "replacement_signed"
        assert EventType.SUSPENSION.value == "suspension"
        assert EventType.ILLNESS.value == "illness"
        assert EventType.NATIONAL_DUTY.value == "national_duty"
        assert EventType.RESTED.value == "rested"
        assert EventType.PERSONAL_LEAVE.value == "personal_leave"
        assert EventType.AVAILABLE_AGAIN.value == "available_again"

    def test_all_events_listed(self) -> None:
        assert len(EventType) == 10


class TestAvailabilityStatus:
    def test_values(self) -> None:
        assert AvailabilityStatus.AVAILABLE.value == "available"
        assert AvailabilityStatus.UNAVAILABLE.value == "unavailable"
        assert AvailabilityStatus.UNKNOWN.value == "unknown"


class TestPlayerRole:
    def test_values(self) -> None:
        assert PlayerRole.BATTER.value == "batter"
        assert PlayerRole.BOWLER.value == "bowler"
        assert PlayerRole.ALL_ROUNDER.value == "all_rounder"
        assert PlayerRole.WICKET_KEEPER.value == "wicket_keeper"


class TestConfidenceLevel:
    def test_order(self) -> None:
        assert ConfidenceLevel.LOW.value < ConfidenceLevel.MEDIUM.value
        assert ConfidenceLevel.MEDIUM.value < ConfidenceLevel.HIGH.value
        assert ConfidenceLevel.HIGH.value < ConfidenceLevel.CONFIRMED.value


class TestSourceType:
    def test_values(self) -> None:
        assert SourceType.RSS.value == "rss"
        assert SourceType.WEB_SCRAPE.value == "web_scrape"
        assert SourceType.MANUAL.value == "manual"
        assert SourceType.API.value == "api"
