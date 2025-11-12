"""Lead model for generated leads."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Lead(Base):
    """Represents a generated lead for a contractor."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prop_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    trade: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # roofing, hvac, etc.
    
    # Lead quality metrics
    intent_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)  # 0.0 to 1.0
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # Overall quality (0.0 to 1.0)
    
    # Lead status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="generated",
        index=True,
    )  # generated, assigned, delivered, converted, expired
    
    # Assignment
    contractor_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    assigned_by: Mapped[str | None] = mapped_column(String(100), nullable=True)  # System or user
    
    # Delivery
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivery_method: Mapped[str | None] = mapped_column(String(50), nullable=True)  # email, api, webhook
    
    # Conversion tracking
    converted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    conversion_value: Mapped[float | None] = mapped_column(Float, nullable=True)  # Revenue from this lead
    
    # Lead metadata
    zip_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    market_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Signal summary
    signal_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    violation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)  # Lead expiration
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata (renamed to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

