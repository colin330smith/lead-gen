from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models.contact_enrichment import ContactEnrichment
from ..models.property import Property
from ..utils.logging import get_logger
from .hunter_io import HunterIOClient

_logger = get_logger(component="contact_enrichment")

_settings = get_settings()


async def enrich_property_contact(
    session: AsyncSession,
    hunter_client: HunterIOClient,
    property: Property,
) -> ContactEnrichment:
    """Enrich contact information for a single property.
    
    IMPORTANT: Only saves emails that have been VERIFIED as deliverable.
    This prevents bounces from invalid email addresses.
    
    Returns:
        ContactEnrichment record (created or updated)
    """
    try:
        # Check if enrichment already exists
        existing = await session.get(ContactEnrichment, property.prop_id)
        
        # Skip if already successfully enriched AND verified
        if existing and existing.enrichment_status == "success" and existing.email_verified:
            return existing
        
        # Attempt enrichment with verification
        hunter_response = await hunter_client.enrich_contact(
            owner_name=property.owner_name,
            owner_address=property.owner_address,
        )
        
        # Prepare enrichment record
        enrichment_data = {
            "prop_id": property.prop_id,
            "owner_name": property.owner_name,
            "owner_address": property.owner_address,
            "enriched_at": datetime.utcnow(),
            "enrichment_source": "hunter_io",
            "updated_at": datetime.utcnow(),
        }
        
        if hunter_response and hunter_response.email:
            # Email was found AND verified (enrich_contact now only returns verified emails)
            enrichment_data.update({
                "email": hunter_response.email,
                "phone": hunter_response.phone,
                "hunter_confidence_score": hunter_response.confidence_score,
                "hunter_sources_count": hunter_response.sources_count,
                "hunter_verification_status": hunter_response.verification_status,
                "email_verified": True,
                "email_deliverable": True,
                "email_verification_score": hunter_response.confidence_score,
                "enrichment_status": "success",
                "last_error": None,
            })
            _logger.info(
                "Contact enriched with VERIFIED email",
                prop_id=property.prop_id,
                email=hunter_response.email,
                verification_status=hunter_response.verification_status,
                confidence_score=hunter_response.confidence_score,
            )
        elif hunter_response and hunter_response.phone and not hunter_response.email:
            # Only phone found, no verified email
            enrichment_data.update({
                "email": None,  # Explicitly set to None - no unverified emails
                "phone": hunter_response.phone,
                "email_verified": False,
                "email_deliverable": False,
                "enrichment_status": "partial",  # Phone only
                "last_error": None,
            })
            _logger.info(
                "Contact enriched with phone only (no verified email)",
                prop_id=property.prop_id,
                phone=hunter_response.phone,
            )
        else:
            # No verified contact info found
            enrichment_data.update({
                "email": None,
                "phone": None,
                "email_verified": False,
                "email_deliverable": False,
                "enrichment_status": "not_found",
                "last_error": None,
            })
            _logger.debug(
                "No verified contact info found",
                prop_id=property.prop_id,
            )
        
        # Upsert enrichment record
        stmt = insert(ContactEnrichment).values(**enrichment_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["prop_id"],
            set_={
                "email": stmt.excluded.email,
                "phone": stmt.excluded.phone,
                "hunter_confidence_score": stmt.excluded.hunter_confidence_score,
                "hunter_sources_count": stmt.excluded.hunter_sources_count,
                "hunter_verification_status": stmt.excluded.hunter_verification_status,
                "email_verified": stmt.excluded.email_verified,
                "email_deliverable": stmt.excluded.email_deliverable,
                "email_verification_score": stmt.excluded.email_verification_score,
                "enriched_at": stmt.excluded.enriched_at,
                "enrichment_status": stmt.excluded.enrichment_status,
                "last_error": stmt.excluded.last_error,
                "updated_at": stmt.excluded.updated_at,
            }
        )
        await session.execute(stmt)
        await session.commit()
        
        return await session.get(ContactEnrichment, property.prop_id)
    
    except Exception as e:
        _logger.exception("Error enriching contact", prop_id=property.prop_id, error=str(e))
        
        # Record error
        error_data = {
            "prop_id": property.prop_id,
            "owner_name": property.owner_name,
            "owner_address": property.owner_address,
            "enrichment_status": "failed",
            "email_verified": False,
            "email_deliverable": False,
            "last_error": str(e)[:500],
            "updated_at": datetime.utcnow(),
        }
        
        stmt = insert(ContactEnrichment).values(**error_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["prop_id"],
            set_={
                "enrichment_status": stmt.excluded.enrichment_status,
                "email_verified": stmt.excluded.email_verified,
                "email_deliverable": stmt.excluded.email_deliverable,
                "last_error": stmt.excluded.last_error,
                "retry_count": ContactEnrichment.retry_count + 1,
                "updated_at": stmt.excluded.updated_at,
            }
        )
        await session.execute(stmt)
        await session.commit()
        
        raise


