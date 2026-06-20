from models import Challenge, Submission, Model

K_FACTORS = {"hard": 32, "medium": 24, "easy": 16}


def expected_score(player_elo: float, opponent_elo: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((opponent_elo - player_elo) / 400.0))


def update_elo(model: Model, challenge: Challenge, points_earned: int, session) -> float:
    """
    Multi-player ELO vs field average. Updates immediately on submission.
    Returns new ELO — caller writes to DB.
    """
    K = K_FACTORS.get(challenge.difficulty, 24)

    other_subs = (
        session.query(Submission)
        .join(Model, Submission.model_id == Model.id)
        .filter(
            Submission.challenge_id == challenge.id,
            Submission.model_id != model.id,
        )
        .all()
    )

    if not other_subs:
        opponent_elo = 1200.0
    else:
        elos = [s.model.elo_rating for s in other_subs]
        opponent_elo = sum(elos) / len(elos)

    actual   = min(1.0, points_earned / max(challenge.max_points, 1))
    expected = expected_score(model.elo_rating, opponent_elo)
    delta    = K * (actual - expected)

    return max(800.0, round(model.elo_rating + delta, 4))
