from enum import IntEnum, StrEnum


class EventType(StrEnum):
    INJURY = "injury"
    RECOVERY = "recovery"
    RULED_OUT = "ruled_out"
    REPLACEMENT_SIGNED = "replacement_signed"
    SUSPENSION = "suspension"
    ILLNESS = "illness"
    NATIONAL_DUTY = "national_duty"
    RESTED = "rested"
    PERSONAL_LEAVE = "personal_leave"
    AVAILABLE_AGAIN = "available_again"


class AvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class PlayerRole(StrEnum):
    BATTER = "batter"
    BOWLER = "bowler"
    ALL_ROUNDER = "all_rounder"
    WICKET_KEEPER = "wicket_keeper"


class ConfidenceLevel(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CONFIRMED = 4


class SourceType(StrEnum):
    RSS = "rss"
    WEB_SCRAPE = "web_scrape"
    MANUAL = "manual"
    API = "api"
