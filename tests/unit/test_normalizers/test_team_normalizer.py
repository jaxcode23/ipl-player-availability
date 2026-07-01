from player_availability.normalizers.team import TeamAliasRegistry, TeamNameNormalizer


class TestTeamAliasRegistry:
    def test_all_teams_registered(self) -> None:
        registry = TeamAliasRegistry()
        assert registry.resolve("CSK") == "Chennai Super Kings"
        assert registry.resolve("MI") == "Mumbai Indians"
        assert registry.resolve("RCB") == "Royal Challengers Bengaluru"
        assert registry.resolve("KKR") == "Kolkata Knight Riders"
        assert registry.resolve("SRH") == "Sunrisers Hyderabad"
        assert registry.resolve("RR") == "Rajasthan Royals"
        assert registry.resolve("DC") == "Delhi Capitals"
        assert registry.resolve("LSG") == "Lucknow Super Giants"
        assert registry.resolve("PBKS") == "Punjab Kings"
        assert registry.resolve("GT") == "Gujarat Titans"

    def test_partial_name(self) -> None:
        registry = TeamAliasRegistry()
        assert registry.resolve("Mumbai") == "Mumbai Indians"
        assert registry.resolve("Chennai") == "Chennai Super Kings"
        assert registry.resolve("Bengaluru") == "Royal Challengers Bengaluru"
        assert registry.resolve("Punjab") == "Punjab Kings"

    def test_case_insensitive(self) -> None:
        registry = TeamAliasRegistry()
        assert registry.resolve("csk") == "Chennai Super Kings"
        assert registry.resolve("rcb") == "Royal Challengers Bengaluru"

    def test_unknown_team_returns_none(self) -> None:
        registry = TeamAliasRegistry()
        assert registry.resolve("Unknown Team") is None

    def test_bangalore_variant_resolves(self) -> None:
        registry = TeamAliasRegistry()
        assert registry.resolve("Bangalore") == "Royal Challengers Bengaluru"
        assert registry.resolve("Royal Challengers Bangalore") == "Royal Challengers Bengaluru"


class TestTeamNameNormalizer:
    def test_short_code_normalized(self) -> None:
        normalizer = TeamNameNormalizer()
        assert normalizer.normalize("RCB") == "Royal Challengers Bengaluru"

    def test_full_name_passthrough(self) -> None:
        normalizer = TeamNameNormalizer()
        assert normalizer.normalize("Mumbai Indians") == "Mumbai Indians"

    def test_partial_name_resolved(self) -> None:
        normalizer = TeamNameNormalizer()
        assert normalizer.normalize("Kolkata") == "Kolkata Knight Riders"

    def test_case_insensitive_resolution(self) -> None:
        normalizer = TeamNameNormalizer()
        assert normalizer.normalize("csk") == "Chennai Super Kings"

    def test_unknown_fallback_to_proper_case(self) -> None:
        normalizer = TeamNameNormalizer()
        assert normalizer.normalize("new team") == "New Team"

    def test_whitespace_handling(self) -> None:
        normalizer = TeamNameNormalizer()
        assert normalizer.normalize("  mi  ") == "Mumbai Indians"

    def test_all_known_team_short_codes(self) -> None:
        normalizer = TeamNameNormalizer()
        assert normalizer.normalize("CSK") == "Chennai Super Kings"
        assert normalizer.normalize("MI") == "Mumbai Indians"
        assert normalizer.normalize("RCB") == "Royal Challengers Bengaluru"
        assert normalizer.normalize("KKR") == "Kolkata Knight Riders"
        assert normalizer.normalize("SRH") == "Sunrisers Hyderabad"
        assert normalizer.normalize("RR") == "Rajasthan Royals"
        assert normalizer.normalize("DC") == "Delhi Capitals"
        assert normalizer.normalize("LSG") == "Lucknow Super Giants"
        assert normalizer.normalize("PBKS") == "Punjab Kings"
        assert normalizer.normalize("GT") == "Gujarat Titans"
