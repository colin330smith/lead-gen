"""Ingest historical signal data and link to properties."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from ..config import get_settings
from ..database import _session_factory, create_tables, init_database
from ..utils.logging import configure_logging, get_logger
from .link_signals_to_properties import link_all_signals

_logger = get_logger(component="historical_ingestion")
_settings = get_settings()


async def ingest_historical_data(months: int = 24) -> None:
    """Ingest historical signal data for the specified number of months."""
    configure_logging(_settings.log_level)
    await init_database()
    await create_tables()
    
    # Calculate date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
    
    _logger.info(
        "Starting historical data ingestion",
        months=months,
        start_date=start_date,
        end_date=end_date,
    )
    
    # Link all signals
    results = await link_all_signals(start_date=start_date, end_date=end_date)
    
    _logger.success("Historical data ingestion complete", results=results)
    
    # Print summary
    total_signals = sum(r.get("total", 0) for r in results.values())
    total_matched = sum(r.get("matched", 0) for r in results.values())
    match_rate = (total_matched / total_signals * 100) if total_signals > 0 else 0
    
    _logger.info(
        "Ingestion summary",
        total_signals=total_signals,
        total_matched=total_matched,
        match_rate=f"{match_rate:.1f}%",
        details=results,
    )


if __name__ == "__main__":
    # Ingest last 24 months by default
    asyncio.run(ingest_historical_data(months=24))

