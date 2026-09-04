from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


# Import models so Alembic can discover their tables through ``Base.metadata``.
from app import models  # noqa: E402,F401
