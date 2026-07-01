from abc import ABC, abstractmethod


class PlayerResolver(ABC):
    @abstractmethod
    def resolve(self, player_name: str, team_name: str | None = None) -> int | None: ...


class DictPlayerResolver(PlayerResolver):
    def __init__(self, mapping: dict[str, int]) -> None:
        self._mapping = mapping

    def resolve(self, player_name: str, team_name: str | None = None) -> int | None:
        return self._mapping.get(player_name.lower().strip())


class TeamResolver(ABC):
    @abstractmethod
    def resolve(self, team_name: str) -> int | None: ...
