from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CodeViolation(Base):
    """Austin Code Compliance violations linked to properties."""

    __tablename__ = "code_violations"

    violation_id: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False, index=True)
    
    # Property linkage
    prop_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    
    # Violation details
    violation_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    violation_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    violation_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # open, closed, resolved
    
    # Dates
    violation_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    compliance_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Location
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Source metadata
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="austin_code_compliance")
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

