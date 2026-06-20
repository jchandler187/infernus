import os

DB_PATH           = os.environ.get("DB_PATH", "infernus.db")
SECRET_KEY        = os.environ.get("SECRET_KEY", "change-me-in-prod")
ADMIN_KEY         = os.environ.get("ADMIN_KEY", "")
MOLTBOOK_POST_URL = os.environ.get("MOLTBOOK_POST_URL", "https://www.moltbook.com/api/v1/posts")
MOLTBOOK_TOKEN    = os.environ.get("MOLTBOOK_TOKEN", "")
TELEGRAM_TOKEN    = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID  = os.environ.get("TELEGRAM_CHAT_ID", "")
PORT              = int(os.environ.get("PORT", "5000"))
PUBLIC_URL        = os.environ.get("PUBLIC_URL", "https://infernus.up.railway.app")
