from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from player_availability.db.base import Base
from player_availability.db.models import PlayerModel, TeamModel
from player_availability.db.repository import SqlRepository
from player_availability.domain.enums import ConfidenceLevel, EventType, PlayerRole
from player_availability.domain.events import EventCreate


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(in_memory_db):
    SessionFactory = sessionmaker(bind=in_memory_db)
    session = SessionFactory()
    yield session
    session.close()


@pytest.fixture
def repository(session):
    return SqlRepository(session)


@pytest.fixture
def sample_team(session):
    team = TeamModel(name="Chennai Super Kings", short_code="CSK")
    session.add(team)
    session.flush()
    return team


@pytest.fixture
def sample_player(session, sample_team):
    player = PlayerModel(
        name="MS Dhoni",
        team_id=sample_team.id,
        role=PlayerRole.WICKET_KEEPER.value,
    )
    session.add(player)
    session.flush()
    return player


@pytest.fixture
def sample_event_create(sample_player):
    return EventCreate(
        player_id=sample_player.id,
        event_type=EventType.INJURY,
        description="Knee strain",
        source_name="manual",
        confidence=ConfidenceLevel.CONFIRMED,
        event_date=date(2026, 4, 1),
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 15),
    )
