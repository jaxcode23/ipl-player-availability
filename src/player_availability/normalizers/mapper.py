from ..domain.events import EventCreate
from .exceptions import UnresolvedPlayerError
from .models import NormalizedRecord
from .resolver import PlayerResolver


def normalized_to_event_create(
    record: NormalizedRecord,
    player_resolver: PlayerResolver,
) -> EventCreate:
    player_id = player_resolver.resolve(record.player_name, record.team_name)
    if player_id is None:
        raise UnresolvedPlayerError(f"Could not resolve player name '{record.player_name}' to a player ID")

    description_parts: list[str] = []
    if record.injury_type:
        description_parts.append(f"Injury: {record.injury_type}")
    if record.replaced_player_name:
        description_parts.append(f"Replacement for {record.replaced_player_name}")
    if record.replacement_player_name:
        description_parts.append(f"Replacement: {record.replacement_player_name}")
    if record.team_name:
        description_parts.append(f"Team: {record.team_name}")

    return EventCreate(
        player_id=player_id,
        event_type=record.event_type,
        description="; ".join(description_parts) if description_parts else None,
        source_name=record.source_name,
        source_url=record.source_url,
        confidence=record.confidence,
        event_date=record.effective_date or record.published_at,
        start_date=record.effective_date,
    )
