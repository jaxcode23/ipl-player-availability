from datetime import date

from player_availability.domain.enums import ConfidenceLevel, EventType
from player_availability.domain.events import EventCreate


class TestSqlRepository:
    def test_add_event(self, repository, sample_event_create):
        event = repository.add_event(sample_event_create)
        assert event.id is not None
        assert event.event_type == EventType.INJURY
        assert event.player_id == sample_event_create.player_id
        assert event.source_name == "manual"

    def test_get_player_events(self, repository, sample_event_create, sample_player):
        repository.add_event(sample_event_create)
        events = repository.get_player_events(sample_player.id)
        assert len(events) == 1
        assert events[0].event_type == EventType.INJURY

    def test_get_current_status_unavailable(self, repository, sample_event_create, sample_player):
        repository.add_event(sample_event_create)
        status = repository.get_current_status(sample_player.id)
        assert status.status == "unavailable"
        assert "Knee strain" in status.reason

    def test_get_current_status_available(self, repository, sample_player):
        status = repository.get_current_status(sample_player.id)
        assert status.status == "available"

    def test_get_all_current_statuses(self, repository, sample_event_create, sample_player):
        repository.add_event(sample_event_create)
        statuses = repository.get_all_current_statuses()
        assert len(statuses) == 1
        assert statuses[0].player_id == sample_player.id

    def test_deactivate_event(self, repository, sample_event_create):
        event = repository.add_event(sample_event_create)
        repository.deactivate_event(event.id)
        updated = repository.get_player_events(event.player_id)[0]
        assert not updated.is_active

    def test_team_events(self, repository, sample_event_create, sample_team, sample_player):
        repository.add_event(sample_event_create)
        events = repository.get_team_events(sample_team.id)
        assert len(events) == 1

    def test_recovery_restores_availability(self, repository, sample_event_create, sample_player):
        repository.add_event(sample_event_create)
        recovery = EventCreate(
            player_id=sample_player.id,
            event_type=EventType.RECOVERY,
            source_name="manual",
            confidence=ConfidenceLevel.CONFIRMED,
            event_date=date(2026, 4, 16),
        )
        repository.add_event(recovery)
        status = repository.get_current_status(sample_player.id)
        assert status.status == "available"

    def test_available_again_restores_availability(self, repository, sample_event_create, sample_player):
        repository.add_event(sample_event_create)
        available = EventCreate(
            player_id=sample_player.id,
            event_type=EventType.AVAILABLE_AGAIN,
            source_name="manual",
            confidence=ConfidenceLevel.CONFIRMED,
            event_date=date(2026, 4, 16),
        )
        repository.add_event(available)
        status = repository.get_current_status(sample_player.id)
        assert status.status == "available"

    def test_multiple_players(self, repository, sample_team):
        from player_availability.db.models import PlayerModel

        player1 = PlayerModel(name="MS Dhoni", team_id=sample_team.id, role="wicket_keeper")
        player2 = PlayerModel(name="Ruturaj Gaikwad", team_id=sample_team.id, role="batter")
        repository._session.add_all([player1, player2])
        repository._session.flush()

        event1 = EventCreate(
            player_id=player1.id,
            event_type=EventType.INJURY,
            source_name="manual",
            confidence=ConfidenceLevel.CONFIRMED,
            event_date=date(2026, 4, 1),
        )
        event2 = EventCreate(
            player_id=player2.id,
            event_type=EventType.INJURY,
            source_name="manual",
            confidence=ConfidenceLevel.CONFIRMED,
            event_date=date(2026, 4, 2),
        )
        repository.add_event(event1)
        repository.add_event(event2)

        statuses = repository.get_all_current_statuses()
        assert len(statuses) == 2
