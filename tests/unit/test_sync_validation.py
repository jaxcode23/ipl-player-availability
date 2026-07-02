import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from player_availability.db.base import Base
from player_availability.db.resolver import DbPlayerResolver
from player_availability.db.seed import PLAYER_SEED, seed_database
from player_availability.normalizers.player import PlayerAliasRegistry


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()

    import unittest.mock

    with unittest.mock.patch("player_availability.db.seed.get_session") as mock_get_session:
        mock_get_session.return_value.__enter__.return_value = session
        seed_database()

    yield session
    session.close()


def test_every_canonical_alias_exists_in_seed():
    registry = PlayerAliasRegistry()
    seeded_names_lower = {p[0].lower().strip() for p in PLAYER_SEED}

    orphaned = []
    for canonical_key in registry._canonical_lower:
        if canonical_key not in seeded_names_lower:
            orphaned.append(canonical_key)

    assert not orphaned, f"Canonical aliases not in seed: {orphaned}"


def test_every_seeded_player_can_be_resolved(session):
    resolver = DbPlayerResolver(session)

    unresolved = []
    for name, _, _, _ in PLAYER_SEED:
        player_id = resolver.resolve(name)
        if player_id is None:
            unresolved.append(name)

    assert not unresolved, f"Seeded players that cannot be resolved: {unresolved}"


def test_resolver_lookup_succeeds_for_canonical_names(session):
    resolver = DbPlayerResolver(session)
    registry = PlayerAliasRegistry()

    # Actually registry._alias_to_canonical values are the canonical names
    canonical_names = set(registry._alias_to_canonical.values())

    unresolved = []
    for canonical_name in canonical_names:
        player_id = resolver.resolve(canonical_name)
        if player_id is None:
            unresolved.append(canonical_name)

    assert not unresolved, f"Registry canonical names that cannot be resolved: {unresolved}"
