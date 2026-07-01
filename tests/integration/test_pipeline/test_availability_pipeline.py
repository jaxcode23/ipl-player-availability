from datetime import date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from player_availability.collectors import MockCollector, SourceUnavailableError
from player_availability.collectors.base import RawData
from player_availability.parsers.exceptions import ParseError
from player_availability.normalizers.exceptions import NormalizeError
from player_availability.db.base import Base
from player_availability.db.models import PlayerModel, TeamModel
from player_availability.db.repository import SqlRepository
from player_availability.db.resolver import DbPlayerResolver
from player_availability.domain.enums import ConfidenceLevel, EventType
from player_availability.normalizers import DefaultNormalizer
from player_availability.parsers import ESPNCricinfoParser, IPLOfficialParser, MockParser
from player_availability.pipeline.availability_pipeline import AvailabilityPipeline


@pytest.fixture
def seeded_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()

    teams = {
        "CSK": TeamModel(name="Chennai Super Kings", short_code="CSK"),
        "MI": TeamModel(name="Mumbai Indians", short_code="MI"),
        "RCB": TeamModel(name="Royal Challengers Bengaluru", short_code="RCB"),
    }
    for t in teams.values():
        session.add(t)
    session.flush()

    session.add_all([
        PlayerModel(name="MS Dhoni", team_id=teams["CSK"].id, role="wicket_keeper"),
        PlayerModel(name="Virat Kohli", team_id=teams["RCB"].id, role="batter"),
        PlayerModel(name="Jasprit Bumrah", team_id=teams["MI"].id, role="bowler"),
        PlayerModel(name="Rohit Sharma", team_id=teams["MI"].id, role="batter"),
        PlayerModel(name="Hardik Pandya", team_id=teams["MI"].id, role="all_rounder"),
    ])
    session.flush()

    yield session
    session.close()


@pytest.fixture
def seeded_repository(seeded_session):
    return SqlRepository(seeded_session)


@pytest.fixture
def seeded_resolver(seeded_session):
    return DbPlayerResolver(seeded_session)


