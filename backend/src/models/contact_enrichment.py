from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ContactEnrichment(Base):
    """Stores enriched contact information for property owners."""

    __tablename__ = "contact_enrichments"

    prop_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, index=True)
    
    # Owner information from property record
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Enriched contact data (from Hunter.io)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    
    # Hunter.io metadata
    hunter_confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    hunter_sources_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hunter_verification_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # valid, invalid, accept_all, unknown
    
    # NEW: Email verification fields
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # True only if email passed verification
    email_verification_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Verification confidence 0-100
    email_deliverable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # True only if safe to send
    email_mx_records: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # Domain has MX records
    email_smtp_check: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # SMTP check passed
    email_is_disposable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # Is disposable email
    email_is_webmail: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # Is webmail (gmail, etc)
    email_verification_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Reason for status
    
    # Enrichment metadata
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    enrichment_source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # hunter_io, manual, etc.
    enrichment_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # pending, success, failed, not_found, unverified
    
    # Error tracking
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class HunterIOResponse(BaseModel):
    """Pydantic model for Hunter.io API response."""
    
    model_config = ConfigDict(extra="ignore")
    
    email: str | None = None
    phone: str | None = None
    confidence_score: int | None = Field(None, alias="score")
    sources_count: int | None = Field(None, alias="sources")
    verification_status: str | None = Field(None, alias="verification")
    
    # Verification fields (populated after verify_email call)
    email_verified: bool = False
    email_deliverable: bool = False
    verification_score: int | None = None
