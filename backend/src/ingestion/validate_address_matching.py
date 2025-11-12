"""Validate address matching accuracy with sample data."""

from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from ..config import get_settings
from ..database import _session_factory, init_database
from ..services.property_matching import match_address_to_property
from ..utils.logging import configure_logging, get_logger

_logger = get_logger(component="validate_matching")
_settings = get_settings()


async def validate_matching_accuracy() -> None:
    """Validate address matching accuracy with property database."""
    configure_logging(_settings.log_level)
    await init_database()
    
    async with _session_factory() as session:  # type: ignore[call-arg]
        from ..models.property import Property
        
        # Get sample of properties with addresses
        query = select(Property).where(
            Property.situs_address.isnot(None),
            Property.situs_zip.isnot(None),
            Property.situs_address != "",
        ).limit(100)
        
        result = await session.execute(query)
        properties = result.scalars().all()
        
        _logger.info("Validating address matching", sample_size=len(properties))
        
        stats = {
            "total": len(properties),
            "perfect_matches": 0,  # Matches own address
            "high_confidence": 0,  # >= 0.9
            "medium_confidence": 0,  # >= 0.7
            "low_confidence": 0,  # < 0.7
            "no_match": 0,
        }
        
        for prop in properties:
            match, confidence = await match_address_to_property(
                session,
                address=prop.situs_address,
                zip_code=prop.situs_zip,
                latitude=prop.centroid_y,
                longitude=prop.centroid_x,
            )
            
            if match:
                if match.prop_id == prop.prop_id:
                    stats["perfect_matches"] += 1
                    if confidence >= 0.9:
                        stats["high_confidence"] += 1
                    elif confidence >= 0.7:
                        stats["medium_confidence"] += 1
                    else:
                        stats["low_confidence"] += 1
                else:
                    stats["no_match"] += 1
            else:
                stats["no_match"] += 1
        
        # Calculate accuracy
        accuracy = (stats["perfect_matches"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        
        _logger.success(
            "Address matching validation complete",
            accuracy=f"{accuracy:.1f}%",
            **stats,
        )
        
        return stats


if __name__ == "__main__":
    asyncio.run(validate_matching_accuracy())

