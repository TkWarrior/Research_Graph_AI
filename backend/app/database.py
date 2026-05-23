"""
SQLAlchemy database engine and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all tables directly from SQLAlchemy metadata.

    Use this ONLY in development / testing when you want a clean DB
    without running Alembic migrations.

    In production (or after the first alembic migration has been applied)
    use Alembic instead:
        alembic upgrade head

    This function is still called on startup via main.py for convenience
    in environments that have not run Alembic yet.
    """
    import app.models  # Ensure ALL models (including Workspace) are loaded
    Base.metadata.create_all(bind=engine)
