from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from player_availability.db.base import Base
from player_availability.db.models import PlayerModel, TeamModel
from player_availability.db.seed import seed_database


@pytest.fixture
def test_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    yield session
    session.close()


def test_seed_database_idempotent(test_db_session):
    with patch("player_availability.db.seed.get_session") as mock_get_session:
        # Mock get_session to return our in-memory session inside a context manager
        mock_get_session.return_value.__enter__.return_value = test_db_session

        # First run: should insert everything
        seed_database()

        players_count_1 = test_db_session.query(PlayerModel).count()
        assert players_count_1 > 0

        # Second run: should be idempotent, no new players
        seed_database()

        players_count_2 = test_db_session.query(PlayerModel).count()
        assert players_count_1 == players_count_2


def test_seed_database_repairs_duplicates(test_db_session):
    with patch("player_availability.db.seed.get_session") as mock_get_session:
        mock_get_session.return_value.__enter__.return_value = test_db_session

        # Insert a team and duplicate players manually
        team = TeamModel(name="Chennai Super Kings", short_code="CSK")
        test_db_session.add(team)
        test_db_session.flush()

        # Add 3 instances of MS Dhoni
        test_db_session.add(PlayerModel(name="MS Dhoni", team_id=team.id, role="batter"))
        test_db_session.add(PlayerModel(name="MS Dhoni", team_id=team.id, role="batter"))
        test_db_session.add(PlayerModel(name="MS Dhoni", team_id=team.id, role="batter"))
        test_db_session.flush()

        assert test_db_session.query(PlayerModel).filter_by(name="MS Dhoni").count() == 3

        # Run seed_database which should repair the duplicates
        seed_database()

        # Should now only be 1 MS Dhoni
        assert test_db_session.query(PlayerModel).filter_by(name="MS Dhoni").count() == 1

        # And it should have updated the role to wicket_keeper as per PLAYER_SEED
        dhoni = test_db_session.query(PlayerModel).filter_by(name="MS Dhoni").first()
        assert dhoni.role == "wicket_keeper"
