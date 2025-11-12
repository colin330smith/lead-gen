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
    
    Returns:
        ContactEnrichment record (created or updated)
    """
    try:
        # Check if enrichment already exists
        existing = await session.get(ContactEnrichment, property.prop_id)
        
        # Skip if already successfully enriched
        if existing and existing.enrichment_status == "success":
            return existing
        
        # Attempt enrichment
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
        
        if hunter_response:
            enrichment_data.update({
                "email": hunter_response.email,
                "phone": hunter_response.phone,
                "hunter_confidence_score": hunter_response.confidence_score,
                "hunter_sources_count": hunter_response.sources_count,
                "hunter_verification_status": hunter_response.verification_status,
                "enrichment_status": "success",
                "last_error": None,
            })
        else:
            enrichment_data.update({
                "enrichment_status": "not_found",
                "last_error": None,
            })
        
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
            "last_error": str(e)[:500],
            "updated_at": datetime.utcnow(),
        }
        
        stmt = insert(ContactEnrichment).values(**error_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["prop_id"],
            set_={
                "enrichment_status": stmt.excluded.enrichment_status,
                "last_error": stmt.excluded.last_error,
                "retry_count": ContactEnrichment.retry_count + 1,
                "updated_at": stmt.excluded.updated_at,
            }
        )
        await session.execute(stmt)
        await session.commit()
        
        raise


async def enrich_properties_batch(
    session: AsyncSession,
    hunter_client: HunterIOClient,
    properties: list[Property],
    rate_limit_per_minute: int = 50,
) -> dict[str, int]:
    """Enrich a batch of properties with rate limiting.
    
    Returns:
        Dictionary with enrichment statistics
    """
    stats = {
        "total": len(properties),
        "success": 0,
        "not_found": 0,
        "failed": 0,
        "skipped": 0,
    }
    
    # Rate limiting: delay between requests
    delay_seconds = 60.0 / rate_limit_per_minute
    
    for i, property in enumerate(properties):
        try:
            # Check if already enriched
            existing = await session.get(ContactEnrichment, property.prop_id)
            if existing and existing.enrichment_status == "success":
                stats["skipped"] += 1
                continue
            
            # Enrich contact
            enrichment = await enrich_property_contact(session, hunter_client, property)
            
            if enrichment.enrichment_status == "success":
                stats["success"] += 1
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
    min_confidence: int = 0,
) -> dict[str, int]:
    """Enrich all properties that need contact enrichment.
    
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
    
    _logger.info("Starting contact enrichment", total_properties=len(properties))
    
    overall_stats = {
        "total": len(properties),
        "success": 0,
        "not_found": 0,
        "failed": 0,
        "skipped": 0,
    }
    
    async with HunterIOClient(_settings.hunter_io_api_key) as hunter_client:
        # Process in batches
        for i in range(0, len(properties), batch_size):
            batch = properties[i:i + batch_size]
            batch_stats = await enrich_properties_batch(
                session,
                hunter_client,
                batch,
                rate_limit_per_minute=_settings.hunter_io_rate_limit_per_minute,
            )
            
            # Accumulate stats
            for key in overall_stats:
                overall_stats[key] += batch_stats.get(key, 0)
            
            _logger.info(
                "Enrichment batch progress",
                batch=i // batch_size + 1,
                total_batches=(len(properties) + batch_size - 1) // batch_size,
                batch_stats=batch_stats,
                overall_stats=overall_stats,
            )
    
    _logger.success("Contact enrichment completed", **overall_stats)
    return overall_stats

