class AliasRegistry:
    """Case-insensitive mapping from aliases to canonical forms.

    Usage:
        registry = AliasRegistry()
        registry.register("Virat Kohli", "Kohli", "V Kohli", "Virat")
        assert registry.resolve("kohli") == "Virat Kohli"
        assert registry.resolve("Unknown") is None
    """

    def __init__(self) -> None:
        self._alias_to_canonical: dict[str, str] = {}
        self._canonical_lower: set[str] = set()

    def register(self, canonical: str, *aliases: str) -> None:
        canonical_key = canonical.lower().strip()
        self._alias_to_canonical[canonical_key] = canonical
        self._canonical_lower.add(canonical_key)
        for alias in aliases:
            self._alias_to_canonical[alias.lower().strip()] = canonical

    def resolve(self, name: str) -> str | None:
        return self._alias_to_canonical.get(name.lower().strip())

    def known_canonical(self, name: str) -> bool:
        return name.lower().strip() in self._canonical_lower
