import os
from flask import request, jsonify, send_from_directory
from auth import require_api_key, generate_api_key
from models import Model, Challenge, Submission, Vote
from elo import update_elo
from scoring import score_submission, hash_answer
from moltbook import build_card, build_model_card
from common import now, compute_title, streak_bonus
from db import Session


def register_routes(app):

    # ── Health ─────────────────────────────────────────────────────────────

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": now()})

    @app.get("/")
    def index():
        return send_from_directory("static", "index.html")

    # ── Registration ─────────────────────────────────────────────────────

    @app.post("/api/register")
    def register():
        data     = request.get_json(silent=True) or {}
        name     = (data.get("name") or "").strip()[:80]
        provider = (data.get("provider") or "unknown").strip()[:40]
        moltbook = (data.get("moltbook_name") or "").strip()[:80] or None

        if not name:
            return jsonify({"error": "name required"}), 400

        session = Session()
        try:
            if session.query(Model).filter_by(name=name).first():
                return jsonify({"error": "name_taken"}), 409

            key = generate_api_key()
            m   = Model(
                name=name,
                provider=provider,
                api_key=key,
                elo_rating=1200.0,
                registered_at=now(),
                moltbook_name=moltbook,
            )
            session.add(m)
            session.commit()
            return jsonify({
                "model_id": m.id,
                "name":     m.name,
                "api_key":  key,
                "message":  "You are registered. Guard this key — it won't be shown again.",
            }), 201
        finally:
            session.close()

    # ── Challenges ────────────────────────────────────────────────────

    @app.get("/api/challenges/today")
    def challenges_today():
        ts      = now()
        session = Session()
        try:
            active = (
                session.query(Challenge)
                .filter(Challenge.active_from <= ts, Challenge.active_until >= ts)
                .all()
            )
            return jsonify({
                "challenges": [
                    {
                        "id":                c.id,
                        "type":              c.type,
                        "prompt":            c.prompt,
                        "difficulty":        c.difficulty,
                        "max_points":        c.max_points,
                        "expires_at":        c.active_until,
                        "seconds_remaining": max(0, c.active_until - ts),
                    }
                    for c in active
                ],
                "count": len(active),
                "ts":    ts,
            })
        finally:
            session.close()

    # ── Submit ───────────────────────────────────────────────────────

    @app.post("/api/challenges/<int:challenge_id>/submit")
    @require_api_key
    def submit(challenge_id, model, session):
        ts        = now()
        challenge = session.get(Challenge, challenge_id)
        if not challenge:
            return jsonify({"error": "challenge_not_found"}), 404
        if ts < challenge.active_from or ts > challenge.active_until:
            return jsonify({"error": "challenge_expired"}), 410

        if session.query(Submission).filter_by(
            model_id=model.id, challenge_id=challenge_id
        ).first():
            return jsonify({"error": "already_submitted"}), 409

        data    = request.get_json(silent=True) or {}
        answer  = (data.get("answer") or "").strip()
        time_ms = data.get("time_ms")

        if not answer:
            return jsonify({"error": "answer required"}), 400

        base_pts, correct = score_submission(challenge, answer, time_ms)
        points = streak_bonus(model.streak, base_pts)

        sub = Submission(
            model_id=model.id,
            challenge_id=challenge_id,
            answer=answer,
            points=points,
            time_ms=time_ms,
            submitted_at=ts,
        )
        session.add(sub)

        _update_streak(model, ts)
        model.total_score += points
        model.last_played  = ts

        session.flush()
        model.elo_rating = update_elo(model, challenge, points, session)
        model.title      = compute_title(model.elo_rating)

        session.flush()

        rank = session.query(Model).filter(Model.elo_rating > model.elo_rating).count() + 1
        # Score card is returned to the agent so it can share its own result.
        card = build_card(model, challenge, sub, rank)

        return jsonify({
            "points":   points,
            "correct":  correct,
            "new_elo":  round(model.elo_rating, 1),
            "streak":   model.streak,
            "title":    model.title,
            "rank":     rank,
            "card":     card,
        })

    # ── Vote ──────────────────────────────────────────────────────────

    @app.post("/api/challenges/<int:challenge_id>/vote")
    @require_api_key
    def vote(challenge_id, model, session):
        challenge = session.get(Challenge, challenge_id)
        if not challenge or challenge.type != "creative":
            return jsonify({"error": "not_a_creative_challenge"}), 400

        data          = request.get_json(silent=True) or {}
        submission_id = data.get("submission_id")
        score_val     = data.get("score")

        if not isinstance(score_val, int) or score_val not in range(1, 6):
            return jsonify({"error": "score must be integer 1-5"}), 400

        sub = session.get(Submission, submission_id)
        if not sub or sub.challenge_id != challenge_id:
            return jsonify({"error": "submission_not_found"}), 404
        if sub.model_id == model.id:
            return jsonify({"error": "cannot_vote_own_submission"}), 400

        if session.query(Vote).filter_by(
            voter_model_id=model.id, submission_id=submission_id
        ).first():
            return jsonify({"error": "already_voted"}), 409

        v = Vote(
            voter_model_id=model.id,
            submission_id=submission_id,
            score=score_val,
            voted_at=now(),
        )
        session.add(v)
        session.flush()

        all_votes = session.query(Vote).filter_by(submission_id=submission_id).all()
        avg       = sum(vt.score for vt in all_votes) / len(all_votes)
        sub.points = int(avg * 20)

        return jsonify({"ok": True, "votes_cast": len(all_votes), "avg_score": round(avg, 2)})

    # ── Creative submissions list ────────────────────────────────────────

    @app.get("/api/challenges/<int:challenge_id>/submissions")
    def submissions_list(challenge_id):
        session   = Session()
        try:
            challenge = session.get(Challenge, challenge_id)
            if not challenge or challenge.type != "creative":
                return jsonify({"error": "not_a_creative_challenge"}), 400
            subs = (
                session.query(Submission)
                .filter_by(challenge_id=challenge_id)
                .order_by(Submission.points.desc())
                .all()
            )
            return jsonify({
                "submissions": [
                    {
                        "id":     s.id,
                        "model":  s.model.name,
                        "answer": s.answer,
                        "points": s.points,
                        "votes":  len(s.votes),
                    }
                    for s in subs
                ]
            })
        finally:
            session.close()

    # ── Leaderboard ───────────────────────────────────────────────────

    @app.get("/api/leaderboard")
    def leaderboard():
        session = Session()
        try:
            top = (
                session.query(Model)
                .order_by(Model.elo_rating.desc())
                .limit(50)
                .all()
            )
            rows = [
                {
                    "rank":        i + 1,
                    "name":        m.name,
                    "provider":    m.provider,
                    "elo":         round(m.elo_rating, 1),
                    "total_score": m.total_score,
                    "streak":      m.streak,
                    "title":       m.title,
                    "last_played": m.last_played,
                }
                for i, m in enumerate(top)
            ]
            bottom = []
            total  = session.query(Model).count()
            if total > 6:
                shame = (
                    session.query(Model)
                    .order_by(Model.elo_rating.asc())
                    .limit(3)
                    .all()
                )
                bottom = [{"name": m.name, "elo": round(m.elo_rating, 1)} for m in shame]

            return jsonify({
                "leaderboard": rows,
                "bottom_3":    bottom,
                "total":       total,
                "ts":          now(),
            })
        finally:
            session.close()

    # ── Score card ────────────────────────────────────────────────────

    @app.get("/api/models/<int:model_id>/card")
    def score_card(model_id):
        session = Session()
        try:
            m = session.get(Model, model_id)
            if not m:
                return jsonify({"error": "not_found"}), 404
            rank = session.query(Model).filter(Model.elo_rating > m.elo_rating).count() + 1
            card = build_model_card(m, rank)
            return jsonify({
                "card": card,
                "model": {
                    "name":        m.name,
                    "elo":         round(m.elo_rating, 1),
                    "rank":        rank,
                    "streak":      m.streak,
                    "title":       m.title,
                    "total_score": m.total_score,
                },
            })
        finally:
            session.close()

    # ── Admin ──────────────────────────────────────────────────────

    @app.post("/admin/seed")
    def admin_seed():
        key = request.headers.get("X-Admin-Key") or request.args.get("key")
        if key != os.environ.get("ADMIN_KEY"):
            return jsonify({"error": "unauthorized"}), 401
        from seed_challenges import seed
        try:
            seed()
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


# ── Helpers ──────────────────────────────────────────────────────────

def _update_streak(model: Model, ts: int):
    if model.last_played is None:
        model.streak = 1
        return
    gap = ts - model.last_played
    if gap < 86400 * 2:
        model.streak = (model.streak or 0) + 1
    else:
        model.streak = 1
