"""
Declarative Base & BaseModel mixin — SQLAlchemy 2.0 style.

Every ORM model inherits from ``BaseModel`` which provides:
- ``id``           – UUID v4 primary key
- ``created_at``   – server-default UTC timestamp
- ``updated_at``   – auto-updated UTC timestamp
- ``__tablename__`` auto-derived from the class name (snake_case + plural)
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base — all models inherit from this."""

    pass


def _camel_to_snake(name: str) -> str:
    """Convert CamelCase class name to snake_case table name."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class BaseModel(Base):
    """Abstract base with UUID pk and timestamp columns."""

    __abstract__ = True

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        """Auto-generate table name: CamelCase → snake_case + 's'."""
        return _camel_to_snake(cls.__name__) + "s"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
