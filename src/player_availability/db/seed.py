from __future__ import annotations

from loguru import logger

from .models import PlayerModel, TeamModel
from .session import get_session

TEAMS: dict[str, str] = {
    "CSK": "Chennai Super Kings",
    "MI": "Mumbai Indians",
    "RCB": "Royal Challengers Bengaluru",
    "KKR": "Kolkata Knight Riders",
    "SRH": "Sunrisers Hyderabad",
    "RR": "Rajasthan Royals",
    "DC": "Delhi Capitals",
    "LSG": "Lucknow Super Giants",
    "PBKS": "Punjab Kings",
    "GT": "Gujarat Titans",
}

PLAYER_SEED: list[tuple[str, str, str, bool]] = [
    # Chennai Super Kings
    ("MS Dhoni", "CSK", "wicket_keeper", False),
    ("Ravindra Jadeja", "CSK", "all_rounder", False),
    ("Ruturaj Gaikwad", "CSK", "batter", False),
    ("Shivam Dube", "CSK", "all_rounder", False),
    ("Deepak Chahar", "CSK", "bowler", False),
    ("Tushar Deshpande", "CSK", "bowler", False),
    ("Matheesha Pathirana", "CSK", "bowler", True),
    ("Maheesh Theekshana", "CSK", "bowler", True),
    ("Shardul Thakur", "CSK", "all_rounder", False),
    ("Devon Conway", "CSK", "batter", True),
    ("Khaleel Ahmed", "CSK", "bowler", False),
    ("Ajinkya Rahane", "CSK", "batter", False),
    ("Moeen Ali", "CSK", "all_rounder", True),
    ("Mitchell Santner", "CSK", "all_rounder", True),
    ("Shaik Rasheed", "CSK", "batter", False),
    ("Mustafizur Rahman", "CSK", "bowler", True),
    ("Rajvardhan Hangargekar", "CSK", "all_rounder", False),
    ("Prashant Solanki", "CSK", "bowler", False),
    ("Simarjeet Singh", "CSK", "bowler", False),
    ("Nishant Sindhu", "CSK", "all_rounder", False),
    ("Sameer Rizvi", "CSK", "batter", False),
    ("Aravelly Avanish", "CSK", "wicket_keeper", False),
    ("Jamie Overton", "CSK", "all_rounder", True),
    ("Richard Gleeson", "CSK", "bowler", True),
    ("Imran Tahir", "CSK", "bowler", True),
    ("Ben Stokes", "CSK", "all_rounder", True),
    # Mumbai Indians
    ("Rohit Sharma", "MI", "batter", False),
    ("Hardik Pandya", "MI", "all_rounder", False),
    ("Jasprit Bumrah", "MI", "bowler", False),
    ("Suryakumar Yadav", "MI", "batter", False),
    ("Ishan Kishan", "MI", "wicket_keeper", False),
    ("Tilak Varma", "MI", "batter", False),
    ("Tim David", "MI", "batter", True),
    ("Romario Shepherd", "MI", "all_rounder", True),
    ("Piyush Chawla", "MI", "bowler", False),
    ("Kumar Kartikeya", "MI", "bowler", False),
    ("Shams Mulani", "MI", "all_rounder", False),
    ("Akash Madhwal", "MI", "bowler", False),
    ("Arjun Tendulkar", "MI", "all_rounder", False),
    ("Dewald Brevis", "MI", "batter", True),
    ("Naman Dhir", "MI", "batter", False),
    ("Gerald Coetzee", "MI", "bowler", True),
    ("Jason Behrendorff", "MI", "bowler", True),
    ("Nuwan Thusara", "MI", "bowler", True),
    ("Shreyas Gopal", "MI", "bowler", False),
    ("Suryansh Shedge", "MI", "all_rounder", False),
    ("Harvik Desai", "MI", "wicket_keeper", False),
    ("Kieron Pollard", "MI", "all_rounder", True),
    ("Jofra Archer", "MI", "bowler", True),
    ("Mohammad Nabi", "MI", "all_rounder", True),
    # Royal Challengers Bengaluru
    ("Virat Kohli", "RCB", "batter", False),
    ("Faf du Plessis", "RCB", "batter", True),
    ("Glenn Maxwell", "RCB", "all_rounder", True),
    ("Rajat Patidar", "RCB", "batter", False),
    ("Mohammed Siraj", "RCB", "bowler", False),
    ("Maxwell Bryant", "RCB", "batter", False),
    ("Wanindu Hasaranga", "RCB", "all_rounder", True),
    ("Josh Hazlewood", "RCB", "bowler", True),
    ("Kyle Jamieson", "RCB", "all_rounder", True),
    ("Dinesh Karthik", "RCB", "wicket_keeper", False),
    ("Anuj Rawat", "RCB", "wicket_keeper", False),
    ("Akash Deep", "RCB", "bowler", False),
    ("Mahipal Lomror", "RCB", "all_rounder", False),
    ("Suyash Prabhudessai", "RCB", "batter", False),
    ("Will Jacks", "RCB", "all_rounder", True),
    ("Reece Topley", "RCB", "bowler", True),
    ("Tom Curran", "RCB", "all_rounder", True),
    ("Manoj Bhandage", "RCB", "all_rounder", False),
    ("Rajesh Manhas", "RCB", "wicket_keeper", False),
    ("Vijaykumar Vyshak", "RCB", "bowler", False),
    ("Swapnil Singh", "RCB", "all_rounder", False),
    ("Yash Dayal", "RCB", "bowler", False),
    ("Cameron Green", "RCB", "all_rounder", True),
    ("Saurav Chauhan", "RCB", "batter", False),
    # Kolkata Knight Riders
    ("Shreyas Iyer", "KKR", "batter", False),
    ("Andre Russell", "KKR", "all_rounder", True),
    ("Sunil Narine", "KKR", "all_rounder", True),
    ("Varun Chakravarthy", "KKR", "bowler", False),
    ("Rinku Singh", "KKR", "batter", False),
    ("Nitish Rana", "KKR", "batter", False),
    ("Ramandeep Singh", "KKR", "all_rounder", False),
    ("Venkatesh Iyer", "KKR", "all_rounder", False),
    ("Kuldeep Yadav", "KKR", "bowler", False),
    ("Phil Salt", "KKR", "wicket_keeper", True),
    ("Jason Roy", "KKR", "batter", True),
    ("Mitchell Starc", "KKR", "bowler", True),
    ("Rahmanullah Gurbaz", "KKR", "wicket_keeper", True),
    ("Vaibhav Arora", "KKR", "bowler", False),
    ("Harshit Rana", "KKR", "bowler", False),
    ("Suyash Sharma", "KKR", "bowler", False),
    ("Chetan Sakariya", "KKR", "bowler", False),
    ("KS Bharat", "KKR", "wicket_keeper", False),
    ("Angkrish Raghuvanshi", "KKR", "batter", False),
    ("Mujeeb Ur Rahman", "KKR", "all_rounder", True),
    ("Gus Atkinson", "KKR", "bowler", True),
    ("Sakib Hussain", "KKR", "bowler", False),
    # Sunrisers Hyderabad
    ("Kane Williamson", "SRH", "batter", True),
    ("Jhye Richardson", "SRH", "bowler", True),
    ("Pat Cummins", "SRH", "all_rounder", True),
    ("Abdul Samad", "SRH", "batter", False),
    ("Rashid Khan", "SRH", "bowler", True),
    ("Shahbaz Ahmed", "SRH", "all_rounder", False),
    ("T Natarajan", "SRH", "bowler", False),
    ("Bhuvneshwar Kumar", "SRH", "bowler", False),
    ("Umran Malik", "SRH", "bowler", False),
    ("Washington Sundar", "SRH", "all_rounder", False),
    ("Aiden Markram", "SRH", "batter", True),
    ("Heinrich Klaasen", "SRH", "wicket_keeper", True),
    ("Travis Head", "SRH", "batter", True),
    ("Abhishek Sharma", "SRH", "all_rounder", False),
    ("Mayank Agarwal", "SRH", "batter", False),
    ("Rahul Tripathi", "SRH", "batter", False),
    ("Glenn Phillips", "SRH", "wicket_keeper", True),
    ("Marco Jansen", "SRH", "all_rounder", True),
    ("Fazalhaq Farooqi", "SRH", "bowler", True),
    ("Nithish Reddy", "SRH", "all_rounder", False),
    ("Sanvir Singh", "SRH", "all_rounder", False),
    ("Upendra Yadav", "SRH", "wicket_keeper", False),
    ("Mayank Markande", "SRH", "bowler", False),
    ("Jaydev Unadkat", "SRH", "bowler", False),
    # Rajasthan Royals
    ("Sanju Samson", "RR", "wicket_keeper", False),
    ("Jos Buttler", "RR", "wicket_keeper", True),
    ("Yuzvendra Chahal", "RR", "bowler", False),
    ("Ravichandran Ashwin", "RR", "all_rounder", False),
    ("Shimron Hetmyer", "RR", "batter", True),
    ("Riyan Parag", "RR", "all_rounder", False),
    ("Dhruv Jurel", "RR", "wicket_keeper", False),
    ("Yashasvi Jaiswal", "RR", "batter", False),
    ("Sandeep Sharma", "RR", "bowler", False),
    ("Trent Boult", "RR", "bowler", True),
    ("Kuldeep Sen", "RR", "bowler", False),
    ("Navdeep Saini", "RR", "bowler", False),
    ("Obed McCoy", "RR", "bowler", True),
    ("Donovan Ferreira", "RR", "wicket_keeper", True),
    ("R Ashwin", "RR", "all_rounder", False),
    ("Adam Zampa", "RR", "bowler", True),
    ("Avesh Khan", "RR", "bowler", False),
    ("Prasidh Krishna", "RR", "bowler", False),
    ("Shubham Dubey", "RR", "batter", False),
    ("Nandre Burger", "RR", "bowler", True),
    ("Tom Kohler-Cadmore", "RR", "batter", True),
    ("Rovman Powell", "RR", "batter", True),
    # Delhi Capitals
    ("Rishabh Pant", "DC", "wicket_keeper", False),
    ("Prithvi Shaw", "DC", "batter", False),
    ("Mitchell Marsh", "DC", "all_rounder", True),
    ("David Warner", "DC", "batter", True),
    ("Axar Patel", "DC", "all_rounder", False),
    ("Anrich Nortje", "DC", "bowler", True),
    ("Lungi Ngidi", "DC", "bowler", True),
    ("Alex Carey", "DC", "wicket_keeper", True),
    ("Amit Mishra", "DC", "bowler", False),
    ("Ishant Sharma", "DC", "bowler", False),
    ("Umesh Yadav", "DC", "bowler", False),
    ("Lalit Yadav", "DC", "all_rounder", False),
    ("Ripal Patel", "DC", "all_rounder", False),
    ("Yash Dhull", "DC", "batter", False),
    ("Vicky Ostwal", "DC", "bowler", False),
    ("Kumar Kushagra", "DC", "wicket_keeper", False),
    ("Rasikh Salam", "DC", "bowler", False),
    ("Sumit Kumar", "DC", "all_rounder", False),
    ("Shai Hope", "DC", "wicket_keeper", True),
    ("Harry Brook", "DC", "batter", True),
    ("Jake Fraser-McGurk", "DC", "batter", True),
    ("Tristan Stubbs", "DC", "wicket_keeper", True),
    ("Mukesh Kumar", "DC", "bowler", False),
    # Lucknow Super Giants
    ("KL Rahul", "LSG", "wicket_keeper", False),
    ("Marcus Stoinis", "LSG", "all_rounder", True),
    ("Ravi Bishnoi", "LSG", "bowler", False),
    ("Deepak Hooda", "LSG", "all_rounder", False),
    ("Krunal Pandya", "LSG", "all_rounder", False),
    ("Mark Wood", "LSG", "bowler", True),
    ("Nicholas Pooran", "LSG", "wicket_keeper", True),
    ("Quinton de Kock", "LSG", "wicket_keeper", True),
    ("Ayush Badoni", "LSG", "batter", False),
    ("Mohsin Khan", "LSG", "bowler", False),
    ("Yash Thakur", "LSG", "bowler", False),
    ("Arshin Kulkarni", "LSG", "all_rounder", False),
    ("M Siddharth", "LSG", "bowler", False),
    ("K Gowtham", "LSG", "all_rounder", False),
    ("Prerak Mankad", "LSG", "all_rounder", False),
    ("Ashton Turner", "LSG", "batter", True),
    ("David Willey", "LSG", "all_rounder", True),
    ("Shamar Joseph", "LSG", "bowler", True),
    ("Mayank Yadav", "LSG", "bowler", False),
    ("Naveen-ul-Haq", "LSG", "bowler", True),
    ("Manimaran Siddharth", "LSG", "bowler", False),
    ("Devdutt Padikkal", "LSG", "batter", False),
    # Punjab Kings
    ("Shikhar Dhawan", "PBKS", "batter", False),
    ("Sam Curran", "PBKS", "all_rounder", True),
    ("Jonny Bairstow", "PBKS", "wicket_keeper", True),
    ("Liam Livingstone", "PBKS", "all_rounder", True),
    ("Kagiso Rabada", "PBKS", "bowler", True),
    ("Arshdeep Singh", "PBKS", "bowler", False),
    ("Rahul Chahar", "PBKS", "bowler", False),
    ("Jitesh Sharma", "PBKS", "wicket_keeper", False),
    ("Prabhsimran Singh", "PBKS", "wicket_keeper", False),
    ("Shahrukh Khan", "PBKS", "batter", False),
    ("Harpreet Brar", "PBKS", "all_rounder", False),
    ("Baltej Dhanda", "PBKS", "bowler", False),
    ("Nathan Ellis", "PBKS", "bowler", True),
    ("Sikandar Raza", "PBKS", "all_rounder", True),
    ("Chris Woakes", "PBKS", "all_rounder", True),
    ("Rilee Rossouw", "PBKS", "batter", True),
    ("Ashutosh Sharma", "PBKS", "batter", False),
    ("Vidwath Kaverappa", "PBKS", "bowler", False),
    ("Harshal Patel", "PBKS", "bowler", False),
    ("Vishwanath Singh", "PBKS", "wicket_keeper", False),
    ("Shashank Singh", "PBKS", "all_rounder", False),
    ("Tanay Thyagaraj", "PBKS", "all_rounder", False),
    ("Prince Choudhary", "PBKS", "bowler", False),
    ("Atharva Taide", "PBKS", "batter", False),
    # Gujarat Titans
    ("Shubman Gill", "GT", "batter", False),
    ("David Miller", "GT", "batter", True),
    ("Rashid Khan", "GT", "bowler", True),
    ("Mohammed Shami", "GT", "bowler", False),
    ("Wriddhiman Saha", "GT", "wicket_keeper", False),
    ("B Sai Sudharsan", "GT", "batter", False),
    ("Vijay Shankar", "GT", "all_rounder", False),
    ("Rahul Tewatia", "GT", "all_rounder", False),
    ("Noor Ahmad", "GT", "bowler", True),
    ("Joshua Little", "GT", "bowler", True),
    ("Mohit Sharma", "GT", "bowler", False),
    ("Darshan Nalkande", "GT", "all_rounder", False),
    ("Siddharth Kaul", "GT", "bowler", False),
    ("Sai Kishore", "GT", "bowler", False),
    ("Jayant Yadav", "GT", "all_rounder", False),
    ("Manav Suthar", "GT", "bowler", False),
    ("Sushant Mishra", "GT", "bowler", False),
    ("Kartik Tyagi", "GT", "bowler", False),
    ("Spencer Johnson", "GT", "bowler", True),
    ("Azmatullah Omarzai", "GT", "all_rounder", True),
    ("Robin Minz", "GT", "wicket_keeper", False),
]


