"""Database connection and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import get_config
from .models import Base


def get_engine():
    """Get SQLAlchemy engine instance.

    Returns:
        Engine: SQLAlchemy engine instance configured for SQLite.
    """
    db_path = get_config().DB_PATH
    db_path.parent.mkdir(exist_ok=True)
    return create_engine(
        f"sqlite:///{db_path}",
        echo=get_config().SQL_ECHO,
    )


def init_db() -> None:
    """Initialize the database by creating all tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session.

    Yields:
        Session: SQLAlchemy database session.

    Example:
        ```python
        with get_db() as db:
            result = db.query(ActionStatus).first()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
