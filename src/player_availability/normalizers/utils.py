import re
from dataclasses import fields

from player_availability.domain.enums import ConfidenceLevel
from player_availability.parsers.patterns import COUNTRY_NAMES, GENERIC_NOUNS, PUBLISHER_NAMES

from .exceptions import ValidationError
from .models import NormalizedRecord

_PARENTHETICAL_RE = re.compile(r"\s*\([^)]*\)\s*$")


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def strip_parenthetical_suffix(text: str) -> str:
    return _PARENTHETICAL_RE.sub("", text).strip()


def to_proper_case(text: str) -> str:
    words = text.split()
    result: list[str] = []
    for word in words:
        if word.isupper() and len(word) <= 4:
            result.append(word)
        elif word.lower() in {"de", "da", "do", "du", "van", "der", "den", "la", "le", "el"}:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    return " ".join(result)


class InjuryNormalizer:
    def __init__(self) -> None:
        self._canonical_variants: list[tuple[str, list[str]]] = [
            ("Knee Injury", ["knee", "knee injury", "knee strain", "knee issue"]),
            (
                "Hamstring Injury",
                [
                    "hamstring",
                    "hamstring strain",
                    "hamstring tear",
                    "tight hamstring",
                    "hamstring injury",
                    "torn hamstring",
                ],
            ),
            ("Back Injury", ["back", "back injury", "back problem", "back spasm", "back strain"]),
            ("Groin Injury", ["groin", "groin strain", "groin injury"]),
            ("Ankle Injury", ["ankle", "ankle injury", "ankle sprain", "ankle twist"]),
            ("Shoulder Injury", ["shoulder", "shoulder injury", "dislocated shoulder"]),
            ("Calf Injury", ["calf", "calf strain", "calf injury"]),
            ("Quadriceps Injury", ["quad", "quadriceps", "quad strain"]),
            ("Side Strain", ["side strain", "intercostal"]),
            ("Finger Injury", ["finger", "finger injury", "broken finger"]),
            ("Concussion", ["concussion", "head injury"]),
            ("Elbow Injury", ["elbow", "elbow injury"]),
            ("Wrist Injury", ["wrist", "wrist injury", "wrist sprain"]),
        ]

    def normalize(self, injury_type: str) -> str | None:
        lower = injury_type.lower().strip()
        for canonical, variants in self._canonical_variants:
            if lower in variants:
                return canonical
        return to_proper_case(injury_type.strip())


def validate_record(record: NormalizedRecord) -> None:
    errors: list[str] = []

    if not record.player_name or not record.player_name.strip():
        errors.append("player_name is empty after normalization")

    if record.event_type is None:
        errors.append("event_type is None")

    if record.availability_status is None:
        errors.append("availability_status is None")

    if record.confidence is None:
        errors.append("confidence is None")

    if not record.source_name:
        errors.append("source_name is empty")

    player_lower = record.player_name.lower().strip() if record.player_name else ""
    if player_lower in PUBLISHER_NAMES:
        errors.append(f"player_name '{record.player_name}' matches a publisher name")
    if player_lower in GENERIC_NOUNS:
        errors.append(f"player_name '{record.player_name}' matches a generic noun")
    if player_lower in COUNTRY_NAMES:
        errors.append(f"player_name '{record.player_name}' matches a country name")

    if record.published_at is None:
        errors.append("published_at is None")

    if (
        record.replaced_player_name
        and record.player_name
        and record.replaced_player_name.lower().strip() == record.player_name.lower().strip()
    ):
        errors.append("replaced_player_name cannot be the same as player_name")

    if errors and record.confidence == ConfidenceLevel.LOW:
        errors.append("confidence is LOW, combined with other issues")

    if (
        record.replacement_player_name
        and record.player_name
        and record.replacement_player_name.lower().strip() == record.player_name.lower().strip()
    ):
        errors.append("replacement_player_name cannot be the same as player_name")

    if errors:
        raise ValidationError("; ".join(errors))


def count_non_none_fields(record: NormalizedRecord) -> int:
    return sum(1 for f in fields(record) if getattr(record, f.name) is not None)