def seed_database() -> None:
    with get_session() as session:
        team_objs: dict[str, TeamModel] = {}
        for code, name in TEAMS.items():
            team = session.query(TeamModel).filter_by(short_code=code).one_or_none()
            if team is None:
                team = TeamModel(name=name, short_code=code)
                session.add(team)
                session.flush()
            elif team.name != name:
                team.name = name
            team_objs[code] = team
        logger.info("Ensured {} teams", len(TEAMS))

        seen: set[str] = set()
        inserted = 0
        for name, code, role, is_foreign in PLAYER_SEED:
            if name in seen:
                continue
            seen.add(name)
            players = session.query(PlayerModel).filter_by(name=name).all()
            if not players:
                session.add(PlayerModel(name=name, team_id=team_objs[code].id, role=role, is_foreign=is_foreign))
                inserted += 1
            elif len(players) > 1:
                # Keep the first one, delete the rest to repair database integrity
                for duplicate in players[1:]:
                    session.delete(duplicate)
                # Update the remaining player to ensure it matches the seed
                players[0].team_id = team_objs[code].id
                players[0].role = role
                players[0].is_foreign = is_foreign
            else:
                # Update existing player to match the seed
                players[0].team_id = team_objs[code].id
                players[0].role = role
                players[0].is_foreign = is_foreign
        session.flush()
        logger.info("Ensured {} players ({} inserted)", len(seen), inserted)
