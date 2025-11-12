"""Script to calculate and update ZIP code tiers based on property statistics."""

from __future__ import annotations

import asyncio

from ..config import get_settings
from ..database import _session_factory, create_tables, init_database
from ..services.zip_code_tiering import calculate_all_zip_code_tiers
from ..utils.logging import configure_logging, get_logger

_logger = get_logger(component="zip_tiering_script")
_settings = get_settings()


async def main() -> None:
    configure_logging(_settings.log_level)
    await init_database()
    await create_tables()
    
    async with _session_factory() as session:  # type: ignore[call-arg]
        stats = await calculate_all_zip_code_tiers(session)
        _logger.info("ZIP code tiering summary", **stats)


if __name__ == "__main__":
    asyncio.run(main())

