"""Script to enrich property owner contacts using Hunter.io."""

from __future__ import annotations

import asyncio

from ..config import get_settings
from ..database import _session_factory, create_tables, init_database
from ..services.contact_enrichment import enrich_all_properties
from ..utils.logging import configure_logging, get_logger

_logger = get_logger(component="contact_enrichment_script")
_settings = get_settings()


async def main() -> None:
    configure_logging(_settings.log_level)
    await init_database()
    await create_tables()
    
    if not _settings.hunter_io_api_key:
        _logger.error("Hunter.io API key not configured. Set LOCALLIFT_HUNTER_IO_API_KEY environment variable.")
        return
    
    async with _session_factory() as session:  # type: ignore[call-arg]
        stats = await enrich_all_properties(session, batch_size=50, limit=None)
        _logger.info("Contact enrichment summary", **stats)


if __name__ == "__main__":
    asyncio.run(main())

