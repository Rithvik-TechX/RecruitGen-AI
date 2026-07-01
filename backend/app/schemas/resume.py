"""
Resume Pydantic Schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    """Public resume representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    raw_text: str | None = None
    parsed_data: dict[str, Any] | None = None
    uploaded_at: datetime
