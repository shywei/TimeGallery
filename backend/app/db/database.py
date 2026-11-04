from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from backend.app.core.config import settings
from backend.app.db.base import Base

# Create SQLite engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False
)

# SQLite optimization event listeners
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import all models before create_all
    import backend.app.models.photo  # noqa
    import backend.app.models.tag  # noqa
    import backend.app.models.collection  # noqa
    import backend.app.models.scan_job  # noqa
    import backend.app.models.scan_issue  # noqa
    import backend.app.models.system_config  # noqa
    import backend.app.models.memory  # noqa
    Base.metadata.create_all(bind=engine)

    # Lightweight migration check for existing SQLite databases
    with engine.connect() as conn:
        try:
            res = conn.exec_driver_sql("PRAGMA table_info(scan_jobs);").fetchall()
            cols = [r[1] for r in res]
            if "missing_dates_json" not in cols and cols:
                conn.exec_driver_sql("ALTER TABLE scan_jobs ADD COLUMN missing_dates_json TEXT;")
                conn.commit()
        except Exception:
            pass
