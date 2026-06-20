import sys
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from models import Base
import config

engine = create_engine(
    "sqlite:///" + config.DB_PATH,
    connect_args={"check_same_thread": False, "timeout": 30},
)


@event.listens_for(engine, "connect")
def _set_pragmas(dbapi_conn, _rec):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA busy_timeout=30000")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    s = Session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


if __name__ == "__main__":
    init_db()
    print("schema ready at", config.DB_PATH)
