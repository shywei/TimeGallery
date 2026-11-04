import pytest
from pathlib import Path
from sqlalchemy import create_engine
from backend.app.db import database

@pytest.fixture(scope="session", autouse=True)
def setup_test_db(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("test_db_dir")
    temp_db_file = temp_dir / "test_growing_up.db"

    test_engine = create_engine(
        f"sqlite:///{temp_db_file.as_posix()}",
        connect_args={"check_same_thread": False}
    )
    database.engine = test_engine
    database.SessionLocal.configure(bind=test_engine)
    database.init_db()
    yield
