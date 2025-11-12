from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ZipCodeTier(Base):
    """ZIP code tier classification for pricing and lead quality."""

    __tablename__ = "zip_code_tiers"

    zip_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # PREMIUM, STANDARD, VALUE
    
    # Statistics for tier calculation
    total_properties: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_market_value: Mapped[float] = mapped_column(Float, nullable=True)
    median_market_value: Mapped[float] = mapped_column(Float, nullable=True)
    min_market_value: Mapped[float] = mapped_column(Float, nullable=True)
    max_market_value: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Property type distribution
    pct_single_family: Mapped[float] = mapped_column(Float, nullable=True)
    pct_residential: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Additional metrics
    avg_property_age: Mapped[float] = mapped_column(Float, nullable=True)
    pct_with_owner_data: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Tier calculation metadata
    tier_score: Mapped[float] = mapped_column(Float, nullable=True)  # Calculated score used for tier assignment
    last_calculated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

