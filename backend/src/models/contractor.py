"""Contractor model for territory management."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Contractor(Base):
    """Represents a contractor customer."""

    __tablename__ = "contractors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Contractor info
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Business details
    trades: Mapped[str] = mapped_column(String(255), nullable=False)  # Comma-separated: roofing,hvac,siding
    subscription_tier: Mapped[str] = mapped_column(String(50), nullable=False, default="starter")  # starter, growth, pro, scale
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
    )  # active, paused, cancelled
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata (renamed to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ContractorTerritory(Base):
    """Tracks contractor territory assignments (ZIP code exclusivity)."""

    __tablename__ = "contractor_territories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contractor_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    trade: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # roofing, hvac, etc.
    
    # Exclusivity
    is_exclusive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # One contractor per ZIP per trade
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
    )  # active, paused, expired
    
    # Timestamps
    assigned_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata (renamed to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

