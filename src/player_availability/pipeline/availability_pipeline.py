from collections.abc import Sequence
from dataclasses import dataclass, field

from loguru import logger

from ..collectors.base import BaseCollector, RawData
from ..collectors.exceptions import CollectError
from ..db.repository import AbstractRepository
from ..domain.events import EventCreate
from ..normalizers.base import BaseNormalizer
from ..normalizers.exceptions import NormalizeError
from ..parsers.base import BaseParser, ParsedRecord
from ..parsers.exceptions import ParseError


@dataclass
class PipelineResult:
    raw_count: int = 0
    parsed_count: int = 0
    normalized_count: int = 0
    stored_count: int = 0
    errors: list[str] = field(default_factory=list)


class AvailabilityPipeline:
    def __init__(
        self,
        collectors: Sequence[BaseCollector],
        parsers: Sequence[BaseParser],
        normalizers: Sequence[BaseNormalizer],
        repository: AbstractRepository,
    ) -> None:
        self._collectors = collectors
        self._parsers = parsers
        self._normalizers = normalizers
        self._repository = repository

    def run(self) -> PipelineResult:
        result = PipelineResult()

        raw_data = self._collect(result)
        parsed = self._parse(raw_data, result)
        events = self._normalize(parsed, result)
        self._store(events, result)

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
    ) -> list[EventCreate]:
        all_events: list[EventCreate] = []
        for normalizer in self._normalizers:
            try:
                events = normalizer.normalize(records)
                all_events.extend(events)
                logger.info("Normalizer '{}' produced {} events", normalizer.name, len(events))
            except NormalizeError as e:
                msg = f"Normalizer '{normalizer.name}' failed: {e}"
                logger.error(msg)
                result.errors.append(msg)
        result.normalized_count = len(all_events)
        return all_events

    def _store(self, events: list[EventCreate], result: PipelineResult) -> None:
        for event in events:
            try:
                self._repository.add_event(event)
                result.stored_count += 1
            except Exception as e:
                msg = f"Failed to store event: {e}"
                logger.error(msg)
                result.errors.append(msg)
