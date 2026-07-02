from collections.abc import Sequence
from dataclasses import dataclass, field

from loguru import logger

from ..collectors.base import BaseCollector, RawData
from ..collectors.exceptions import CollectError
from ..db.repository import AbstractRepository
from ..domain.events import EventCreate
from ..normalizers.base import BaseNormalizer
from ..normalizers.exceptions import NormalizeError, UnresolvedPlayerError
from ..normalizers.mapper import normalized_to_event_create
from ..normalizers.models import NormalizedRecord
from ..normalizers.resolver import PlayerResolver
from ..parsers.base import BaseParser, ParsedRecord
from ..parsers.exceptions import ParseError


@dataclass
class PipelineResult:
    raw_count: int = 0
    parsed_count: int = 0
    normalized_count: int = 0
    stored_count: int = 0
    errors: list[str] = field(default_factory=list)
    event_type_counts: dict[str, int] = field(default_factory=dict)
    confidence_counts: dict[str, int] = field(default_factory=dict)
    team_counts: dict[str, int] = field(default_factory=dict)
    resolved_count: int = 0
    unresolved_count: int = 0


class AvailabilityPipeline:
    def __init__(
        self,
        collectors: Sequence[BaseCollector],
        parsers: Sequence[BaseParser],
        normalizers: Sequence[BaseNormalizer],
        repository: AbstractRepository,
        player_resolver: PlayerResolver | None = None,
    ) -> None:
        self._collectors = collectors
        self._parsers = parsers
        self._normalizers = normalizers
        self._repository = repository
        self._player_resolver = player_resolver

    def run(self) -> PipelineResult:
        result = PipelineResult()

        raw_data = self._collect(result)
        parsed = self._parse(raw_data, result)
        normalized = self._normalize(parsed, result)
        self._store(normalized, result)

        return result

    def _collect(self, result: PipelineResult) -> list[RawData]:
        all_raw: list[RawData] = []
        for collector in self._collectors:
            try:
                items = collector.collect()
                all_raw.extend(items)
                logger.info("Collected {} items from {}", len(items), collector.source_name)
            except CollectError as e:
                msg = f"Failed to collect from {collector.source_name}: {e}"
                logger.error(msg)
                result.errors.append(msg)
        result.raw_count = len(all_raw)
        return all_raw

    def _parse(
        self,
        raw_data: list[RawData],
        result: PipelineResult,
    ) -> list[ParsedRecord]:
        all_parsed: list[ParsedRecord] = []
        for raw in raw_data:
            for parser in self._parsers:
                if parser.can_handle(raw.source_name):
                    try:
                        records = parser.parse(raw)
                        all_parsed.extend(records)
                    except ParseError as e:
                        msg = f"Failed to parse from {raw.source_name}: {e}"
                        logger.error(msg)
                        result.errors.append(msg)
        result.parsed_count = len(all_parsed)
        return all_parsed

    def _normalize(
        self,
        records: list[ParsedRecord],
        result: PipelineResult,
    ) -> list[NormalizedRecord]:
        all_normalized: list[NormalizedRecord] = []
        for normalizer in self._normalizers:
            try:
                normalized = normalizer.normalize(records)
                all_normalized.extend(normalized)
                logger.info("Normalizer '{}' produced {} records", normalizer.name, len(normalized))
            except NormalizeError as e:
                msg = f"Normalizer '{normalizer.name}' failed: {e}"
                logger.error(msg)
                result.errors.append(msg)
        result.normalized_count = len(all_normalized)
        for nr in all_normalized:
            et = nr.event_type.value if nr.event_type else "unknown"
            result.event_type_counts[et] = result.event_type_counts.get(et, 0) + 1
            cl = nr.confidence.name if nr.confidence else "unknown"
            result.confidence_counts[cl] = result.confidence_counts.get(cl, 0) + 1
            if nr.team_name:
                result.team_counts[nr.team_name] = result.team_counts.get(nr.team_name, 0) + 1
        return all_normalized

    def _store(self, normalized: list[NormalizedRecord], result: PipelineResult) -> None:
        for nr in normalized:
            try:
                if self._player_resolver is not None:
                    event = normalized_to_event_create(nr, self._player_resolver)
                    result.resolved_count += 1
                else:
                    event = self._create_dummy_event(nr)
                self._repository.add_event(event)
                result.stored_count += 1
            except UnresolvedPlayerError as e:
                result.unresolved_count += 1
                logger.error("Unresolved player: {}", e)
                result.errors.append(str(e))
            except Exception as e:
                msg = f"Failed to store event: {e}"
                logger.error(msg)
                result.errors.append(msg)

    @staticmethod
    def _create_dummy_event(nr: NormalizedRecord) -> EventCreate:
        return EventCreate(
            player_id=0,
            event_type=nr.event_type,
            description=nr.title,
            source_name=nr.source_name,
            source_url=nr.source_url,
            confidence=nr.confidence,
            event_date=nr.effective_date or nr.published_at,
            start_date=nr.effective_date,
        )
