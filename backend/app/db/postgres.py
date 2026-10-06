from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.app.core.config import settings


# -----------------------------
# Database Engine
# -----------------------------

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


# -----------------------------
# Database Session
# -----------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# -----------------------------
# Database Model Base
# -----------------------------

class Base(DeclarativeBase):
    pass


# -----------------------------
# Database Dependency
# -----------------------------

def get_db():
    """
    Provide a database session for one API request.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()