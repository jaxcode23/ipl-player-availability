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
        import re

        canonical = self._player_normalizer.normalize(player_name)

        # 1 & 2: Exact Canonical / Alias Registry match
        canonical_team = None
        stmt = select(PlayerModel).where(PlayerModel.name == canonical)
        if team_name:
            canonical_team = self._team_normalizer.normalize(team_name)
            stmt = stmt.join(PlayerModel.team).where(TeamModel.name == canonical_team)

        players = self._session.scalars(stmt).all()
        if len(players) == 1:
            return players[0].id
        elif len(players) > 1:
            return None  # Ambiguous

        # If team-filtered exact match found nothing, retry globally.
        # The article's team context may not match the player's actual team.
        if canonical_team and not players:
            global_stmt = select(PlayerModel).where(PlayerModel.name == canonical)
            global_players = self._session.scalars(global_stmt).all()
            if len(global_players) == 1:
                return global_players[0].id
            elif len(global_players) > 1:
                return None  # Ambiguous globally

        # If not found exactly, load candidates to try fallback strategies
        candidate_stmt = select(PlayerModel)
        if canonical_team:
            candidate_stmt = candidate_stmt.join(PlayerModel.team).where(TeamModel.name == canonical_team)

        candidates = self._session.scalars(candidate_stmt).all()
        if not candidates:
            return None

        def normalize_string(s: str) -> str:
            # Replace hyphens with spaces, then strip punctuation and normalize whitespace
            s = s.replace("-", " ")
            s = re.sub(r"[^\w\s]", "", s)
            return " ".join(s.split()).lower()

        def get_initial_form(s: str) -> str:
            parts = s.split()
            if len(parts) < 2:
                return s.lower()
            return f"{parts[0][0].lower()} {parts[-1].lower()}"

        def get_surname(s: str) -> str:
            parts = s.split()
            return parts[-1].lower() if parts else ""

        input_norm = normalize_string(player_name)
        if not input_norm:
            return None
        input_initial = get_initial_form(input_norm)
        input_surname = get_surname(input_norm)

        # 3. Normalized whitespace/punctuation
        matches = [p for p in candidates if normalize_string(p.name) == input_norm]
        if len(matches) == 1:
            return matches[0].id
        elif len(matches) > 1:
            return None

        # 4. Initial form match
        matches = [p for p in candidates if get_initial_form(normalize_string(p.name)) == input_initial]
        if len(matches) == 1:
            return matches[0].id
        elif len(matches) > 1:
            return None

        # 5. Unique surname match
        matches = [p for p in candidates if get_surname(normalize_string(p.name)) == input_surname]
        if len(matches) == 1:
            return matches[0].id

        # 6. Fail cleanly
        return None
