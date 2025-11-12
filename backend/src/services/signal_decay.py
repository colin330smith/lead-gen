"""Temporal signal decay service for intent signal strength calculation."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from ..utils.logging import get_logger

_logger = get_logger(component="signal_decay")

# Default half-life for 30-day prediction window
DEFAULT_HALF_LIFE_DAYS = 30


def calculate_signal_strength(
    base_score: float,
    signal_date: date | datetime | str | None,
    half_life_days: int = DEFAULT_HALF_LIFE_DAYS,
    reference_date: date | datetime | None = None,
) -> float:
    """
    Calculate signal strength with exponential decay.
    
    Signal strength halves every half_life_days.
    
    Examples (with 30-day half-life):
    - Signal 7 days ago: ~80% strength
    - Signal 15 days ago: ~71% strength
    - Signal 30 days ago: ~50% strength
    - Signal 60 days ago: ~25% strength
    
    Args:
        base_score: Base score for the signal (typically 1.0)
        signal_date: Date when the signal occurred
        half_life_days: Number of days for signal to decay to 50% (default: 30)
        reference_date: Reference date for calculation (default: today)
    
    Returns:
        Decayed signal strength (0.0 to base_score)
    """
    if signal_date is None:
        return 0.0
    
    # Parse date if string
    if isinstance(signal_date, str):
        try:
            signal_date = datetime.strptime(signal_date, "%Y-%m-%d").date()
        except ValueError:
            return 0.0
    
    # Convert datetime to date
    if isinstance(signal_date, datetime):
        signal_date = signal_date.date()
    
    # Use today as reference if not provided
    if reference_date is None:
        reference_date = date.today()
    elif isinstance(reference_date, datetime):
        reference_date = reference_date.date()
    
    # Calculate days ago
    days_ago = (reference_date - signal_date).days
    
    if days_ago < 0:
        # Future date - return full strength (or 0, depending on use case)
        return base_score
    
    if days_ago == 0:
        return base_score
    
    # Exponential decay: strength = base * 2^(-days_ago / half_life)
    decay_factor = 2 ** (-days_ago / half_life_days)
    strength = base_score * decay_factor
    
    return max(0.0, min(base_score, strength))


def calculate_signal_strength_for_property(
    signal_dates: list[date | datetime | str],
    base_score: float = 1.0,
    half_life_days: int = DEFAULT_HALF_LIFE_DAYS,
    aggregation: str = "sum",
) -> float:
    """
    Calculate aggregated signal strength for multiple signals on a property.
    
    Args:
        signal_dates: List of dates when signals occurred
        base_score: Base score per signal
        half_life_days: Half-life in days
        aggregation: How to aggregate ('sum', 'max', 'average')
    
    Returns:
        Aggregated signal strength
    """
    if not signal_dates:
        return 0.0
    
    strengths = [
        calculate_signal_strength(base_score, date, half_life_days)
        for date in signal_dates
    ]
    
    if aggregation == "sum":
        return sum(strengths)
    elif aggregation == "max":
        return max(strengths)
    elif aggregation == "average":
        return sum(strengths) / len(strengths) if strengths else 0.0
    else:
        return sum(strengths)


def get_signal_age_category(
    signal_date: date | datetime | str | None,
    reference_date: date | datetime | None = None,
) -> str:
    """
    Categorize signal age for analysis.
    
    Returns:
        'recent' (0-7 days), 'fresh' (8-30 days), 'aging' (31-90 days), 'stale' (90+ days)
    """
    if signal_date is None:
        return "stale"
    
    # Parse date
    if isinstance(signal_date, str):
        try:
            signal_date = datetime.strptime(signal_date, "%Y-%m-%d").date()
        except ValueError:
            return "stale"
    
    if isinstance(signal_date, datetime):
        signal_date = signal_date.date()
    
    if reference_date is None:
        reference_date = date.today()
    elif isinstance(reference_date, datetime):
        reference_date = reference_date.date()
    
    days_ago = (reference_date - signal_date).days
    
    if days_ago < 0:
        return "future"
    elif days_ago <= 7:
        return "recent"
    elif days_ago <= 30:
        return "fresh"
    elif days_ago <= 90:
        return "aging"
    else:
        return "stale"

