from dataclasses import dataclass
from datetime import date

from ..domain.enums import EventType
from .models import NormalizedRecord
from .utils import count_non_none_fields


@dataclass(frozen=True)
class DedupKey:
    player_name: str
    event_type: EventType
    source_name: str
    effective_date: date | None


class Deduplicator:
    def deduplicate(self, records: list[NormalizedRecord]) -> list[NormalizedRecord]:
        best: dict[DedupKey, NormalizedRecord] = {}
        insertion_order: list[DedupKey] = []

        for rec in records:
            key = DedupKey(
                player_name=rec.player_name.lower().strip(),
                event_type=rec.event_type,
                source_name=rec.source_name,
                effective_date=rec.effective_date or rec.published_at,
            )
            existing = best.get(key)
            if existing is None:
                best[key] = rec
                insertion_order.append(key)
            else:
                winner = self._pick_best(existing, rec)
                if winner is rec:
                    best[key] = rec

        return [best[k] for k in insertion_order]

    @staticmethod
    def _pick_best(a: NormalizedRecord, b: NormalizedRecord) -> NormalizedRecord:
        if a.confidence.value > b.confidence.value:
            return a
        if b.confidence.value > a.confidence.value:
            return b
        if count_non_none_fields(a) >= count_non_none_fields(b):
            return a
        return b
