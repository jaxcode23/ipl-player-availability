import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from player_availability.db.base import Base
from player_availability.db.models import PlayerModel, TeamModel
from player_availability.db.resolver import DbPlayerResolver


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()

    # Setup data
    team = TeamModel(name="Chennai Super Kings", short_code="CSK")
    session.add(team)
    session.flush()

    session.add_all(
        [
            PlayerModel(name="Virat Kohli", team_id=team.id, role="batter"),
            PlayerModel(name="MS Dhoni", team_id=team.id, role="wicket_keeper"),
            PlayerModel(name="T Natarajan", team_id=team.id, role="bowler"),
            PlayerModel(name="Faf du Plessis", team_id=team.id, role="batter"),
            PlayerModel(name="Mohammed Siraj", team_id=team.id, role="bowler"),
            PlayerModel(name="Suyash Sharma", team_id=team.id, role="bowler"),
            PlayerModel(name="Sandeep Sharma", team_id=team.id, role="bowler"),
        ]
    )
    session.flush()

    yield session
    session.close()


def test_resolver_exact_match(session):
    resolver = DbPlayerResolver(session)
    player_id = resolver.resolve("Virat Kohli")
    assert player_id is not None


def test_resolver_normalized_whitespace(session):
    resolver = DbPlayerResolver(session)
    # Testing extra spaces and case
    player_id = resolver.resolve("  viRat   KohLi ")
    assert player_id is not None


def test_resolver_normalized_punctuation(session):
    resolver = DbPlayerResolver(session)
    # Testing punctuation removal
    player_id = resolver.resolve("T. Natarajan")
    assert player_id is not None

    player_id_2 = resolver.resolve("Faf du-Plessis")
    assert player_id_2 is not None


def test_resolver_initial_form(session):
    resolver = DbPlayerResolver(session)
    player_id = resolver.resolve("V Kohli")
    assert player_id is not None

    player_id_2 = resolver.resolve("M Dhoni")
    assert player_id_2 is not None


def test_resolver_unique_surname(session):
    resolver = DbPlayerResolver(session)
    # Siraj is unique
    player_id = resolver.resolve("Siraj")
    assert player_id is not None


def test_resolver_ambiguous_fails_cleanly(session):
    resolver = DbPlayerResolver(session)
    # Both Suyash Sharma and Sandeep Sharma exist
    player_id = resolver.resolve("S Sharma")
    assert player_id is None

    player_id_2 = resolver.resolve("Sharma")
    assert player_id_2 is None


def test_resolver_unknown_fails_cleanly(session):
    resolver = DbPlayerResolver(session)
    player_id = resolver.resolve("Unknown Player")
    assert player_id is None


def test_resolver_wrong_team_retry_globally(session):
    """A player on CSK should resolve even when asked with wrong team."""
    resolver = DbPlayerResolver(session)
    player_id = resolver.resolve("Virat Kohli", team_name="Mumbai Indians")
    assert player_id is not None


def test_resolver_ambiguous_globally_still_fails(session):
    """Ambiguous name 'S Sharma' should still fail even with wrong team."""
    resolver = DbPlayerResolver(session)
    player_id = resolver.resolve("S Sharma", team_name="Mumbai Indians")
    assert player_id is None