async def verify_existing_emails(
    session: AsyncSession,
    hunter_client: HunterIOClient,
    batch_size: int = 50,
) -> dict[str, int]:
    """Verify all existing unverified emails in the database.
    
    This should be run to clean up any emails that were added before
    verification was implemented.
    
    Returns:
        Dictionary with verification statistics
    """
    stats = {
        "total": 0,
        "verified_valid": 0,
        "verified_invalid": 0,
        "failed": 0,
    }
    
    # Query contacts with emails that haven't been verified
    query = select(ContactEnrichment).where(
        ContactEnrichment.email.isnot(None),
        ContactEnrichment.email != "",
        ContactEnrichment.email_verified == False,
    ).order_by(ContactEnrichment.prop_id)
    
    result = await session.execute(query)
    contacts = list(result.scalars().all())
    
    stats["total"] = len(contacts)
    _logger.info("Starting verification of existing emails", total=len(contacts))
    
    for contact in contacts:
        try:
            verification = await hunter_client.verify_email(contact.email)
            
            if verification.get("deliverable", False):
                # Email is valid - update record
                contact.email_verified = True
                contact.email_deliverable = True
                contact.email_verification_score = verification.get("score")
                contact.hunter_verification_status = verification.get("status")
                contact.email_mx_records = verification.get("mx_records", False)
                contact.email_smtp_check = verification.get("smtp_check", False)
                contact.email_is_disposable = verification.get("disposable", False)
                contact.email_is_webmail = verification.get("webmail", False)
                contact.email_verification_reason = verification.get("reason")
                stats["verified_valid"] += 1
                _logger.info(
                    "Email verified as VALID",
                    email=contact.email,
                    score=verification.get("score"),
                )
            else:
                # Email is invalid - REMOVE IT to prevent bounces
                _logger.warning(
                    "Email verified as INVALID - removing from record",
                    email=contact.email,
                    status=verification.get("status"),
                    reason=verification.get("reason"),
                )
                contact.email = None  # Remove invalid email
                contact.email_verified = False
                contact.email_deliverable = False
                contact.email_verification_score = verification.get("score")
                contact.hunter_verification_status = verification.get("status")
                contact.email_verification_reason = verification.get("reason")
                contact.enrichment_status = "unverified"  # Mark as unverified
                stats["verified_invalid"] += 1
            
            contact.updated_at = datetime.utcnow()
            await session.commit()
            
            # Rate limiting
            await asyncio.sleep(1.2)  # ~50 requests per minute
            
        except Exception as e:
            _logger.exception("Error verifying email", email=contact.email, error=str(e))
            stats["failed"] += 1
    
    _logger.success("Email verification completed", **stats)
    return stats


