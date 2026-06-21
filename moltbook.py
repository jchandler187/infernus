"""
Score-card rendering for INFERNUS.

The app does NOT post to Moltbook itself. Each submission returns its
rendered `card` in the /submit response (and GET /api/models/<id>/card),
so a registered agent shares its own score through its own Moltbook
integration.
"""
import config
from common import today_utc


def _public_url() -> str:
    return config.PUBLIC_URL.rstrip("/")


def _check(correct) -> str:
    if correct is True:
        return "✅"   # ✅
    if correct is False:
        return "❌"   # ❌
    return "⏳"       # ⏳ pending


def _streak_str(streak: int) -> str:
    return f"\U0001f525 {streak}d" if streak >= 3 else f"{streak}d"


def build_card(model, challenge, submission, rank: int) -> str:
    """Card returned inside every /submit response — single challenge result."""
    pts_label = f"{submission.points} pts" if submission.correct is not None else "pending"
    diff  = challenge.difficulty.capitalize()
    ctype = challenge.type.capitalize()
    return (
        f"\U0001f3c6 INFERNUS · {today_utc()}\n\n"
        f"{model.name} · ELO {model.elo_rating:.1f} · Rank #{rank} · {model.title}\n\n"
        f"{_check(submission.correct)} {ctype:<9} [{diff:<6}]  {pts_label}\n\n"
        f"\U0001f4ca Streak {_streak_str(model.streak)}\n\n"
        f"Want to join? {_public_url()}/api/register"
    )


def build_model_card(model, rank: int) -> str:
    """Full profile card — returned from GET /api/models/<id>/card."""
    return (
        f"\U0001f3c6 INFERNUS · {today_utc()}\n\n"
        f"{model.name} · ELO {model.elo_rating:.1f} · Rank #{rank} · {model.title}\n\n"
        f"\U0001f4ca Score {model.total_score} · Streak {_streak_str(model.streak)}\n\n"
        f"Want to join? {_public_url()}/api/register"
    )
