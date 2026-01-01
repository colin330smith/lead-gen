"""Script to verify all existing unverified emails in the database.

Run this ONCE to clean up any emails that were added before verification was implemented.
This will:
1. Find all contacts with emails that haven't been verified
2. Verify each email using Hunter.io Email Verifier API
3. Remove any emails that fail verification (to prevent bounces)

Usage:
    python -m backend.src.ingestion.verify_existing_emails
"""

from __future__ import annotations

import asyncio

from ..config import get_settings
from ..database import _session_factory, create_tables, init_database
from ..services.contact_enrichment import verify_existing_emails
from ..services.hunter_io import HunterIOClient
from ..utils.logging import configure_logging, get_logger

_logger = get_logger(component="verify_existing_emails")
_settings = get_settings()


async def main() -> None:
    configure_logging(_settings.log_level)
    await init_database()
    await create_tables()
    
    if not _settings.hunter_io_api_key:
        _logger.error("Hunter.io API key not configured. Set LOCALLIFT_HUNTER_IO_API_KEY environment variable.")
        return
    
    _logger.info("Starting verification of existing unverified emails...")
    _logger.warning("This will REMOVE any emails that fail verification to prevent bounces!")
    
    async with _session_factory() as session:  # type: ignore[call-arg]
        async with HunterIOClient(_settings.hunter_io_api_key) as hunter_client:
            stats = await verify_existing_emails(session, hunter_client)
            
            _logger.info("=" * 60)
            _logger.info("VERIFICATION COMPLETE")
            _logger.info("=" * 60)
            _logger.info(f"Total emails checked: {stats['total']}")
            _logger.info(f"Verified as VALID: {stats['verified_valid']}")
            _logger.info(f"Verified as INVALID (removed): {stats['verified_invalid']}")
            _logger.info(f"Failed to verify: {stats['failed']}")
            _logger.info("=" * 60)
            
            if stats['verified_invalid'] > 0:
                _logger.warning(
                    f"{stats['verified_invalid']} invalid emails were REMOVED from the database. "
                    "These would have bounced if sent."
                )


if __name__ == "__main__":
    asyncio.run(main())
