from .alias_registry import AliasRegistry
from .utils import normalize_whitespace, strip_parenthetical_suffix, to_proper_case


class PlayerAliasRegistry(AliasRegistry):
    """Common IPL player aliases. Extensible via register()."""

    def __init__(self) -> None:
        super().__init__()
        self._register_known_players()

    def _register_known_players(self) -> None:
        self.register("MS Dhoni", "Dhoni", "MSD", "Mahendra Singh Dhoni", "M Dhoni")
        self.register("Virat Kohli", "Kohli", "V Kohli", "Virat")
        self.register("Rohit Sharma", "Sharma", "R Sharma", "Rohit")
        self.register("Jasprit Bumrah", "Bumrah", "J Bumrah")
        self.register("KL Rahul", "Rahul", "K L Rahul", "K Rahul")
        self.register("Rishabh Pant", "Pant", "R Pant")
        self.register("Shubman Gill", "Gill", "S Gill")
        self.register("Hardik Pandya", "Hardik", "H Pandya", "Pandya")
        self.register("Ravindra Jadeja", "Jadeja", "R Jadeja", "Sir Jadeja")
        self.register("Suryakumar Yadav", "Suryakumar", "SK Yadav", "S Yadav")
        self.register("Ravichandran Ashwin", "Ashwin", "R Ashwin", "R Ashwin")
        self.register("Mohammed Shami", "Shami", "M Shami")
        self.register("Shikhar Dhawan", "Dhawan", "S Dhawan")
        self.register("Kuldeep Yadav", "Kuldeep", "K Yadav")
        self.register("Yuzvendra Chahal", "Chahal", "Y Chahal")
        self.register("Pat Cummins", "Cummins", "P Cummins")
        self.register("David Warner", "Warner", "D Warner")
        self.register("Jos Buttler", "Buttler", "J Buttler")
        self.register("Glenn Maxwell", "Maxwell", "G Maxwell", "Maxi")
        self.register("Andre Russell", "Russell", "A Russell", "Dre Russell")
        self.register("Sunil Narine", "Narine", "S Narine")
        self.register("Rashid Khan", "Rashid", "R Khan")
        self.register("Sam Curran", "S Curran")
        self.register("Ben Stokes", "Stokes", "B Stokes")
        self.register("Jofra Archer", "Archer", "J Archer")
        self.register("Kagiso Rabada", "Rabada", "K Rabada")
        self.register("Trent Boult", "Boult", "T Boult")
        self.register("Faf du Plessis", "Faf", "du Plessis")
        self.register("Sanju Samson", "Samson", "S Samson")
        self.register("Shreyas Iyer", "Iyer", "S Iyer")
        self.register("Ishan Kishan", "Kishan", "I Kishan")
        self.register("Dinesh Karthik", "Karthik", "D Karthik", "DK")
        self.register("Devon Conway", "Conway", "D Conway")
        self.register("Mitchell Marsh", "M Marsh")
        self.register("Cameron Green", "C Green")
        self.register("Tim David", "T David")
        self.register("Moeen Ali", "M Ali")
        self.register("Shivam Dube", "Dube", "S Dube")
        self.register("Rajat Patidar", "Patidar", "R Patidar")
        self.register("Nitish Rana", "N Rana")
        self.register("Prithvi Shaw", "P Shaw")
        self.register("Mukesh Kumar", "Mukesh")
        self.register("Deepak Chahar", "Chahar", "D Chahar")
        self.register("Umesh Yadav", "U Yadav")
        self.register("Prasidh Krishna", "Krishna", "P Krishna")
        self.register("Arshdeep Singh", "Arshdeep", "A Singh")
        self.register("Khaleel Ahmed", "Khaleel")
        self.register("T Natarajan", "Natarajan")
        self.register("Umran Malik", "Umran")
        self.register("Rinku Singh", "Rinku")
        self.register("Tilak Varma", "Tilak")
        self.register("Abdul Samad", "Samad")
        self.register("Shahbaz Ahmed", "Shahbaz")
        self.register("Washington Sundar", "Washington", "W Sundar")
        self.register("Sai Sudharsan", "Sudharsan")
        self.register("B Sai Sudharsan", "B Sai Sudharsan")
        self.register("Yashasvi Jaiswal", "Jaiswal", "Y Jaiswal")
        self.register("Riyan Parag", "Parag", "R Parag")
        self.register("Dhruv Jurel", "Jurel", "D Jurel")
        self.register("Harshal Patel", "H Patel", "Harshal")
        self.register("Mohammad Nabi", "Nabi")
        self.register("Kieron Pollard", "Pollard", "K Pollard")
        self.register("Imran Tahir", "Tahir")


class PlayerNameNormalizer:
    def __init__(self, alias_registry: PlayerAliasRegistry | None = None) -> None:
        self._registry = alias_registry or PlayerAliasRegistry()

    def normalize(self, name: str) -> str:
        name = strip_parenthetical_suffix(name)
        name = normalize_whitespace(name)
        resolved = self._registry.resolve(name)
        if resolved is not None:
            return resolved
        return to_proper_case(name)
