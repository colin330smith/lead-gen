"""Test and validate address matching system."""

from __future__ import annotations

import asyncio

from ..config import get_settings
from ..database import _session_factory, init_database
from ..services.address_normalization import address_similarity, normalize_address
from ..services.property_matching import match_address_to_property
from ..utils.logging import configure_logging, get_logger

_logger = get_logger(component="test_address_matching")
_settings = get_settings()


async def test_address_normalization() -> None:
    """Test address normalization with various formats."""
    _logger.info("Testing address normalization")
    
    test_cases = [
        "123 Main St, Austin, TX 78701",
        "4507 KNAP HOLW, AUSTIN, TX 78731",
        "1411 MEARNS MEADOW BLVD, AUSTIN, TX 78758",
        "N 805 CAPITAL OF TX HY, TX",
        "9219 ANDERSON MILL RD, AUSTIN, TX 78729",
        "1026 CLAYTON LN, AUSTIN, TX 78723",
    ]
    
    for addr in test_cases:
        normalized = normalize_address(addr)
        _logger.info(
            "Address normalization",
            original=addr,
            normalized=normalized["normalized"],
            street_number=normalized["street_number"],
            street_name=normalized["street_name"],
            zip_code=normalized["zip_code"],
        )


async def test_address_similarity() -> None:
    """Test address similarity calculation."""
    _logger.info("Testing address similarity")
    
    test_pairs = [
        ("123 Main St", "123 Main Street"),
        ("4507 KNAP HOLW", "4507 KNAP HOLLOW"),
        ("N 805 CAPITAL OF TX HY", "805 N CAPITAL OF TEXAS HWY"),
        ("1411 MEARNS MEADOW BLVD", "1411 MEARNS MEADOW BOULEVARD"),
    ]
    
    for addr1, addr2 in test_pairs:
        similarity = address_similarity(addr1, addr2)
        _logger.info(
            "Address similarity",
            addr1=addr1,
            addr2=addr2,
            similarity=round(similarity, 3),
        )


async def test_property_matching() -> None:
    """Test property matching with real addresses from database."""
    _logger.info("Testing property matching with database addresses")
    
    async with _session_factory() as session:  # type: ignore[call-arg]
        # Get some sample properties
        from sqlalchemy import select
        from ..models.property import Property
        
        query = select(Property).where(
            Property.situs_address.isnot(None),
            Property.situs_zip.isnot(None),
        ).limit(10)
        
        result = await session.execute(query)
        properties = result.scalars().all()
        
        _logger.info("Testing matching with sample properties", count=len(properties))
        
        matches = {"high_confidence": 0, "medium_confidence": 0, "low_confidence": 0, "no_match": 0}
        
        for prop in properties:
            if not prop.situs_address:
                continue
            
            # Try to match the property's own address (should be perfect match)
            match, confidence = await match_address_to_property(
                session,
                address=prop.situs_address,
                zip_code=prop.situs_zip,
                latitude=prop.centroid_y,
                longitude=prop.centroid_x,
            )
            
            if match and match.prop_id == prop.prop_id:
                if confidence >= 0.9:
                    matches["high_confidence"] += 1
                    _logger.success("Perfect match", prop_id=prop.prop_id, confidence=confidence)
                elif confidence >= 0.7:
                    matches["medium_confidence"] += 1
                    _logger.info("Good match", prop_id=prop.prop_id, confidence=confidence)
                else:
                    matches["low_confidence"] += 1
                    _logger.warning("Low confidence match", prop_id=prop.prop_id, confidence=confidence)
            else:
                matches["no_match"] += 1
                _logger.warning("No match found", prop_id=prop.prop_id, address=prop.situs_address)
        
        _logger.success("Property matching test complete", **matches)


async def test_signal_address_matching() -> None:
    """Test matching addresses from signal data."""
    _logger.info("Testing signal address matching")
    
    # Test addresses from 311 and violations
    test_addresses = [
        {"address": "4507 KNAP HOLW, AUSTIN, TX", "zip_code": "78731", "latitude": 30.3484472, "longitude": -97.77776831},
        {"address": "1411 MEARNS MEADOW BLVD, AUSTIN, TX", "zip_code": "78758", "latitude": 30.37525546, "longitude": -97.70466813},
        {"address": "9219 ANDERSON MILL RD", "zip_code": "78729", "latitude": 30.45092881, "longitude": -97.78260329},
    ]
    
    async with _session_factory() as session:  # type: ignore[call-arg]
        from ..services.property_matching import match_signal_to_property
        
        for signal_data in test_addresses:
            prop_id, confidence, method = await match_signal_to_property(
                session, signal_data, "test"
            )
            
            if prop_id:
                _logger.success(
                    "Signal matched",
                    address=signal_data["address"],
                    prop_id=prop_id,
                    confidence=round(confidence, 3),
                    method=method,
                )
            else:
                _logger.warning(
                    "Signal not matched",
                    address=signal_data["address"],
                    confidence=round(confidence, 3),
                )


async def main() -> None:
    """Run all address matching tests."""
    configure_logging(_settings.log_level)
    await init_database()
    
    _logger.info("Starting address matching tests")
    
    await test_address_normalization()
    await test_address_similarity()
    await test_property_matching()
    await test_signal_address_matching()
    
    _logger.success("All address matching tests complete")


if __name__ == "__main__":
    asyncio.run(main())

