from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..domain.enums import ConfidenceLevel, EventType
from ..domain.events import AvailabilityEvent, EventCreate, PlayerStatus
from ..exceptions import NotFoundError
from .models import AvailabilityEventModel, PlayerModel

_UNEVENTFUL_TYPES = frozenset(
    {
        EventType.RECOVERY.value,
        EventType.AVAILABLE_AGAIN.value,
        EventType.REPLACEMENT_SIGNED.value,
    }
)


class AbstractRepository(ABC):
    @abstractmethod
    def add_event(self, event: EventCreate) -> AvailabilityEvent: ...

    @abstractmethod
    def get_player_events(self, player_id: int) -> Sequence[AvailabilityEvent]: ...

    @abstractmethod
    def get_team_events(self, team_id: int) -> Sequence[AvailabilityEvent]: ...

    @abstractmethod
    def get_current_status(self, player_id: int) -> PlayerStatus: ...

    @abstractmethod
    def get_all_current_statuses(self) -> Sequence[PlayerStatus]: ...

    @abstractmethod
    def deactivate_event(self, event_id: int) -> None: ...


class SqlRepository(AbstractRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_event(self, event: EventCreate) -> AvailabilityEvent:
        model = AvailabilityEventModel(
            player_id=event.player_id,
            event_type=event.event_type.value,
            description=event.description,
            source_name=event.source_name,
            source_url=event.source_url,
            confidence=event.confidence.value,
            event_date=event.event_date,
            start_date=event.start_date,
            end_date=event.end_date,
        )
        self._session.add(model)
        self._session.flush()
        return self._to_domain(model)

    def get_player_events(self, player_id: int) -> Sequence[AvailabilityEvent]:
        stmt = (
            select(AvailabilityEventModel)
            .where(AvailabilityEventModel.player_id == player_id)
            .order_by(
                AvailabilityEventModel.event_date.desc(),
                AvailabilityEventModel.created_at.desc(),
            )
        )
        return [self._to_domain(e) for e in self._session.scalars(stmt).all()]

    def get_team_events(self, team_id: int) -> Sequence[AvailabilityEvent]:
        stmt = (
            select(AvailabilityEventModel)
            .join(PlayerModel)
            .where(PlayerModel.team_id == team_id)
            .order_by(AvailabilityEventModel.event_date.desc())
        )
        return [self._to_domain(e) for e in self._session.scalars(stmt).all()]

    def get_current_status(self, player_id: int) -> PlayerStatus:
        player = self._session.get(PlayerModel, player_id)
        if not player:
            raise NotFoundError(f"Player {player_id} not found")

        stmt = (
            select(AvailabilityEventModel)
            .where(
                AvailabilityEventModel.player_id == player_id,
                AvailabilityEventModel.is_active,
            )
            .order_by(
                AvailabilityEventModel.event_date.desc(),
                AvailabilityEventModel.created_at.desc(),
            )
            .limit(1)
        )
        event = self._session.scalar(stmt)

        if event and event.event_type not in _UNEVENTFUL_TYPES:
            return PlayerStatus(
                player_id=player.id,
                player_name=player.name,
                team_name=player.team.name if player.team else "",
                status="unavailable",
                reason=_format_reason(event),
                since=event.start_date or event.event_date,
                expected_return=event.end_date,
            )

        return PlayerStatus(
            player_id=player.id,
            player_name=player.name,
            team_name=player.team.name if player.team else "",
            status="available",
        )

    def get_all_current_statuses(self) -> Sequence[PlayerStatus]:
        stmt = (
            select(AvailabilityEventModel)
            .where(
                AvailabilityEventModel.is_active,
                ~AvailabilityEventModel.event_type.in_(list(_UNEVENTFUL_TYPES)),
            )
            .order_by(
                AvailabilityEventModel.player_id,
                AvailabilityEventModel.event_date.desc(),
                AvailabilityEventModel.created_at.desc(),
            )
        )
        results = self._session.scalars(stmt).all()

        seen: set[int] = set()
        events: list[AvailabilityEventModel] = []
        for event in results:
            if event.player_id not in seen:
                seen.add(event.player_id)
                events.append(event)

        return [
            PlayerStatus(
                player_id=e.player_id,
                player_name=e.player.name,
                team_name=e.player.team.name if e.player.team else "",
                status="unavailable",
                reason=_format_reason(e),
                since=e.start_date or e.event_date,
                expected_return=e.end_date,
            )
            for e in events
        ]

    def deactivate_event(self, event_id: int) -> None:
        stmt = (
            update(AvailabilityEventModel)
            .where(AvailabilityEventModel.id == event_id)
            .values(is_active=False, updated_at=datetime.now(UTC).replace(tzinfo=None))
        )
        self._session.execute(stmt)

    @staticmethod
    def _to_domain(model: AvailabilityEventModel) -> AvailabilityEvent:
        return AvailabilityEvent(
            id=model.id,
            player_id=model.player_id,
            event_type=EventType(model.event_type),
            description=model.description,
            source_name=model.source_name,
            source_url=model.source_url,
            confidence=ConfidenceLevel(model.confidence),
            event_date=model.event_date,
            start_date=model.start_date,
            end_date=model.end_date,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


def _format_reason(event: AvailabilityEventModel) -> str:
    label = event.event_type.replace("_", " ").title()
    if event.description:
        return f"{label} - {event.description}"
    return label
