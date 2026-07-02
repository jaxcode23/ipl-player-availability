import re
from datetime import date, datetime

from loguru import logger

from ..collectors.base import RawData
from ..domain.enums import AvailabilityStatus, ConfidenceLevel, EventType
from .base import ParsedRecord
from .patterns import (
    COUNTRY_NAMES,
    EVENT_FRAGMENTS,
    EVENT_KEYWORDS,
    EVENT_PRIORITY,
    GENERIC_NOUNS,
    HEADLINE_BOILERPLATE,
    HEADLINE_FRAGMENTS,
    HIGH_CONFIDENCE_PHRASES,
    INJURY_KEYWORDS,
    LOW_CONFIDENCE_PHRASES,
    MEDIUM_CONFIDENCE_PHRASES,
    PUBLISHER_NAMES,
    REGION_NAMES,
    TEAM_NAMES,
)
from .utils import clean_html

# Tokens stripped only during prefix/suffix cleanup (not in global validation)
# to avoid false positives on words that can appear in legitimate contexts.
_CLEANUP_TOKEN_SET: set[str] = {"bad"}

# Build set of team word fragments for partial team name rejection.
# Catches cases like "Kings" (from "super kings", "punjab kings") or
# "Indians" (from "mumbai indians") that aren't caught by exact variant match.
_TEAM_WORD_FRAGMENTS: set[str] = set()
for _variants in TEAM_NAMES.values():
    for _variant in _variants:
        for _word in _variant.split():
            if len(_word) > 3:
                _TEAM_WORD_FRAGMENTS.add(_word.lower())

_PLAYER_RE = re.compile(r"(?:[A-Z]{1,2}\.?\s+)?[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2}")

# Reusable player name regex fragment (matches names like "MS Dhoni", "V Kohli", "Virat Kohli")
_PLAYER_NAME = r"(?:[A-Z]{1,2}\.?\s+)?[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2}"

# Replacement extraction patterns: captures (incoming_player, outgoing_player)
_REPLACEMENT_PAIR_PATTERNS: list[tuple[str, str, str]] = [
    # "X replaces Y" or "X replaces Y as replacement"
    (f"(?P<in>{_PLAYER_NAME})\\s+replaces\\s+(?P<out>{_PLAYER_NAME})(?:\\s+as|\\s+in|$|\\.|,|\\s)", "in", "out"),
    # "[Team] signs/named [incoming] as replacement for [outgoing]"  (verb THEN incoming)
    (
        f"(?:[A-Z]{{2,}}\\s+)?(?:sign(?:s|ned)|nam(?:es|ed)|ropes?)\\s+(?P<in>{_PLAYER_NAME})\\s+as\\s+(?:a\\s+)?replacement\\s+for\\s+(?P<out>{_PLAYER_NAME})",
        "in",
        "out",
    ),
    # "[Team] brings/drafts/calls in [incoming] for [outgoing]"
    (
        f"(?:[A-Z]{{2,}}\\s+)?(?:brings?|brought|drafts?|drafted|calls?|called)\\s+in\\s+(?P<in>{_PLAYER_NAME})\\s+for\\s+(?P<out>{_PLAYER_NAME})",
        "in",
        "out",
    ),
    # "replacement for Y: X" or "replacement for Y — X" (separator is REQUIRED)
    (f"replacement\\s+for\\s+(?P<out>{_PLAYER_NAME})\\s*[:–—]\\s*(?P<in>{_PLAYER_NAME})", "in", "out"),
]


def _extend_to_word_boundary(text: str, pos: int, side: str = "right") -> int:
    if pos <= 0 or pos >= len(text):
        return pos
    if side == "right":
        while pos < len(text) and text[pos].isalpha():
            pos += 1
    else:
        while pos > 0 and text[pos - 1].isalpha():
            pos -= 1
    return pos


def _tokenize_phrase(phrase: str) -> list[str]:
    return phrase.split()


def _match_prefix(tokens: list[str], phrases: set[str]) -> int:
    for phrase in phrases:
        pts = _tokenize_phrase(phrase)
        n = len(pts)
        if n <= len(tokens) and all(t.lower() == pt for t, pt in zip(tokens[:n], pts)):
            return n
    return 0


