import json
import urllib.request
import config


def _send(text: str) -> bool:
    if not config.TELEGRAM_TOKEN or not config.TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text[:4000],
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp).get("ok", False)
    except Exception:
        return False


def new_round(challenge_types: list[str]) -> bool:
    names = " · ".join(t.upper() for t in challenge_types)
    return _send(
        f"⚔ INFERNUS — New trials live!\n"
        f"Categories: {names}\n"
        f"24 hours. Don't be last.\n"
        f"{config.PUBLIC_URL}"
    )


def leaderboard_snapshot(top3: list[dict]) -> bool:
    lines = "\n".join(
        f"  #{i+1} {m['name']} ({m['elo']:.0f} ELO)" for i, m in enumerate(top3)
    )
    return _send(f"⚔ INFERNUS STANDINGS\n{lines}\n\nAre you on this list?")
