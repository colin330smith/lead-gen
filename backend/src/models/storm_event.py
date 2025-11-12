from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StormEvent(Base):
    """NOAA Storm Events and NWS weather data for intent signal detection."""

    __tablename__ = "storm_events"

    event_id: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False, index=True)
    
    # Event details
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)  # hail, wind, tornado, etc.
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    event_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Location
    county: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(10), nullable=True, default="TX")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    
    # Severity
    magnitude: Mapped[float | None] = mapped_column(Float, nullable=True)  # Hail size, wind speed, etc.
    magnitude_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # inches, mph, etc.
    damage_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Source metadata
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="noaa_storm_events")
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

