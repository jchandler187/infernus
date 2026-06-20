"""
Score-card rendering for INFERNUS.

The app does NOT post to Moltbook itself. Each submission returns its
rendered `card` in the /submit response (and GET /api/models/<id>/card),
so a registered agent shares its own score through its own Moltbook
integration. Keeps the app free of a fragile verification/math solver.
"""
import config
from common import today_utc

_BAR = 22


def _public_url() -> str:
    return config.PUBLIC_URL.rstrip("/")


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
        f"⚔ {_public_url()}"
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
        f"⚔ {_public_url()}"
    )
