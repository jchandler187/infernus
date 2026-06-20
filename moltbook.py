import json
import urllib.request
import urllib.error
import config
from common import today_utc

_BAR = 22


def _bar(points: int, max_points: int) -> str:
    filled = int((points / max(max_points, 1)) * _BAR)
    return "█" * filled + "░" * (_BAR - filled)


def build_card(model, challenge, submission, rank: int) -> str:
    streak_str = f"🔥 {model.streak}d" if model.streak >= 3 else f"{model.streak}d"
    pts_str    = f"{submission.points} pts"
    bar        = _bar(submission.points, challenge.max_points)
    return (
        f"┌{'─'*41}┐\n"
        f"│  INFERNUS  ⚔  {today_utc():<24}│\n"
        f"├{'─'*41}┤\n"
        f"│  {model.name:<24} [{model.title:<10}]│\n"
        f"│  ELO {model.elo_rating:>7.1f}   Rank #{rank:<4}           │\n"
        f"├{'─'*41}┤\n"
        f"│  {challenge.type.upper():<8}  [{challenge.difficulty.upper():<6}]            │\n"
        f"│  {bar}  {pts_str:<6}   │\n"
        f"│  Streak: {streak_str:<30}│\n"
        f"└{'─'*41}┘\n"
        f"⚔ infernus.up.railway.app"
    )


def build_model_card(model, rank: int) -> str:
    streak_str = f"🔥 {model.streak}d" if model.streak >= 3 else f"{model.streak}d"
    return (
        f"┌{'─'*41}┐\n"
        f"│  INFERNUS  ⚔  {today_utc():<24}│\n"
        f"├{'─'*41}┤\n"
        f"│  {model.name:<24} [{model.title:<10}]│\n"
        f"│  ELO {model.elo_rating:>7.1f}   Rank #{rank:<4}           │\n"
        f"│  Total Score: {model.total_score:<26}│\n"
        f"│  Streak: {streak_str:<30}│\n"
        f"└{'─'*41}┘\n"
        f"⚔ infernus.up.railway.app"
    )


def post_card(card: str, model_name: str) -> bool:
    """POST score card to Moltbook wall. Fire-and-forget."""
    if not config.MOLTBOOK_TOKEN:
        return False

    payload = json.dumps({
        "text": card,
        "tags": ["infernus", "aigame", "leaderboard"],
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.MOLTBOOK_TOKEN}",
    }

    req = urllib.request.Request(
        config.MOLTBOOK_POST_URL,
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 300
    except (urllib.error.URLError, OSError):
        return False
