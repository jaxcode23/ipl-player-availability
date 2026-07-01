#!/usr/bin/env python3
"""Initialize the database. Run from project root:

python scripts/init_db.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from loguru import logger

from player_availability.config import settings
from player_availability.db import models  # noqa: F401 — registers tables in Base.metadata
from player_availability.db.base import Base
from player_availability.db.session import engine
from player_availability.logging import setup_logging


def main() -> None:
    setup_logging()
    Base.metadata.create_all(engine)
    logger.info("Database initialized at {}", settings.database_url)


if __name__ == "__main__":
    main()
