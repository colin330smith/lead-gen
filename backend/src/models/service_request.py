from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ServiceRequest(Base):
    """City of Austin 311 service requests for intent signal detection."""

    __tablename__ = "service_requests"

    request_id: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False, index=True)
    
    # Request details
    request_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    request_category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    request_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # open, closed, in_progress
    
    # Location
    address: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    zip_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Dates
    requested_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    closed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Property linkage (if we can match)
    prop_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    
    # Source metadata
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="austin_311")
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

