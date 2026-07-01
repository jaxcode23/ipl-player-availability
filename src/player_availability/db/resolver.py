from sqlalchemy import select
from sqlalchemy.orm import Session

from ..normalizers.player import PlayerNameNormalizer
from ..normalizers.resolver import PlayerResolver
from ..normalizers.team import TeamNameNormalizer
from .models import PlayerModel, TeamModel


class DbPlayerResolver(PlayerResolver):
    def __init__(
        self,
        session: Session,
        player_normalizer: PlayerNameNormalizer | None = None,
        team_normalizer: TeamNameNormalizer | None = None,
    ) -> None:
        self._session = session
        self._player_normalizer = player_normalizer or PlayerNameNormalizer()
        self._team_normalizer = team_normalizer or TeamNameNormalizer()

    def resolve(self, player_name: str, team_name: str | None = None) -> int | None:
        canonical = self._player_normalizer.normalize(player_name)

        stmt = select(PlayerModel).where(PlayerModel.name == canonical)
        if team_name:
            canonical_team = self._team_normalizer.normalize(team_name)
            stmt = stmt.join(PlayerModel.team).where(TeamModel.name == canonical_team)

        player = self._session.scalar(stmt.limit(1))
        return player.id if player is not None else None
