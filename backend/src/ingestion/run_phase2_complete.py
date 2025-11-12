"""Complete Phase 2 workflow: Ingest, analyze, score."""

from __future__ import annotations

import asyncio

from ..config import get_settings
from ..database import _session_factory, create_tables, init_database
from ..analysis.correlation_analysis import calculate_signal_correlations
from ..analysis.pattern_discovery import discover_all_patterns
from ..services.score_scheduler import recalculate_scores
from ..validation.model_validation import validate_scoring_performance, validate_score_distribution
from ..utils.logging import configure_logging, get_logger
from .ingest_historical_signals import ingest_historical_data

_logger = get_logger(component="phase2_complete")
_settings = get_settings()


async def run_phase2_complete() -> None:
    """Run complete Phase 2 workflow."""
    configure_logging(_settings.log_level)
    await init_database()
    await create_tables()
    
    _logger.info("Starting Phase 2 complete workflow")
    
    # Step 1: Ingest historical data
    _logger.info("Step 1: Ingesting historical signals")
    await ingest_historical_data(months=24)
    
    async with _session_factory() as session:  # type: ignore[call-arg]
        # Step 2: Correlation analysis
        _logger.info("Step 2: Calculating signal correlations")
        correlations = await calculate_signal_correlations(session)
        _logger.info("Signal correlations", **correlations)
        
        # Step 3: Pattern discovery
        _logger.info("Step 3: Discovering patterns")
        patterns = await discover_all_patterns(session)
        _logger.info("Discovered patterns", **patterns)
        
        # Step 4: Recalculate scores for all trades
        _logger.info("Step 4: Calculating scores")
        for trade in ["roofing", "hvac", "siding", "electrical"]:
            _logger.info(f"Scoring for trade: {trade}")
            stats = await recalculate_scores(session, trade=trade, limit=10000)
            _logger.info(f"Scoring complete for {trade}", **stats)
        
        # Step 5: Validation
        _logger.info("Step 5: Validating scoring performance")
        performance = await validate_scoring_performance(session, sample_size=1000)
        _logger.info("Performance metrics", **performance)
        
        distribution = await validate_score_distribution(session)
        _logger.info("Score distribution", **distribution)
    
    _logger.success("Phase 2 complete workflow finished")


if __name__ == "__main__":
    asyncio.run(run_phase2_complete())

