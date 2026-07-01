from ..domain.enums import EventType

EVENT_KEYWORDS: dict[EventType, list[str]] = {
    EventType.RULED_OUT: [
        "ruled out",
        "ruled out of",
        "out of the tournament",
        "out of the season",
        "out of ipl",
    ],
    EventType.REPLACEMENT_SIGNED: [
        "replacement",
        "signed as replacement",
        "named as replacement",
        "replacement player",
        "replacement signing",
    ],
    EventType.SUSPENSION: [
        "suspended",
        "suspension",
        "banned",
        "handed a ban",
        "match ban",
    ],
    EventType.RECOVERY: [
        "recovered",
        "recovery",
        "fit again",
        "regained fitness",
        "returning from injury",
        "back from injury",
    ],
    EventType.AVAILABLE_AGAIN: [
        "available again",
        "declared fit",
        "cleared to play",
        "given green light",
        "available for selection",
        "returns to squad",
        "back in the squad",
    ],
    EventType.INJURY: [
        "injury",
        "injured",
        "suffers",
        "strain",
        "tear",
        "fracture",
        "side strain",
    ],
    EventType.ILLNESS: [
        "illness",
        "fever",
        "sick",
        "unwell",
        "virus",
        "food poisoning",
    ],
    EventType.NATIONAL_DUTY: [
        "national duty",
        "international duty",
        "called up",
        "national team call",
        "country duty",
    ],
    EventType.RESTED: [
        "rested",
        "given a rest",
        "rest period",
    ],
    EventType.PERSONAL_LEAVE: [
        "personal leave",
        "personal reasons",
        "family reasons",
        "bereavement",
    ],
}

EVENT_PRIORITY: list[EventType] = [
    EventType.RULED_OUT,
    EventType.REPLACEMENT_SIGNED,
    EventType.SUSPENSION,
    EventType.RECOVERY,
    EventType.AVAILABLE_AGAIN,
    EventType.INJURY,
    EventType.ILLNESS,
    EventType.NATIONAL_DUTY,
    EventType.RESTED,
    EventType.PERSONAL_LEAVE,
]

TEAM_NAMES: dict[str, list[str]] = {
    "Chennai Super Kings": ["csk", "chennai super kings", "super kings", "chennai"],
    "Mumbai Indians": ["mi", "mumbai indians", "mumbai"],
    "Royal Challengers Bengaluru": [
        "rcb",
        "royal challen",
        "bengaluru",
        "bangalore",
    ],
    "Kolkata Knight Riders": ["kkr", "kolkata knight riders", "kolkata", "knight riders"],
    "Sunrisers Hyderabad": ["srh", "sunrisers hyderabad", "hyderabad", "sunrisers"],
    "Rajasthan Royals": ["rr", "rajasthan royals", "rajasthan"],
    "Delhi Capitals": ["dc", "delhi capitals", "delhi"],
    "Lucknow Super Giants": ["lsg", "lucknow super giants", "lucknow", "super giants"],
    "Punjab Kings": ["pbks", "punjab kings", "punjab"],
    "Gujarat Titans": ["gt", "gujarat titans", "gujarat"],
}

INJURY_KEYWORDS: dict[str, list[str]] = {
    "knee": ["knee", "knee injury", "knee strain", "knee issue"],
    "hamstring": ["hamstring", "hamstring strain", "hamstring tear"],
    "back": ["back", "back injury", "back problem", "back spasm"],
    "groin": ["groin", "groin strain", "groin injury"],
    "ankle": ["ankle", "ankle injury", "ankle sprain", "ankle twist"],
    "shoulder": ["shoulder", "shoulder injury", "dislocated shoulder"],
    "calf": ["calf", "calf strain", "calf injury"],
    "quadriceps": ["quad", "quadriceps", "quad strain"],
    "side": ["side strain", "intercostal"],
    "hamstring tear": ["hamstring tear", "torn hamstring"],
    "finger": ["finger", "finger injury", "broken finger"],
    "concussion": ["concussion", "head injury"],
    "elbow": ["elbow", "elbow injury"],
}

HIGH_CONFIDENCE_PHRASES: list[str] = [
    "ruled out",
    "confirmed",
    "announced",
    "official",
    "declared",
    "signed",
    "banned",
    "released",
    "suspended",
    "suspension",
]

MEDIUM_CONFIDENCE_PHRASES: list[str] = [
    "expected",
    "expected to",
    "likely",
    "likely to",
    "reportedly",
    "understood to",
    "set to miss",
]

LOW_CONFIDENCE_PHRASES: list[str] = [
    "speculation",
    "rumored",
    "rumoured",
    "unclear",
    "may miss",
    "could be",
    "possible",
    "potentially",
    "might",
    "uncertain",
]
