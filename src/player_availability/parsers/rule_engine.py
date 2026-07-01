import re
from datetime import date, datetime

from loguru import logger

from ..collectors.base import RawData
from ..domain.enums import AvailabilityStatus, ConfidenceLevel, EventType
from .base import ParsedRecord
from .patterns import (
    EVENT_KEYWORDS,
    EVENT_PRIORITY,
    HIGH_CONFIDENCE_PHRASES,
    INJURY_KEYWORDS,
    LOW_CONFIDENCE_PHRASES,
    MEDIUM_CONFIDENCE_PHRASES,
    TEAM_NAMES,
)
from .utils import clean_html

_PLAYER_RE = re.compile(r"(?:[A-Z]{1,2}\.?\s+)?[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2}")


def parse_article(raw_data: RawData, source_name: str) -> list[ParsedRecord]:
    body = clean_html(raw_data.content)
    combined = f"{raw_data.title} {body}".strip()
    published_at_date = raw_data.published_at.date() if raw_data.published_at else date.today()

    text_lower = combined.lower()
    matches = _find_all_keyword_matches(text_lower)

    if not matches:
        logger.debug("No availability event detected from '{}'", source_name)
        return []

    seen: set[tuple[str, EventType]] = set()
    records: list[ParsedRecord] = []

    for event_type, kw_start, kw_end in matches:
        window_start = max(0, kw_start - 60)
        window_end = min(len(combined), kw_end + 60)
        context = combined[window_start:window_end]

        player: str | None = None

        if event_type == EventType.REPLACEMENT_SIGNED:
            player = _extract_replacement_signed_name(combined)

        if player is None:
            player = _find_nearest_name(context)
        if player is None:
            player = extract_player_name_from_title(raw_data.title, event_type)
        if player is None:
            continue

        key = (player.lower(), event_type)
        if key in seen:
            continue
        seen.add(key)

        team_name = extract_team_name(context) or extract_team_name(combined)
        injury_type = extract_injury_type(context)
        replacement = extract_replacement(context) or extract_replacement(combined)
        effective_date = extract_effective_date(context, published_at_date)
        confidence = determine_confidence(combined, event_type)

        records.append(
            ParsedRecord(
                source_name=source_name,
                title=raw_data.title,
                body=body,
                url=raw_data.url,
                published_at=published_at_date,
                player_name=player,
                replacement_player=replacement,
                team_name=team_name,
                event_type=event_type,
                availability_status=map_event_to_status(event_type),
                injury_type=injury_type,
                effective_date=effective_date,
                confidence=confidence,
            )
        )

    return _deduplicate_records(records)


def _find_all_keyword_matches(text_lower: str) -> list[tuple[EventType, int, int]]:
    matches: list[tuple[EventType, int, int]] = []
    for event_type in EVENT_PRIORITY:
        for kw in EVENT_KEYWORDS[event_type]:
            start = 0
            while True:
                idx = text_lower.find(kw, start)
                if idx == -1:
                    break
                matches.append((event_type, idx, idx + len(kw)))
                start = idx + 1
    return matches


def _deduplicate_records(records: list[ParsedRecord]) -> list[ParsedRecord]:
    best: dict[str, ParsedRecord] = {}
    for rec in records:
        if rec.player_name is None:
            continue
        key = rec.player_name.lower()
        existing = best.get(key)
        if existing is None:
            best[key] = rec
        else:
            existing_pri = _priority(existing.event_type)
            new_pri = _priority(rec.event_type)
            if new_pri < existing_pri:
                best[key] = rec
    result = list(best.values())
    result.sort(key=lambda r: r.player_name or "")
    return result


def _priority(event_type: EventType | None) -> int:
    if event_type is None:
        return len(EVENT_PRIORITY)
    try:
        return EVENT_PRIORITY.index(event_type)
    except ValueError:
        return len(EVENT_PRIORITY)


def detect_event_type(text: str) -> EventType | None:
    text_lower = text.lower()
    for event_type in EVENT_PRIORITY:
        keywords = EVENT_KEYWORDS[event_type]
        for kw in keywords:
            if kw in text_lower:
                return event_type
    return None


def extract_player_name(text: str) -> str | None:
    candidates = _find_name_candidates(text)
    if not candidates:
        return None

    text_lower = text.lower()
    best_name = None
    best_dist = float("inf")

    for event_type in EVENT_PRIORITY:
        for kw in EVENT_KEYWORDS[event_type]:
            idx = text_lower.find(kw)
            if idx == -1:
                continue
            for name, start in candidates:
                dist = abs(start - idx)
                if dist < best_dist:
                    best_dist = dist
                    best_name = name

    if best_name:
        return best_name
    return candidates[0][0]


