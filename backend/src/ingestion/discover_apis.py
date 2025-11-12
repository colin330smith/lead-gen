"""Script to help discover and test data source APIs."""

from __future__ import annotations

import asyncio
import json

import httpx

from ..utils.logging import configure_logging, get_logger

_logger = get_logger(component="api_discovery")
configure_logging("INFO")


async def test_socrata_portal(base_url: str, search_terms: list[str]) -> None:
    """Test Socrata portal for datasets."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try common Socrata endpoints
        endpoints = [
            f"{base_url}/api/catalog/v1",
            f"{base_url}/api/views",
            f"{base_url}/resource",
        ]
        
        for endpoint in endpoints:
            try:
                _logger.info("Testing endpoint", endpoint=endpoint)
                response = await client.get(endpoint)
                _logger.info("Response", status=response.status_code, url=response.url)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        _logger.info("JSON response", keys=list(data.keys())[:10] if isinstance(data, dict) else "list")
                    except Exception:
                        _logger.info("Non-JSON response", length=len(response.text))
            except Exception as e:
                _logger.debug("Endpoint failed", endpoint=endpoint, error=str(e))


async def test_noaa_storm_events() -> None:
    """Test NOAA Storm Events API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        endpoints = [
            "https://www.ncei.noaa.gov/stormevents/csv/",
            "https://www.ncdc.noaa.gov/stormevents/",
        ]
        
        for endpoint in endpoints:
            try:
                _logger.info("Testing NOAA endpoint", endpoint=endpoint)
                response = await client.get(endpoint)
                _logger.info("Response", status=response.status_code)
            except Exception as e:
                _logger.debug("Endpoint failed", endpoint=endpoint, error=str(e))


async def main() -> None:
    """Discover and test data source APIs."""
    _logger.info("Starting API discovery")
    
    # Test Austin Socrata portal
    await test_socrata_portal(
        "https://data.austintexas.gov",
        ["code", "compliance", "violation", "311", "service", "request"],
    )
    
    # Test NOAA
    await test_noaa_storm_events()
    
    _logger.info("API discovery complete")


if __name__ == "__main__":
    asyncio.run(main())

