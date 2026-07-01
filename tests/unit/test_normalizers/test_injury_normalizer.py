from player_availability.normalizers.utils import InjuryNormalizer


class TestInjuryNormalizer:
    def setup_method(self) -> None:
        self.normalizer = InjuryNormalizer()

    def test_knee_injury(self) -> None:
        assert self.normalizer.normalize("knee") == "Knee Injury"
        assert self.normalizer.normalize("knee injury") == "Knee Injury"
        assert self.normalizer.normalize("knee strain") == "Knee Injury"

    def test_hamstring_injury(self) -> None:
        assert self.normalizer.normalize("hamstring") == "Hamstring Injury"
        assert self.normalizer.normalize("hamstring strain") == "Hamstring Injury"
        assert self.normalizer.normalize("tight hamstring") == "Hamstring Injury"
        assert self.normalizer.normalize("torn hamstring") == "Hamstring Injury"

    def test_back_injury(self) -> None:
        assert self.normalizer.normalize("back") == "Back Injury"
        assert self.normalizer.normalize("back spasm") == "Back Injury"

    def test_ankle_injury(self) -> None:
        assert self.normalizer.normalize("ankle sprain") == "Ankle Injury"
        assert self.normalizer.normalize("ankle twist") == "Ankle Injury"

    def test_shoulder_injury(self) -> None:
        assert self.normalizer.normalize("dislocated shoulder") == "Shoulder Injury"

    def test_concussion(self) -> None:
        assert self.normalizer.normalize("concussion") == "Concussion"
        assert self.normalizer.normalize("head injury") == "Concussion"

    def test_all_known_types(self) -> None:
        types = [
            "knee",
            "hamstring",
            "back",
            "groin",
            "ankle",
            "shoulder",
            "calf",
            "quad",
            "side strain",
            "finger",
            "concussion",
            "elbow",
            "wrist",
        ]
        for t in types:
            assert self.normalizer.normalize(t) is not None, f"{t} should normalize"

    def test_case_insensitive(self) -> None:
        assert self.normalizer.normalize("Hamstring Strain") == "Hamstring Injury"
        assert self.normalizer.normalize("KNEE INJURY") == "Knee Injury"

    def test_unknown_injury_passthrough(self) -> None:
        result = self.normalizer.normalize("unknown injury type")
        assert result == "Unknown Injury Type"

    def test_empty_string_whitespace(self) -> None:
        result = self.normalizer.normalize("")
        assert result == ""

    def test_whitespace_handling(self) -> None:
        assert self.normalizer.normalize("  knee  ") == "Knee Injury"

    def test_quadriceps_variants(self) -> None:
        assert self.normalizer.normalize("quad") == "Quadriceps Injury"
        assert self.normalizer.normalize("quadriceps") == "Quadriceps Injury"
        assert self.normalizer.normalize("quad strain") == "Quadriceps Injury"
