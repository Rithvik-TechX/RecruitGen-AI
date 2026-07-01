"""
Organization ORM Model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Organization(BaseModel):
    """Organization entity — multi-tenant company grouping."""

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Relationships ───────────────────────────────────────
    users: Mapped[list[User]] = relationship(
        "User", back_populates="organization", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name!r}>"