def extract_player_name_from_title(title: str, preferred_event: EventType | None = None) -> str | None:
    title_lower = title.lower()

    if preferred_event is not None:
        for kw in EVENT_KEYWORDS[preferred_event]:
            idx = title_lower.find(kw)
            if idx != -1:
                prefix = title[:idx].strip().rstrip(",-:;")
                if not prefix:
                    suffix = title[idx + len(kw) :].strip().lstrip(",:; ")
                    if suffix:
                        name_tokens = suffix.split()
                        candidate: list[str] = []
                        for token in name_tokens:
                            if not token or token[0].islower():
                                break
                            candidate.append(token.strip(".,:;!?"))
                        if candidate:
                            return " ".join(candidate)
                else:
                    tokens = prefix.split()
                    name_tokens: list[str] = []
                    for token in reversed(tokens):
                        if not token or token[0].islower():
                            break
                        name_tokens.insert(0, token.strip(".,:;!?"))
                    if name_tokens:
                        return " ".join(name_tokens)

    for event_type in EVENT_PRIORITY:
        for kw in EVENT_KEYWORDS[event_type]:
            idx = title_lower.find(kw)
            if idx == -1:
                continue
            prefix = title[:idx].strip().rstrip(",-:;")
            if not prefix:
                continue
            tokens = prefix.split()
            name_tokens: list[str] = []
            for token in reversed(tokens):
                if not token or token[0].islower():
                    break
                name_tokens.insert(0, token.strip(".,:;!?"))
            if name_tokens:
                return " ".join(name_tokens)
    return None


def _find_name_candidates(text: str) -> list[tuple[str, int]]:
    return [(m.group(), m.start()) for m in _PLAYER_RE.finditer(text) if not _is_obviously_not_player(m.group())]


def _is_obviously_not_player(name: str) -> bool:
    lower = name.lower()
    non_player_phrases: set[str] = {
        "indian premier league",
        "cricket",
        "stadium",
        "training",
        "session",
        "announcement",
        "news",
        "update",
        "report",
    }
    return lower in non_player_phrases or name.isupper()


def extract_team_name(text: str) -> str | None:
    text_lower = text.lower()
    for canonical, variants in TEAM_NAMES.items():
        for variant in variants:
            if variant in text_lower:
                return canonical
    return None


def extract_injury_type(text: str) -> str | None:
    text_lower = text.lower()
    for injury, keywords in INJURY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return injury
    return None


def extract_replacement(text: str) -> str | None:
    text_lower = text.lower()
    idx = text_lower.find("replacement")
    if idx == -1:
        return None

    after = text[idx + len("replacement") :]
    for_key = after.lower().find("for")
    if for_key != -1:
        after_replacement = after[for_key + len("for") :]
        matches = list(_PLAYER_RE.finditer(after_replacement))
        if matches:
            return matches[0].group()

    before = text[:idx]
    matches = list(_PLAYER_RE.finditer(before))
    if matches:
        return matches[-1].group()
    return None


def _extract_replacement_signed_name(text: str) -> str | None:
    text_lower = text.lower()
    idx = text_lower.find("replacement")
    if idx == -1:
        return None

    before = text[:idx]

    for_pat = re.search(r"(?:signs|names|named)\s+", before, re.IGNORECASE)
    if for_pat:
        start = for_pat.end()
        candidates = list(_PLAYER_RE.finditer(before, start))
        if candidates:
            return candidates[0].group()
        after = text[idx + len("replacement") :]
        after_candidates = list(_PLAYER_RE.finditer(after))
        if after_candidates:
            return after_candidates[0].group()

    candidates = list(_PLAYER_RE.finditer(before, 0))
    if candidates:
        return candidates[-1].group()
    return None


def _find_nearest_name(fragment: str) -> str | None:
    matches = list(_PLAYER_RE.finditer(fragment))
    if not matches:
        return None
    center = len(fragment) // 2
    return min(matches, key=lambda m: abs(m.start() - center)).group()


def extract_effective_date(text: str, published_at: date) -> date | None:
    patterns: list[str] = [
        r"on\s+(\w+\s+\d{1,2},?\s+\d{4})",
        r"from\s+(\w+\s+\d{1,2},?\s+\d{4})",
        r"until\s+(\w+\s+\d{1,2},?\s+\d{4})",
        r"(\d{1,2}\s+\w+\s+\d{4})",
        r"(\w+\s+\d{1,2},?\s+\d{4})",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            date_str = m.group(1).replace(",", "")
            for fmt in ("%B %d %Y", "%d %B %Y", "%b %d %Y", "%d %b %Y"):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except (ValueError, TypeError):
                    continue
    return None


def determine_confidence(text: str, event_type: EventType | None = None) -> ConfidenceLevel:
    text_lower = text.lower()

    for phrase in HIGH_CONFIDENCE_PHRASES:
        if phrase in text_lower:
            return ConfidenceLevel.HIGH

    for phrase in LOW_CONFIDENCE_PHRASES:
        if phrase in text_lower:
            return ConfidenceLevel.LOW

    for phrase in MEDIUM_CONFIDENCE_PHRASES:
        if phrase in text_lower:
            return ConfidenceLevel.MEDIUM

    if event_type is not None:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def map_event_to_status(event_type: EventType) -> AvailabilityStatus:
    unavailable_types: set[EventType] = {
        EventType.INJURY,
        EventType.RULED_OUT,
        EventType.SUSPENSION,
        EventType.ILLNESS,
        EventType.NATIONAL_DUTY,
        EventType.RESTED,
        EventType.PERSONAL_LEAVE,
    }
    if event_type in unavailable_types:
        return AvailabilityStatus.UNAVAILABLE
    if event_type in {EventType.RECOVERY, EventType.AVAILABLE_AGAIN, EventType.REPLACEMENT_SIGNED}:
        return AvailabilityStatus.AVAILABLE
    return AvailabilityStatus.UNKNOWN