async def enrich_properties_batch(
    session: AsyncSession,
    hunter_client: HunterIOClient,
    properties: list[Property],
    rate_limit_per_minute: int = 25,  # Reduced because we now make 2 API calls per contact
) -> dict[str, int]:
    """Enrich a batch of properties with rate limiting.
    
    Note: Rate limit is lower because each enrichment now includes verification.
    
    Returns:
        Dictionary with enrichment statistics
    """
    stats = {
        "total": len(properties),
        "success": 0,
        "partial": 0,  # Phone only
        "not_found": 0,
        "failed": 0,
        "skipped": 0,
    }
    
    # Rate limiting: delay between requests (doubled because we verify each email)
    delay_seconds = 60.0 / rate_limit_per_minute
    
    for i, property in enumerate(properties):
        try:
            # Check if already enriched with verified email
            existing = await session.get(ContactEnrichment, property.prop_id)
            if existing and existing.enrichment_status == "success" and existing.email_verified:
                stats["skipped"] += 1
                continue
            
            # Enrich contact (now includes verification)
            enrichment = await enrich_property_contact(session, hunter_client, property)
            
            if enrichment.enrichment_status == "success":
                stats["success"] += 1
            elif enrichment.enrichment_status == "partial":
                stats["partial"] += 1
            elif enrichment.enrichment_status == "not_found":
                stats["not_found"] += 1
            else:
                stats["failed"] += 1
            
            # Rate limiting
            if i < len(properties) - 1:  # Don't delay after last item
                await asyncio.sleep(delay_seconds)
        
        except Exception as e:
            _logger.exception("Error in batch enrichment", prop_id=property.prop_id)
            stats["failed"] += 1
    
    return stats


async def enrich_all_properties(
    session: AsyncSession,
    batch_size: int = 100,
    limit: int | None = None,
    min_confidence: int = 70,  # Minimum confidence score
) -> dict[str, int]:
    """Enrich all properties that need contact enrichment.
    
    IMPORTANT: This now verifies all emails before saving them.
    Only verified, deliverable emails will be stored.
    
    Args:
        batch_size: Number of properties to process per batch
        limit: Maximum number of properties to enrich (None = all)
        min_confidence: Minimum Hunter.io confidence score to accept (0-100)
    
    Returns:
        Dictionary with overall enrichment statistics
    """
    if not _settings.hunter_io_api_key:
        _logger.error("Hunter.io API key not configured. Skipping enrichment.")
        return {"error": "API key not configured"}
    
    # Query properties that need enrichment
    query = select(Property).where(
        Property.owner_name.isnot(None),
        Property.owner_name != "",
    ).order_by(Property.prop_id)
    
    if limit:
        query = query.limit(limit)
    
    result = await session.execute(query)
    properties = list(result.scalars().all())
    
    _logger.info("Starting contact enrichment WITH VERIFICATION", total_properties=len(properties))
    
    overall_stats = {
        "total": len(properties),
        "success": 0,
        "partial": 0,
        "not_found": 0,
        "failed": 0,
        "skipped": 0,
    }
    
    async with HunterIOClient(_settings.hunter_io_api_key) as hunter_client:
        # Set minimum confidence score
        hunter_client.MIN_CONFIDENCE_SCORE = min_confidence
        
        # Process in batches
        for i in range(0, len(properties), batch_size):
            batch = properties[i:i + batch_size]
            batch_stats = await enrich_properties_batch(
                session,
                hunter_client,
                batch,
                rate_limit_per_minute=_settings.hunter_io_rate_limit_per_minute // 2,  # Halved for verification
            )
            
            # Accumulate stats
            for key in overall_stats:
                if key in batch_stats:
                    overall_stats[key] += batch_stats.get(key, 0)
            
            _logger.info(
                "Enrichment batch progress",
                batch=i // batch_size + 1,
                total_batches=(len(properties) + batch_size - 1) // batch_size,
                batch_stats=batch_stats,
                overall_stats=overall_stats,
            )
    
    _logger.success("Contact enrichment with verification completed", **overall_stats)
    return overall_stats


async def get_verified_contacts_for_outreach(
    session: AsyncSession,
    limit: int | None = None,
) -> list[ContactEnrichment]:
    """Get only verified, deliverable contacts for email outreach.
    
    This is the ONLY function that should be used to get contacts for sending emails.
    It ensures we only send to verified addresses.
    
    Args:
        limit: Maximum number of contacts to return
        
    Returns:
        List of ContactEnrichment records with verified emails
    """
    query = select(ContactEnrichment).where(
        ContactEnrichment.email.isnot(None),
        ContactEnrichment.email != "",
        ContactEnrichment.email_verified == True,
        ContactEnrichment.email_deliverable == True,
    ).order_by(ContactEnrichment.enriched_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    result = await session.execute(query)
    contacts = list(result.scalars().all())
    
    _logger.info("Retrieved verified contacts for outreach", count=len(contacts))
    return contacts
