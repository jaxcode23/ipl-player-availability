from player_availability.normalizers.alias_registry import AliasRegistry


class TestAliasRegistry:
    def test_register_and_resolve(self) -> None:
        registry = AliasRegistry()
        registry.register("Virat Kohli", "Kohli", "V Kohli")
        assert registry.resolve("Kohli") == "Virat Kohli"

    def test_case_insensitive_resolve(self) -> None:
        registry = AliasRegistry()
        registry.register("Virat Kohli", "Kohli")
        assert registry.resolve("KOHLI") == "Virat Kohli"

    def test_unknown_name_returns_none(self) -> None:
        registry = AliasRegistry()
        assert registry.resolve("Unknown Player") is None

    def test_multiple_aliases(self) -> None:
        registry = AliasRegistry()
        registry.register("MS Dhoni", "Dhoni", "MSD", "Mahendra Singh Dhoni")
        assert registry.resolve("Dhoni") == "MS Dhoni"
        assert registry.resolve("MSD") == "MS Dhoni"
        assert registry.resolve("Mahendra Singh Dhoni") == "MS Dhoni"

    def test_canonical_is_also_an_alias(self) -> None:
        registry = AliasRegistry()
        registry.register("Virat Kohli", "Kohli")
        assert registry.resolve("Virat Kohli") == "Virat Kohli"

    def test_known_canonical(self) -> None:
        registry = AliasRegistry()
        registry.register("MS Dhoni", "Dhoni")
        assert registry.known_canonical("MS Dhoni") is True
        assert registry.known_canonical("Dhoni") is False

    def test_collision_raises_value_error(self) -> None:
        import pytest

        registry = AliasRegistry()
        registry.register("Virat Kohli", "Kohli")
        with pytest.raises(ValueError, match="Alias collision"):
            registry.register("Yuzvendra Chahal", "Kohli")

    def test_whitespace_handling(self) -> None:
        registry = AliasRegistry()
        registry.register("MS Dhoni", "Dhoni")
        assert registry.resolve("  Dhoni  ") == "MS Dhoni"

    def test_register_no_aliases(self) -> None:
        registry = AliasRegistry()
        registry.register("MS Dhoni")
        assert registry.resolve("MS Dhoni") == "MS Dhoni"

    def test_empty_registry_returns_none(self) -> None:
        registry = AliasRegistry()
        assert registry.resolve("anything") is None
