"""
CLI: python3 seed_challenges.py [YYYY-MM-DD]

Seeds one challenge of each type for the given UTC date.
Safe to re-run on redeploy — skips already-seeded dates.
"""
import json
import sys
import random
import hashlib
import re
from datetime import datetime, timezone
from db import init_db, Session
from models import Challenge
import config


def _hash(answer: str | None) -> str | None:
    if not answer:
        return None
    normalized = re.sub(r"\s+", " ", answer.strip().lower())
    return hashlib.sha256(normalized.encode()).hexdigest()


def _midnight_utc(date_str: str) -> int:
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def seed(date_str: str | None = None):
    init_db()
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    active_from  = _midnight_utc(date_str)
    active_until = active_from + 86400

    with open("data/challenges.json") as fh:
        bank = json.load(fh)["challenges"]

    session = Session()
    try:
        existing_prompts = {r[0] for r in session.query(Challenge.prompt).all()}

        # Check if this date is already seeded
        existing_today = session.query(Challenge).filter(
            Challenge.active_from == active_from
        ).count()
        if existing_today > 0:
            print(f"Challenges for {date_str} already seeded ({existing_today} found). Skipping.")
            return

        unused = [c for c in bank if c["prompt"] not in existing_prompts]

        seeded = 0
        for ctype in ("trivia", "riddle", "code", "creative"):
            pool = [c for c in unused if c["type"] == ctype]
            if not pool:
                print(f"WARNING: no unused {ctype} challenges in bank")
                continue
            chosen = random.choice(pool)
            ch = Challenge(
                type=chosen["type"],
                prompt=chosen["prompt"],
                answer_hash=_hash(chosen.get("answer")),
                difficulty=chosen.get("difficulty", "medium"),
                max_points=chosen.get("max_points", 100),
                active_from=active_from,
                active_until=active_until,
            )
            session.add(ch)
            unused = [c for c in unused if c["prompt"] != chosen["prompt"]]
            seeded += 1
            print(f"  ⚔  Seeded [{ctype.upper()}] {chosen['difficulty']} — {chosen['prompt'][:60]}…")

        session.commit()
        print(f"\n{seeded} challenges seeded for {date_str}.")
    finally:
        session.close()


if __name__ == "__main__":
    seed(sys.argv[1] if len(sys.argv) > 1 else None)
