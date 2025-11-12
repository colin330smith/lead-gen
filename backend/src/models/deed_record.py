from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class DeedRecord(Base):
    """Travis County Deed Records for property ownership changes and intent signals."""

    __tablename__ = "deed_records"

    deed_id: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False, index=True)
    
    # Property linkage
    prop_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    
    # Deed details
    deed_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    deed_book_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    deed_book_page: Mapped[str | None] = mapped_column(String(50), nullable=True)
    deed_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    deed_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)  # sale, transfer, etc.
    
    # Parties
    grantor: Mapped[str | None] = mapped_column(String(500), nullable=True)
    grantee: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Transaction details
    sale_price: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    sale_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    
    # Property details from deed
    property_address: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    legal_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Source metadata
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="travis_county_deeds")
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

