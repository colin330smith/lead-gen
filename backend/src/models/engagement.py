"""Engagement tracking models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class LeadEngagement(Base):
    """Tracks engagement with delivered leads."""

    __tablename__ = "lead_engagements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Engagement type
    engagement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # email_opened, email_clicked, webhook_received, api_accessed, converted
    
    # Engagement details
    engagement_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)  # Additional context
    
    # Tracking
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    engaged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Additional metadata (renamed to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class DeliveryLog(Base):
    """Logs all delivery attempts and outcomes."""

    __tablename__ = "delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    contractor_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    
    # Delivery method
    delivery_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # email, webhook, api
    
    # Delivery status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # pending, delivered, failed, retrying
    
    # Delivery details
    recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Email or webhook URL
    tracking_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    
    # Error information
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Timestamps
    attempted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Additional metadata (renamed to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