class TestAvailabilityPipeline:
    def test_empty_pipeline(self, seeded_repository):
        pipeline = AvailabilityPipeline(
            collectors=[],
            parsers=[],
            normalizers=[],
            repository=seeded_repository,
        )
        result = pipeline.run()
        assert result.raw_count == 0
        assert result.parsed_count == 0
        assert result.normalized_count == 0
        assert result.stored_count == 0
        assert result.errors == []

    def test_mock_data_end_to_end(self, seeded_repository, seeded_resolver, seeded_session):
        collectors = [MockCollector()]
        parsers = [IPLOfficialParser(), ESPNCricinfoParser(), MockParser()]
        normalizers = [DefaultNormalizer()]

        pipeline = AvailabilityPipeline(
            collectors=collectors,
            parsers=parsers,
            normalizers=normalizers,
            repository=seeded_repository,
            player_resolver=seeded_resolver,
        )

        result = pipeline.run()

        assert result.raw_count == 3
        assert result.parsed_count == 3
        assert result.normalized_count == 3
        assert result.stored_count == 3
        assert len(result.errors) == 0

        dhoni_id = seeded_session.query(PlayerModel).filter_by(name="MS Dhoni").one().id
        dhoni_events = seeded_repository.get_player_events(dhoni_id)
        assert len(dhoni_events) >= 1
        assert dhoni_events[-1].event_type == EventType.INJURY

        kohli_id = seeded_session.query(PlayerModel).filter_by(name="Virat Kohli").one().id
        kohli_events = seeded_repository.get_player_events(kohli_id)
        assert len(kohli_events) >= 1

        bumrah_id = seeded_session.query(PlayerModel).filter_by(name="Jasprit Bumrah").one().id
        bumrah_events = seeded_repository.get_player_events(bumrah_id)
        assert len(bumrah_events) >= 1
        assert bumrah_events[-1].event_type == EventType.RULED_OUT

    def test_pipeline_with_no_resolver_falls_back_to_dummy(self, seeded_repository):
        collectors = [MockCollector()]
        parsers = [IPLOfficialParser(), ESPNCricinfoParser(), MockParser()]
        normalizers = [DefaultNormalizer()]

        pipeline = AvailabilityPipeline(
            collectors=collectors,
            parsers=parsers,
            normalizers=normalizers,
            repository=seeded_repository,
            player_resolver=None,
        )

        result = pipeline.run()
        assert result.raw_count == 3
        assert result.stored_count >= 3
        for err in result.errors:
            assert "Could not resolve" not in err

    def test_pipeline_isolates_collector_failure(self, seeded_repository, seeded_resolver):

        class FailingCollector(MockCollector):
            @property
            def source_name(self):
                return "failing"

            def collect(self):
                raise SourceUnavailableError("Network error")

        collectors = [FailingCollector(), MockCollector()]
        parsers = [IPLOfficialParser(), ESPNCricinfoParser(), MockParser()]
        normalizers = [DefaultNormalizer()]

        pipeline = AvailabilityPipeline(
            collectors=collectors,
            parsers=parsers,
            normalizers=normalizers,
            repository=seeded_repository,
            player_resolver=seeded_resolver,
        )

        result = pipeline.run()

        assert any("Failed to collect" in err for err in result.errors)
        assert result.raw_count == 3
        assert result.stored_count == 3

    def test_pipeline_isolates_parser_failure(self, seeded_repository, seeded_resolver):

        class FailingParser(MockParser):
            @property
            def supported_source(self):
                return "mock"

            def parse(self, raw_data):
                raise ParseError("Parse crash")

        collectors = [MockCollector()]
        parsers = [FailingParser()]
        normalizers = [DefaultNormalizer()]

        pipeline = AvailabilityPipeline(
            collectors=collectors,
            parsers=parsers,
            normalizers=normalizers,
            repository=seeded_repository,
            player_resolver=seeded_resolver,
        )

        result = pipeline.run()

        assert len(result.errors) >= 1
        assert result.parsed_count == 0
        assert result.normalized_count == 0
        assert result.stored_count == 0

    def test_pipeline_isolates_normalizer_failure(self, seeded_repository, seeded_resolver):

        class CrashingNormalizer(DefaultNormalizer):
            @property
            def name(self):
                return "crashing"

            def normalize(self, records):
                raise NormalizeError("Normalizer crash")

        collectors = [MockCollector()]
        parsers = [IPLOfficialParser(), ESPNCricinfoParser(), MockParser()]
        normalizers = [CrashingNormalizer()]

        pipeline = AvailabilityPipeline(
            collectors=collectors,
            parsers=parsers,
            normalizers=normalizers,
            repository=seeded_repository,
            player_resolver=seeded_resolver,
        )

        result = pipeline.run()

        assert any("Normalizer" in err for err in result.errors)
        assert result.normalized_count == 0
        assert result.stored_count == 0

    def test_custom_mock_data(self, seeded_repository, seeded_resolver, seeded_session):
        items = [
            RawData(
                source_name="ipl_official",
                title="Shubman Gill suffers side strain",
                content=(
                    "<p>Gujarat Titans opener Shubman Gill has suffered a side strain"
                    " during a practice match and is expected to miss the next game.</p>"
                ),
                url="https://example.com/gill-injury",
                published_at=datetime(2026, 4, 5, 10, 0, 0),
            ),
            RawData(
                source_name="espn_cricinfo",
                title="Hardik Pandya cleared to play after fitness test",
                content=(
                    "<p>Mumbai Indians captain Hardik Pandya has been cleared to play"
                    " after passing a fitness test at the Wankhede Stadium.</p>"
                ),
                url="https://example.com/pandya-fit",
                published_at=datetime(2026, 4, 6, 14, 30, 0),
            ),
        ]

        teams = {
            "GT": seeded_session.query(TeamModel).filter_by(short_code="GT").first(),
            "MI": seeded_session.query(TeamModel).filter_by(short_code="MI").first(),
        }
        if not teams["GT"]:
            gt = TeamModel(name="Gujarat Titans", short_code="GT")
            seeded_session.add(gt)
            seeded_session.flush()
            teams["GT"] = gt

        gill = seeded_session.query(PlayerModel).filter_by(name="Shubman Gill").first()
        if not gill:
            gill = PlayerModel(name="Shubman Gill", team_id=teams["GT"].id, role="batter")
            seeded_session.add(gill)
            seeded_session.flush()

        hardik = seeded_session.query(PlayerModel).filter_by(name="Hardik Pandya").first()
        if not hardik:
            hardik = PlayerModel(name="Hardik Pandya", team_id=teams["MI"].id, role="all_rounder")
            seeded_session.add(hardik)
            seeded_session.flush()

        collector = MockCollector(items)
        parsers = [IPLOfficialParser(), ESPNCricinfoParser(), MockParser()]
        normalizers = [DefaultNormalizer()]

        pipeline = AvailabilityPipeline(
            collectors=[collector],
            parsers=parsers,
            normalizers=normalizers,
            repository=seeded_repository,
            player_resolver=seeded_resolver,
        )

        result = pipeline.run()
        assert result.stored_count >= 2
        assert result.errors == []

        gill_id = seeded_session.query(PlayerModel).filter_by(name="Shubman Gill").one().id
        gill_events = seeded_repository.get_player_events(gill_id)
        assert len(gill_events) >= 1
        assert gill_events[-1].event_type == EventType.INJURY

    def test_unresolved_player_logged_as_error(self, seeded_repository, seeded_session):
        items = [
            RawData(
                source_name="ipl_official",
                title="Unknown Player out of IPL",
                content="<p>Unknown Player has been ruled out of IPL 2026.</p>",
                url="https://example.com/unknown",
                published_at=datetime(2026, 4, 7, 12, 0, 0),
            ),
        ]

        collector = MockCollector(items)
        parsers = [IPLOfficialParser(), ESPNCricinfoParser(), MockParser()]
        normalizers = [DefaultNormalizer()]
        resolver = DbPlayerResolver(seeded_session)

        pipeline = AvailabilityPipeline(
            collectors=[collector],
            parsers=parsers,
            normalizers=normalizers,
            repository=seeded_repository,
            player_resolver=resolver,
        )

        result = pipeline.run()

        assert result.parsed_count >= 1
        assert result.normalized_count >= 1
        assert result.stored_count == 0
        assert any("Could not resolve" in err for err in result.errors)

    def test_db_player_resolver_resolves_known_players(self, seeded_session):
        resolver = DbPlayerResolver(seeded_session)

        dhoni_id = resolver.resolve("MS Dhoni", "Chennai Super Kings")
        assert dhoni_id is not None

        kohli_id = resolver.resolve("Virat Kohli", "Royal Challengers Bengaluru")
        assert kohli_id is not None

        dhoni_no_team = resolver.resolve("MS Dhoni")
        assert dhoni_no_team is not None
        assert dhoni_no_team == dhoni_id

    def test_db_player_resolver_returns_none_for_unknown(self, seeded_session):
        resolver = DbPlayerResolver(seeded_session)
        assert resolver.resolve("Nonexistent Player") is None
        assert resolver.resolve("MS Dhoni", "Nonexistent Team") is None