def _match_suffix(tokens: list[str], phrases: set[str]) -> int:
    for phrase in phrases:
        pts = _tokenize_phrase(phrase)
        n = len(pts)
        if n <= len(tokens) and all(t.lower() == pt for t, pt in zip(tokens[-n:], pts)):
            return n
    return 0


def _clean_player_name(name: str) -> str | None:
    if not name:
        return None
    tokens = name.split()
    if not tokens:
        return None

    # Pre-compute single-token lookup sets
    headline_lower: set[str] = HEADLINE_FRAGMENTS
    country_lower: set[str] = COUNTRY_NAMES
    region_lower: set[str] = REGION_NAMES
    publisher_single: set[str] = {p for p in PUBLISHER_NAMES if " " not in p}
    event_single: set[str] = {p for p in EVENT_FRAGMENTS if " " not in p}
    publisher_multi: set[str] = {p for p in PUBLISHER_NAMES if " " in p}
    region_multi: set[str] = {p for p in REGION_NAMES if " " in p}
    boilerplate_multi: set[str] = {p for p in HEADLINE_BOILERPLATE if " " in p}
    event_multi: set[str] = {p for p in EVENT_FRAGMENTS if " " in p}

    _SINGLE_PREFIX: set[str] = (
        headline_lower | country_lower | region_lower | publisher_single | event_single | _CLEANUP_TOKEN_SET
    )
    _SINGLE_SUFFIX: set[str] = headline_lower | event_single | _CLEANUP_TOKEN_SET
    _MULTI_PREFIX: set[str] = boilerplate_multi | event_multi | publisher_multi | region_multi
    _MULTI_SUFFIX: set[str] = event_multi

    changed = True
    while changed:
        changed = False

        # --- Strip prefix ---
        while tokens:
            n = _match_prefix(tokens, _MULTI_PREFIX)
            if n:
                tokens = tokens[n:]
                changed = True
                continue
            if tokens[0].lower() in _SINGLE_PREFIX:
                tokens.pop(0)
                changed = True
                continue
            break

        if not tokens:
            break

        # --- Strip suffix ---
        while tokens:
            n = _match_suffix(tokens, _MULTI_SUFFIX)
            if n:
                tokens = tokens[:-n]
                changed = True
                continue
            if tokens[-1].lower() in _SINGLE_SUFFIX:
                tokens.pop(-1)
                changed = True
                continue
            break

    if not tokens:
        return None
    return " ".join(tokens)


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
        window_start = max(0, kw_start - 120)
        window_end = min(len(combined), kw_end + 120)
        window_start = _extend_to_word_boundary(combined, window_start, side="left")
        window_end = _extend_to_word_boundary(combined, window_end, side="right")
        context = combined[window_start:window_end]

        player: str | None = None
        replacement: str | None = None

        if event_type == EventType.REPLACEMENT_SIGNED:
            pair = _extract_replacement_pair(combined)
            if pair is not None:
                player, replacement = pair
            if player is None:
                player = _extract_replacement_signed_name(combined)
            if replacement is None:
                replacement = extract_replacement(context) or extract_replacement(combined)

        if player is None:
            player = _find_nearest_name(context)
        if player is None:
            player = extract_player_name_from_title(raw_data.title, event_type)
        if player is None:
            continue
        # Clean the candidate name (strip noise prefixes/suffixes)
        player = _clean_player_name(player)
        if player is None:
            logger.debug("Rejected player candidate (no valid name after cleanup)")
            continue
        if not _is_valid_player_candidate(player):
            continue

        key = (player.lower(), event_type)
        if key in seen:
            continue
        seen.add(key)

        if replacement and player and replacement.lower() == player.lower():
            replacement = None
        team_name = extract_team_name(context) or extract_team_name(combined)
        injury_type = extract_injury_type(context)
        if replacement is None:
            replacement = extract_replacement(context) or extract_replacement(combined)
        if replacement and player and replacement.lower() == player.lower():
            replacement = None
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
    raw_candidates = _find_name_candidates(text)
    if not raw_candidates:
        return None

    # Clean candidates (strip noise prefixes/suffixes)
    candidates: list[tuple[str, int]] = []
    for name, pos in raw_candidates:
        cleaned = _clean_player_name(name)
        if cleaned is not None:
            candidates.append((cleaned, pos))

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


