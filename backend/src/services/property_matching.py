"""Property matching service to link signals to properties."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.property import Property
from ..utils.logging import get_logger
from .address_normalization import address_similarity, normalize_address

_logger = get_logger(component="property_matching")

MATCH_THRESHOLD = 0.7  # Minimum similarity score for automatic matching
HIGH_CONFIDENCE_THRESHOLD = 0.9  # High confidence match threshold


async def match_address_to_property(
    session: AsyncSession,
    address: str | None,
    zip_code: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> tuple[Property | None, float]:
    """
    Match an address to a property in the database.
    
    Returns:
        Tuple of (Property or None, confidence_score)
    """
    if not address:
        return None, 0.0
    
    # Normalize the input address
    normalized = normalize_address(address)
    normalized_addr = normalized["normalized"]
    
    if not normalized_addr:
        return None, 0.0
    
    # Try multiple matching strategies
    best_match = None
    best_score = 0.0
    
    # Strategy 1: Exact ZIP + normalized address match
    if normalized.get("zip_code") or zip_code:
        zip_to_match = normalized.get("zip_code") or zip_code
        query = select(Property).where(Property.situs_zip == zip_to_match)
        properties = await session.execute(query)
        
        for prop in properties.scalars().all():
            if not prop.situs_address:
                continue
            
            # Normalize property address
            prop_normalized = normalize_address(prop.situs_address)
            prop_normalized_addr = prop_normalized["normalized"]
            
            # Calculate similarity
            score = address_similarity(normalized_addr, prop_normalized_addr)
            
            # Boost score if street number matches
            if normalized.get("street_number") and prop_normalized.get("street_number"):
                if normalized["street_number"] == prop_normalized["street_number"]:
                    score = min(1.0, score + 0.2)
            
            if score > best_score:
                best_score = score
                best_match = prop
    
    # Strategy 2: If no ZIP match or low score, try coordinate-based matching
    if (best_score < MATCH_THRESHOLD) and latitude and longitude:
        # Find properties within ~100 meters (rough approximation)
        # Using simple bounding box (not precise, but fast)
        lat_delta = 0.001  # ~100 meters
        lng_delta = 0.001
        
        query = select(Property).where(
            Property.centroid_y.isnot(None),
            Property.centroid_x.isnot(None),
            Property.centroid_y.between(latitude - lat_delta, latitude + lat_delta),
            Property.centroid_x.between(longitude - lng_delta, longitude + lng_delta),
        )
        
        properties = await session.execute(query)
        
        for prop in properties.scalars().all():
            if not prop.situs_address:
                continue
            
            # Calculate address similarity
            prop_normalized = normalize_address(prop.situs_address)
            prop_normalized_addr = prop_normalized["normalized"]
            score = address_similarity(normalized_addr, prop_normalized_addr)
            
            # Boost for coordinate proximity
            if prop.centroid_y and prop.centroid_x:
                lat_diff = abs(prop.centroid_y - latitude)
                lng_diff = abs(prop.centroid_x - longitude)
                distance_score = 1.0 - min(1.0, (lat_diff + lng_diff) / (lat_delta + lng_delta))
                score = (score * 0.7) + (distance_score * 0.3)
            
            if score > best_score:
                best_score = score
                best_match = prop
    
    # Strategy 3: Fuzzy match across all properties (if still no good match)
    if best_score < MATCH_THRESHOLD:
        # This is expensive, so only do it if we have a ZIP code to narrow down
        if normalized.get("zip_code") or zip_code:
            zip_to_match = normalized.get("zip_code") or zip_code
            query = select(Property).where(Property.situs_zip == zip_to_match)
            properties = await session.execute(query)
            
            for prop in properties.scalars().all():
                if not prop.situs_address:
                    continue
                
                score = address_similarity(normalized_addr, prop.situs_address)
                
                if score > best_score:
                    best_score = score
                    best_match = prop
    
    # Return match if above threshold
    if best_score >= MATCH_THRESHOLD:
        return best_match, best_score
    
    return None, best_score


async def match_signal_to_property(
    session: AsyncSession,
    signal_data: dict[str, Any],
    signal_type: str,
) -> tuple[int | None, float, str]:
    """
    Match a signal (violation, 311 request, etc.) to a property.
    
    Args:
        session: Database session
        signal_data: Dictionary with address, zip_code, latitude, longitude
        signal_type: Type of signal (violation, 311, storm, deed)
    
    Returns:
        Tuple of (prop_id or None, confidence_score, match_method)
    """
    address = signal_data.get("address")
    zip_code = signal_data.get("zip_code")
    latitude = signal_data.get("latitude")
    longitude = signal_data.get("longitude")
    
    property_match, confidence = await match_address_to_property(
        session,
        address=address,
        zip_code=zip_code,
        latitude=latitude,
        longitude=longitude,
    )
    
    if property_match:
        match_method = "high_confidence" if confidence >= HIGH_CONFIDENCE_THRESHOLD else "medium_confidence"
        return property_match.prop_id, confidence, match_method
    
    return None, confidence, "no_match"

