"""Feedback and conversion tracking models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class LeadFeedback(Base):
    """Contractor feedback on lead quality and outcomes."""

    __tablename__ = "lead_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    contractor_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Outcome
    outcome: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # won, lost, no_response, not_interested, wrong_lead
    
    # Quality ratings (1-5 scale)
    lead_quality_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    accuracy_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 (how accurate was the intent score)
    contact_quality_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 (contact data quality)
    
    # Conversion details
    converted: Mapped[bool] = mapped_column(String(50), nullable=False, default=False)
    conversion_value: Mapped[float | None] = mapped_column(Float, nullable=True)  # Revenue
    conversion_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Feedback text
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Additional data
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class ModelVersion(Base):
    """Tracks different versions of the scoring model."""

    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)  # e.g., "v1.0", "v1.1"
    
    # Model configuration
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # baseline, calibrated, ml_model
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)  # Model parameters, weights, etc.
    
    # Performance metrics
    avg_conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_leads_scored: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )  # draft, testing, active, deprecated
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class ABTest(Base):
    """A/B testing configuration and results."""

    __tablename__ = "ab_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Test configuration
    model_a_version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_b_version: Mapped[str] = mapped_column(String(50), nullable=False)
    split_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)  # 0.5 = 50/50 split
    
    # Test status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )  # draft, running, completed, cancelled
    
    # Results
    model_a_conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_b_conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    statistical_significance: Mapped[float | None] = mapped_column(Float, nullable=True)  # p-value
    winner: Mapped[str | None] = mapped_column(String(50), nullable=True)  # model_a, model_b, no_difference
    
    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Metadata
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

