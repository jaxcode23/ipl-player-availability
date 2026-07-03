from player_availability.normalizers.player import PlayerAliasRegistry, PlayerNameNormalizer


class TestPlayerAliasRegistry:
    def test_common_aliases(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("Kohli") == "Virat Kohli"
        assert registry.resolve("Dhoni") == "MS Dhoni"
        assert registry.resolve("Bumrah") == "Jasprit Bumrah"
        assert registry.resolve("Rahul") == "KL Rahul"

    def test_initial_aliases(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("V Kohli") == "Virat Kohli"
        assert registry.resolve("J Bumrah") == "Jasprit Bumrah"
        assert registry.resolve("R Jadeja") == "Ravindra Jadeja"

    def test_unknown_player_not_in_registry(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("Unknown Player") is None

    def test_known_canonical(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.known_canonical("Virat Kohli") is True
        assert registry.known_canonical("Rohit Sharma") is True

    def test_extend_registry(self) -> None:
        registry = PlayerAliasRegistry()
        registry.register("New Player", "New")
        assert registry.resolve("New") == "New Player"

    def test_msd_to_ms_dhoni(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("MSD") == "MS Dhoni"

    def test_quinton_resolves(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("Quinton") == "Quinton de Kock"

    def test_hasaranga_resolves(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("Hasaranga") == "Wanindu Hasaranga"

    def test_emanjot_resolves(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("Emanjot") == "Emanjot Chahal"

    def test_esterhuizen_resolves(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("Esterhuizen") == "Connor Esterhuizen"

    def test_bethell_resolves(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("Bethell") == "Jacob Bethell"

    def test_ruchir_ahir_resolves_to_ruchit(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("Ruchir Ahir") == "Ruchit Ahir"

    def test_banton_resolves(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("Banton") == "Tom Banton"

    def test_dian_resolves(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("Dian") == "Dian Forrester"

    def test_thusara_resolves(self) -> None:
        registry = PlayerAliasRegistry()
        assert registry.resolve("Thusara") == "Nuwan Thushara"


class TestPlayerNameNormalizer:
    def test_full_name_passthrough(self) -> None:
        normalizer = PlayerNameNormalizer()
        assert normalizer.normalize("Virat Kohli") == "Virat Kohli"

    def test_alias_resolved(self) -> None:
        normalizer = PlayerNameNormalizer()
        assert normalizer.normalize("Kohli") == "Virat Kohli"

    def test_initial_based_name(self) -> None:
        normalizer = PlayerNameNormalizer()
        assert normalizer.normalize("V Kohli") == "Virat Kohli"

    def test_parenthetical_stripped(self) -> None:
        normalizer = PlayerNameNormalizer()
        assert normalizer.normalize("Virat Kohli (India)") == "Virat Kohli"

    def test_parenthetical_and_alias(self) -> None:
        normalizer = PlayerNameNormalizer()
        assert normalizer.normalize("Kohli (c)") == "Virat Kohli"

    def test_unknown_name_proper_cased(self) -> None:
        normalizer = PlayerNameNormalizer()
        assert normalizer.normalize("john smith") == "John Smith"

    def test_whitespace_normalized(self) -> None:
        normalizer = PlayerNameNormalizer()
        assert normalizer.normalize("  Virat   Kohli  ") == "Virat Kohli"

    def test_initials_preserved_in_unknown(self) -> None:
        normalizer = PlayerNameNormalizer()
        assert normalizer.normalize("AB de Villiers") == "AB de Villiers"

    def test_lowercase_alias_still_resolves(self) -> None:
        assert PlayerNameNormalizer().normalize("kohli") == "Virat Kohli"

    def test_empty_string_returns_empty(self) -> None:
        normalizer = PlayerNameNormalizer()
        assert normalizer.normalize("") == ""

    def test_dhoni_aliases(self) -> None:
        normalizer = PlayerNameNormalizer()
        assert normalizer.normalize("MS Dhoni") == "MS Dhoni"
        assert normalizer.normalize("Dhoni") == "MS Dhoni"
        assert normalizer.normalize("MSD") == "MS Dhoni"

    def test_custom_registry(self) -> None:
        registry = PlayerAliasRegistry()
        registry.register("Custom Player", "Custom")
        normalizer = PlayerNameNormalizer(alias_registry=registry)
        assert normalizer.normalize("Custom") == "Custom Player"
        assert normalizer.normalize("Virat Kohli") == "Virat Kohli"

    def test_deterministic_noise_stripped(self) -> None:
        normalizer = PlayerNameNormalizer()
        assert normalizer.normalize("Cricinfo Virat Kohli") == "Virat Kohli"
        assert normalizer.normalize("India Today MS Dhoni (c)") == "MS Dhoni"
        assert normalizer.normalize("Rohit Sharma returns") == "Rohit Sharma"
        assert normalizer.normalize("Injury Crisis Deepens: Suryakumar Yadav") == "Suryakumar Yadav"
        assert normalizer.normalize("Hardik Pandya still unavailable") == "Hardik Pandya"