_CRICKET_CONTEXT_TERMS: set[str] = {
    "ipl",
    "bowler",
    "batsman",
    "batter",
    "all-rounder",
    "wicket-keeper",
    "captain",
    "vice-captain",
    "franchise",
    "cricket",
    "match",
    "team",
    "squad",
    "playing xi",
    "eleven",
    "innings",
    "over",
    "run",
    "wicket",
    "stadium",
    "ground",
    "training",
    "net session",
    "practice",
    "player",
    "star",
    "opener",
    "spinner",
    "fast bowler",
    "paceman",
}


def _is_team_name_exact(lower: str) -> bool:
    for canonical, variants in TEAM_NAMES.items():
        if lower == canonical.lower():
            return True
        for variant in variants:
            if lower == variant:
                return True
    # Reject single-word candidates that match a ≥4-char word
    # within any team variant (catches "kings", "indians", "titans", etc.)
    if lower in _TEAM_WORD_FRAGMENTS:
        return True
    return False


def _is_valid_player_candidate(name: str) -> bool:
    if len(name.strip()) < 2 or len(name) > 40:
        logger.debug("Rejected player candidate '{}' (invalid length)", name)
        return False
    if name.isupper():
        logger.debug("Rejected player candidate '{}' (all uppercase)", name)
        return False
    if not _has_capitalized_word(name):
        logger.debug("Rejected player candidate '{}' (no capitalized word)", name)
        return False
    lower = name.lower()
    if lower in PUBLISHER_NAMES:
        logger.debug("Rejected player candidate '{}' (publisher name)", name)
        return False
    if lower in GENERIC_NOUNS:
        logger.debug("Rejected player candidate '{}' (generic noun)", name)
        return False
    if lower in COUNTRY_NAMES:
        logger.debug("Rejected player candidate '{}' (country name)", name)
        return False
    if lower in HEADLINE_FRAGMENTS:
        logger.debug("Rejected player candidate '{}' (headline fragment)", name)
        return False
    if lower in REGION_NAMES:
        logger.debug("Rejected player candidate '{}' (region name)", name)
        return False
    if lower in HEADLINE_BOILERPLATE:
        logger.debug("Rejected player candidate '{}' (headline boilerplate)", name)
        return False
    if _is_team_name_exact(lower):
        logger.debug("Rejected player candidate '{}' (team name)", name)
        return False
    return True


def _has_capitalized_word(name: str) -> bool:
    return any(word and word[0].isupper() for word in name.split())


def _find_name_candidates(text: str) -> list[tuple[str, int]]:
    return [(m.group(), m.start()) for m in _PLAYER_RE.finditer(text) if not _is_obviously_not_player(m.group())]


def _is_obviously_not_player(name: str) -> bool:
    if not _is_valid_player_candidate(name):
        return True
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
        "ma chidambaram stadium",
        "m chidambaram stadium",
        "wankhede stadium",
        "chinnaswamy stadium",
        "eden gardens",
        "arun jaitley stadium",
        "narendra modi stadium",
        "rajiv gandhi stadium",
        "sawai mansingh stadium",
        "pca stadium",
        "holkar stadium",
    }
    if lower in non_player_phrases:
        return True
    for team_variants in TEAM_NAMES.values():
        for variant in team_variants:
            if _word_in_text(variant, lower) and lower == variant:
                return True
    for canonical in TEAM_NAMES:
        if lower == canonical.lower():
            return True
    return False


def extract_team_name(text: str) -> str | None:
    text_lower = text.lower()
    for canonical, variants in TEAM_NAMES.items():
        for variant in variants:
            if _word_in_text(variant, text_lower):
                return canonical
    return None


