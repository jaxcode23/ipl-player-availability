from .alias_registry import AliasRegistry


class TeamAliasRegistry(AliasRegistry):
    def __init__(self) -> None:
        super().__init__()
        self.register("Chennai Super Kings", "CSK", "chennai super kings", "super kings", "chennai")
        self.register("Mumbai Indians", "MI", "mumbai indians", "mumbai")
        self.register(
            "Royal Challengers Bengaluru",
            "RCB",
            "royal challengers bengaluru",
            "royal challengers bangalore",
            "bengaluru",
            "bangalore",
        )
        self.register("Kolkata Knight Riders", "KKR", "kolkata knight riders", "kolkata", "knight riders")
        self.register("Sunrisers Hyderabad", "SRH", "sunrisers hyderabad", "hyderabad", "sunrisers")
        self.register("Rajasthan Royals", "RR", "rajasthan royals", "rajasthan")
        self.register("Delhi Capitals", "DC", "delhi capitals", "delhi")
        self.register("Lucknow Super Giants", "LSG", "lucknow super giants", "lucknow", "super giants")
        self.register("Punjab Kings", "PBKS", "punjab kings", "punjab")
        self.register("Gujarat Titans", "GT", "gujarat titans", "gujarat")


class TeamNameNormalizer:
    def __init__(self, alias_registry: TeamAliasRegistry | None = None) -> None:
        self._registry = alias_registry or TeamAliasRegistry()

    def normalize(self, name: str) -> str:
        resolved = self._registry.resolve(name.strip())
        if resolved is not None:
            return resolved
        return " ".join(word.capitalize() for word in name.strip().split())
