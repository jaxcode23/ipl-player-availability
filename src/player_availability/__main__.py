from __future__ import annotations

import argparse
from datetime import date

from loguru import logger

from .db import models  # noqa: F401 — registers tables in Base.metadata
from .db.base import Base
from .db.session import engine, get_session
from .logging import setup_logging


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(prog="player-availability")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create all database tables and seed with sample data")

    run_pp = subparsers.add_parser("run-pipeline", help="Run the full collection pipeline")
    run_pp.add_argument(
        "--use-mock",
        action="store_true",
        help="Use mock article data instead of live RSS feeds",
    )

    add_ev = subparsers.add_parser("add-event", help="Manually record an availability event")
    add_ev.add_argument("--player-id", type=int, required=True)
    add_ev.add_argument(
        "--event-type",
        required=True,
        choices=[
            "injury",
            "recovery",
            "ruled_out",
            "replacement_signed",
            "suspension",
            "illness",
            "national_duty",
            "rested",
            "personal_leave",
            "available_again",
        ],
    )
    add_ev.add_argument("--description", type=str, default=None)
    add_ev.add_argument("--source", type=str, default="manual")
    add_ev.add_argument("--event-date", type=str, default=None)
    add_ev.add_argument("--start-date", type=str, default=None)
    add_ev.add_argument("--end-date", type=str, default=None)

    args = parser.parse_args()

    if args.command == "init-db":
        _handle_init_db()
    elif args.command == "run-pipeline":
        _handle_run_pipeline(args)
    elif args.command == "add-event":
        _handle_add_event(args)


def _handle_init_db() -> None:
    from .db.seed import seed_database

    Base.metadata.create_all(engine)
    logger.info("Database tables created")
    seed_database()
    logger.info("Database initialization complete")


def _handle_run_pipeline(args: argparse.Namespace) -> None:
    from .collectors import MockCollector
    from .config import settings
    from .db.repository import SqlRepository
    from .db.resolver import DbPlayerResolver
    from .normalizers import DefaultNormalizer
    from .parsers import GenericArticleParser, MockParser
    from .pipeline.availability_pipeline import AvailabilityPipeline

    Base.metadata.create_all(engine)
    logger.info("Database tables ready")

    collectors = []
    if args.use_mock:
        logger.info("Using mock collector (no live RSS)")
        collectors.append(MockCollector())
    else:
        for source in settings.source_registry:
            if source.is_active:
                try:
                    collector = _build_collector(source)
                    if collector is not None:
                        collectors.append(collector)
                        logger.info("Registered collector: {} -> {}", source.name, source.base_url)
                except Exception as e:
                    logger.error("Failed to register collector '{}': {}", source.name, e)

        if not collectors:
            logger.warning("No live collectors could be registered; falling back to mock")
            collectors.append(MockCollector())

    parsers = [MockParser()]
    for source in settings.source_registry:
        if source.is_active:
            parsers.append(GenericArticleParser(source_name=source.name))
    normalizers = [DefaultNormalizer()]

    with get_session() as session:
        repo = SqlRepository(session)
        resolver = DbPlayerResolver(session)
        pipeline = AvailabilityPipeline(
            collectors=collectors,
            parsers=parsers,
            normalizers=normalizers,
            repository=repo,
            player_resolver=resolver,
        )

        logger.info("Starting pipeline run")
        result = pipeline.run()

        _print_pipeline_result(result)


def _build_collector(source) -> object | None:
    from .collectors import GenericRSSCollector

    mechanism = getattr(source, "mechanism", source.type)
    if mechanism == "rss":
        return GenericRSSCollector(
            source_name=source.name,
            url=source.base_url,
            fetch_full_article=getattr(source, "fetch_full_article", False),
        )
    logger.warning("Unknown mechanism '{}' for source '{}', skipping", mechanism, source.name)
    return None


def _print_pipeline_result(result) -> None:
    separator = "-" * 60
    logger.info(separator)
    logger.info("Pipeline Run Complete")
    logger.info(separator)
    logger.info("  Raw articles collected : {}", result.raw_count)
    logger.info("  Records parsed         : {}", result.parsed_count)
    logger.info("  Records normalized     : {}", result.normalized_count)
    logger.info("  Events stored          : {}", result.stored_count)
    logger.info("  Players resolved       : {}", result.resolved_count)
    logger.info("  Players unresolved     : {}", result.unresolved_count)
    if result.event_type_counts:
        logger.info("  By event type:")
        for et, cnt in sorted(result.event_type_counts.items()):
            logger.info("    {:25s}: {}", et.replace("_", " ").title(), cnt)
    if result.confidence_counts:
        logger.info("  By confidence:")
        for cl, cnt in sorted(result.confidence_counts.items()):
            logger.info("    {:25s}: {}", cl.title(), cnt)
    if result.team_counts:
        logger.info("  By team:")
        for team, cnt in sorted(result.team_counts.items()):
            logger.info("    {:25s}: {}", team, cnt)
    if result.errors:
        logger.info("  Errors ({}):", len(result.errors))
        for i, err in enumerate(result.errors, 1):
            logger.info("    {}. {}", i, err)
    else:
        logger.info("  Errors                 : 0 (clean run)")
    logger.info(separator)


def _handle_add_event(args: argparse.Namespace) -> None:
    from .db.repository import SqlRepository
    from .domain.enums import ConfidenceLevel, EventType
    from .domain.events import EventCreate

    event = EventCreate(
        player_id=args.player_id,
        event_type=EventType(args.event_type),
        description=args.description,
        source_name=args.source,
        source_url=None,
        confidence=ConfidenceLevel.CONFIRMED if args.source == "manual" else ConfidenceLevel.MEDIUM,
        event_date=date.fromisoformat(args.event_date) if args.event_date else date.today(),
        start_date=date.fromisoformat(args.start_date) if args.start_date else None,
        end_date=date.fromisoformat(args.end_date) if args.end_date else None,
    )

    with get_session() as session:
        repo = SqlRepository(session)
        created = repo.add_event(event)
        logger.info("Created event #{} for player {}", created.id, created.player_id)


if __name__ == "__main__":
    main()
