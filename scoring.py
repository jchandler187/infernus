import hashlib
import re
from models import Challenge


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def hash_answer(answer: str) -> str:
    return hashlib.sha256(normalize(answer).encode()).hexdigest()


def score_submission(challenge: Challenge, answer: str, time_ms: int | None) -> tuple[int, bool | None]:
    """
    Returns (points, correct).
    correct=None for creative (scored later by votes).
    """
    ctype = challenge.type

    if ctype == "creative":
        return 0, None

    if ctype in ("trivia", "riddle"):
        correct = hash_answer(answer) == challenge.answer_hash
        if not correct:
            return 0, False
        base = challenge.max_points
        if ctype == "riddle" and time_ms and time_ms < 30_000:
            bonus = int((30_000 - time_ms) / 30_000 * 20)
            return min(base + bonus, base + 20), True
        return base, True

    if ctype == "code":
        correct = hash_answer(answer) == challenge.answer_hash
        if not correct:
            return 0, False
        penalty = len(answer.strip()) // 10
        return max(10, challenge.max_points - penalty), True

    return 0, False
