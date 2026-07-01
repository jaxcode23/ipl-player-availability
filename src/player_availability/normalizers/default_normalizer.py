from loguru import logger

from ..parsers.base import ParsedRecord
from .base import BaseNormalizer
from .deduplication import Deduplicator
from .exceptions import ValidationError
from .models import NormalizedRecord
from .player import PlayerNameNormalizer
from .team import TeamNameNormalizer
from .utils import InjuryNormalizer, validate_record


class DefaultNormalizer(BaseNormalizer):
    def __init__(
        self,
        player_normalizer: PlayerNameNormalizer | None = None,
        team_normalizer: TeamNameNormalizer | None = None,
        injury_normalizer: InjuryNormalizer | None = None,
        deduplicator: Deduplicator | None = None,
    ) -> None:
        self._player_normalizer = player_normalizer or PlayerNameNormalizer()
        self._team_normalizer = team_normalizer or TeamNameNormalizer()
        self._injury_normalizer = injury_normalizer or InjuryNormalizer()
        self._deduplicator = deduplicator or Deduplicator()

    @property
    def name(self) -> str:
        return "default"

    def normalize(self, records: list[ParsedRecord]) -> list[NormalizedRecord]:
        normalized: list[NormalizedRecord] = []
        for record in records:
            if not record.player_name:
                logger.warning("Skipping record with no player_name: {}", record.title)
                continue
            try:
                nr = self._normalize_one(record)
                normalized.append(nr)
            except ValidationError as e:
                logger.warning("Validation failed for '{}': {}", record.title, e)
            except Exception as e:
                logger.error("Unexpected error normalizing '{}': {}", record.title, e)
        return self._deduplicator.deduplicate(normalized)

    def _normalize_one(self, record: ParsedRecord) -> NormalizedRecord:
        player = self._player_normalizer.normalize(record.player_name)
        replaced = self._player_normalizer.normalize(record.replacement_player) if record.replacement_player else None
        team = self._team_normalizer.normalize(record.team_name) if record.team_name else None
        injury = self._injury_normalizer.normalize(record.injury_type) if record.injury_type else None

        nr = NormalizedRecord(
            player_name=player,
            event_type=record.event_type,
            availability_status=record.availability_status,
            confidence=record.confidence,
            source_name=record.source_name,
            source_url=record.url,
            published_at=record.published_at,
            effective_date=record.effective_date,
            team_name=team,
            injury_type=injury,
            replaced_player_name=replaced,
            replacement_player_name=None,
            title=record.title,
            body=record.body,
        )
        validate_record(nr)
        return nr
