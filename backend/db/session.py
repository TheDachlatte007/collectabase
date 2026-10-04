import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_database_url() -> str:
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        return configured_url

    # Inside Docker, /app always exists - use the container default.
    # SQLite absolute path on Linux needs 4 slashes: sqlite:////absolute/path
    if os.path.exists("/app"):
        return "sqlite:////app/data/games.db"

    # Local development: store next to the backend source
    local_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "data")
    os.makedirs(local_data_dir, exist_ok=True)
    local_db_path = os.path.join(local_data_dir, "games.db")
    return f"sqlite:///{local_db_path.replace(chr(92), '/')}"

engine = create_engine(get_database_url(), connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """Dependency to provide a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
