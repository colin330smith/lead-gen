"""Test script to validate data source clients with sample data."""

from __future__ import annotations

import asyncio

from ..config import get_settings
from ..database import _session_factory, init_database
from ..utils.logging import configure_logging, get_logger
from .austin_311 import Austin311Client
from .austin_code_compliance import AustinCodeComplianceClient
from .noaa_storm_events import NOAAStormEventsClient

_logger = get_logger(component="test_data_sources")
_settings = get_settings()


async def test_austin_311() -> None:
    """Test Austin 311 client."""
    _logger.info("Testing Austin 311 client")
    
    async with Austin311Client() as client:
        count = 0
        async for record in client.iter_records(limit=10):
            _logger.info("311 record", **{k: v for k, v in record.items() if k != "raw_data"})
            count += 1
            if count >= 5:
                break
        
        _logger.success("Austin 311 test complete", records_fetched=count)


async def test_code_compliance() -> None:
    """Test Austin Code Compliance client."""
    _logger.info("Testing Austin Code Compliance client")
    
    async with AustinCodeComplianceClient() as client:
        count = 0
        async for record in client.iter_records(limit=10):
            _logger.info("Violation record", **{k: v for k, v in record.items() if k != "raw_data"})
            count += 1
            if count >= 5:
                break
        
        _logger.success("Code Compliance test complete", records_fetched=count)


async def test_noaa_storm_events() -> None:
    """Test NOAA Storm Events client."""
    _logger.info("Testing NOAA Storm Events client")
    
    async with NOAAStormEventsClient() as client:
        count = 0
        try:
            async for record in client.iter_records(years=[2024], limit=10):
                if record:
                    _logger.info("Storm event record", **{k: v for k, v in record.items() if k != "raw_data"})
                    count += 1
                    if count >= 5:
                        break
        except Exception as e:
            _logger.warning("NOAA test encountered issue", error=str(e))
        
        _logger.success("NOAA Storm Events test complete", records_fetched=count)


async def test_address_matching() -> None:
    """Test address matching with sample addresses."""
    _logger.info("Testing address matching")
    
    from ..services.address_normalization import normalize_address, address_similarity
    from ..services.property_matching import match_address_to_property
    
    test_addresses = [
        "123 Main St, Austin, TX 78701",
        "4507 KNAP HOLW, AUSTIN, TX 78731",
        "1411 MEARNS MEADOW BLVD, AUSTIN, TX 78758",
    ]
    
    async with _session_factory() as session:  # type: ignore[call-arg]
        for addr in test_addresses:
            _logger.info("Testing address", address=addr)
            normalized = normalize_address(addr)
            _logger.info("Normalized", **normalized)
            
            property_match, confidence = await match_address_to_property(session, addr)
            if property_match:
                _logger.success(
                    "Match found",
                    prop_id=property_match.prop_id,
                    confidence=confidence,
                    property_address=property_match.situs_address,
                )
            else:
                _logger.info("No match found", confidence=confidence)


async def main() -> None:
    """Run all tests."""
    configure_logging(_settings.log_level)
    await init_database()
    
    _logger.info("Starting data source tests")
    
    # Test each client
    await test_austin_311()
    await test_code_compliance()
    await test_noaa_storm_events()
    
    # Test address matching
    await test_address_matching()
    
    _logger.success("All tests complete")


if __name__ == "__main__":
    asyncio.run(main())

