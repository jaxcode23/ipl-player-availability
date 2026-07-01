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

    subparsers.add_parser("init-db", help="Create all database tables")

    subparsers.add_parser("run-pipeline", help="Run the full collection pipeline")

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
        Base.metadata.create_all(engine)
        logger.info("Database tables created")

    elif args.command == "run-pipeline":
        logger.info("Pipeline execution not yet implemented")

    elif args.command == "add-event":
        _handle_add_event(args)


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