def _word_in_text(word: str, text_lower: str) -> bool:
    if len(word) <= 3:
        idx = text_lower.find(word)
        while idx != -1:
            before = idx == 0 or not text_lower[idx - 1].isalpha()
            after_pos = idx + len(word)
            after = after_pos >= len(text_lower) or not text_lower[after_pos].isalpha()
            if before and after:
                return True
            idx = text_lower.find(word, idx + 1)
        return False
    return word in text_lower


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
        return None

    of_key = after.lower().find("of ")
    if of_key != -1:
        after_of = after[of_key + len("of ") :]
        matches = list(_PLAYER_RE.finditer(after_of))
        if matches:
            return matches[0].group()
        return None

    return None


_all_player_patterns_compiled = [
    (re.compile(pat), in_group, out_group) for pat, in_group, out_group in _REPLACEMENT_PAIR_PATTERNS
]


def _extract_replacement_pair(text: str) -> tuple[str | None, str | None]:
    for compiled, in_group, out_group in _all_player_patterns_compiled:
        m = compiled.search(text)
        if m:
            incoming = m.group(in_group)
            outgoing = m.group(out_group)
            if incoming and outgoing and incoming.lower() != outgoing.lower():
                return incoming, outgoing
    return None, None


def _extract_replacement_signed_name(text: str) -> str | None:
    text_lower = text.lower()
    idx = text_lower.find("replacement")
    if idx == -1:
        return None

    before = text[:idx]

    for_pat = re.search(r"(?:signs?|names|named|brings?|drafts?|ropes?|calls?)\s+", before, re.IGNORECASE)
    if for_pat:
        before_verb = before[: for_pat.start()]
        candidates = list(_PLAYER_RE.finditer(before_verb))
        if candidates:
            return candidates[-1].group()

    candidates = list(_PLAYER_RE.finditer(before))
    if candidates:
        return candidates[-1].group()

    after = text[idx + len("replacement") :]
    after_candidates = list(_PLAYER_RE.finditer(after))
    if after_candidates:
        return after_candidates[0].group()
    return None


def _find_nearest_name(fragment: str) -> str | None:
    candidates: list[tuple[str, int]] = []
    for m in _PLAYER_RE.finditer(fragment):
        name = m.group()
        cleaned = _clean_player_name(name)
        if cleaned is None:
            continue
        if _is_obviously_not_player(cleaned):
            continue
        candidates.append((cleaned, m.start()))
    if not candidates:
        return None
    center = len(fragment) // 2
    fragment_lower = fragment.lower()
    scored: list[tuple[str, float]] = []
    for name, pos in candidates:
        dist = abs(pos - center)
        score = float(dist)
        for term in _CRICKET_CONTEXT_TERMS:
            idx = fragment_lower.find(term)
            if idx != -1:
                term_dist = abs(pos - idx)
                if term_dist < 80:
                    score -= 60.0
                    break
        if any(word[0].isupper() and len(word) > 1 and word[0].isupper() for word in name.split()):
            pass
        if _INDIVIDUAL_PLAYER_INDICATORS.search(name):
            score -= 40.0
        scored.append((name, score))
    scored.sort(key=lambda x: x[1])
    return scored[0][0] if scored else None


_INDIVIDUAL_PLAYER_INDICATORS = re.compile(
    r"\b(?:Smith|Kohli|Dhoni|Sharma|Bumrah|Rahul|Pant|Gill|Pandya|Jadeja|"
    r"Yadav|Ashwin|Shami|Dhawan|Chahal|Warner|Buttler|Maxwell|Russell|Narine|"
    r"Khan|Curran|Stokes|Archer|Rabada|Boult|Samson|Iyer|Kishan|Karthik|"
    r"Conway|Marsh|Green|David|Ali|Dube|Patidar|Rana|Shaw|Chahar|"
    r"Natarajan|Malik|Rinku|Tilak|Samad|Shahbaz|Sundar|Sudharsan|"
    r"Jaiswal|Parag|Jurel|Patel|Gaikwad|Rahane|Ravindra|Mitchell|"
    r"Theekshana|Pathirana|Mustafizur|Thakur|Deshpande|Solanki|"
    r"Suryakumar|Ishan|Hardik|Rohit|Virat|Shubman|Rishabh|"
    r"Head|Klaasen|Salt|Starc|Nortje|Ferguson|Wood|"
    r"Coetzee|Madhwal|Mhatre|Akash|Gerald)\b",
    re.IGNORECASE,
)


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
