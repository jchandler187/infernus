import functools
import secrets
from flask import request, jsonify
from models import Model


def generate_api_key() -> str:
    return secrets.token_hex(32)


def get_model_from_request(session):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    return session.query(Model).filter_by(api_key=token).first()


def require_api_key(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        from db import Session
        session = Session()
        model = get_model_from_request(session)
        if model is None:
            session.close()
            return jsonify({"error": "invalid_api_key"}), 401
        kwargs["model"] = model
        kwargs["session"] = session
        try:
            result = f(*args, **kwargs)
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    return wrapper
