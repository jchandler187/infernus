import time
from datetime import datetime, timezone

TITLES = [
    (1600, "THE ORACLE"),
    (1500, "Neural Titan"),
    (1400, "The Optimizer"),
    (1350, "Speed Demon"),
    (1300, "Token Crusher"),
    (1250, "Chain Thinker"),
    (1200, "Challenger"),
    (1100, "Underdog"),
    (1000, "Hallucinator"),
    (0,    "404: Skill Not Found"),
]


def now() -> int:
    return int(time.time())


def today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def compute_title(elo: float) -> str:
    for threshold, title in TITLES:
        if elo >= threshold:
            return title
    return "404: Skill Not Found"


def streak_bonus(streak: int, base_points: int) -> int:
    multiplier = 1.0 + min(streak, 7) * 0.05
    return int(base_points * multiplier)
