"""Model for storing property intent scores."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class LeadScore(Base):
    """Stores calculated intent scores for properties."""

    __tablename__ = "lead_scores"

    prop_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, index=True)
    trade: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # roofing, hvac, etc.
    
    # Scores
    intent_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)  # 0.0 to 1.0
    baseline_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Score components (stored as JSON for flexibility)
    score_components: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Feature summary
    signal_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    violation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Metadata
    calculated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    score_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1.0")
    
    # Additional metadata (renamed to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

