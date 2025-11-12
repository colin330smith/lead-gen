"""Property lifecycle modeling for maintenance window prediction."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from ..utils.logging import get_logger

_logger = get_logger(component="property_lifecycle")

# Lifecycle stages based on property age
LIFECYCLE_STAGES = {
    "warranty": (0, 5),  # Years 0-5: Minimal maintenance (warranty period)
    "routine": (5, 15),  # Years 5-15: Routine maintenance
    "major_replacement": (15, 25),  # Years 15-25: Major system replacements
    "ongoing_maintenance": (25, 999),  # Years 25+: Ongoing major maintenance
}


def calculate_property_age(first_improvement_year: int | None) -> int | None:
    """Calculate property age from first improvement year."""
    if first_improvement_year is None:
        return None
    return datetime.now().year - first_improvement_year


def get_lifecycle_stage(property_age: int | None) -> Literal["warranty", "routine", "major_replacement", "ongoing_maintenance", "unknown"]:
    """
    Determine property lifecycle stage based on age.
    
    Returns:
        Lifecycle stage name
    """
    if property_age is None:
        return "unknown"
    
    for stage, (min_age, max_age) in LIFECYCLE_STAGES.items():
        if min_age <= property_age < max_age:
            return stage
    
    return "ongoing_maintenance"  # Default for very old properties


def is_in_maintenance_window(
    property_age: int | None,
    window_start: int = 15,
    window_end: int = 25,
) -> bool:
    """
    Check if property is in a critical maintenance window.
    
    Default window is 15-25 years (major system replacement period).
    """
    if property_age is None:
        return False
    return window_start <= property_age <= window_end


def calculate_maintenance_urgency(
    property_age: int | None,
    years_since_last_improvement: int | None = None,
) -> float:
    """
    Calculate maintenance urgency score (0.0 to 1.0).
    
    Higher score = more urgent maintenance needs.
    """
    if property_age is None:
        return 0.0
    
    urgency = 0.0
    
    # Age-based urgency
    if 15 <= property_age <= 25:
        # Peak replacement window
        urgency = 0.8
    elif 25 < property_age <= 35:
        # Past peak but still high
        urgency = 0.6
    elif property_age > 35:
        # Very old, ongoing maintenance
        urgency = 0.7
    elif 10 <= property_age < 15:
        # Approaching peak
        urgency = 0.4
    else:
        # Low urgency (warranty/routine period)
        urgency = 0.2
    
    # Boost if no recent improvements
    if years_since_last_improvement is not None:
        if years_since_last_improvement > 15:
            urgency = min(1.0, urgency + 0.2)
        elif years_since_last_improvement > 10:
            urgency = min(1.0, urgency + 0.1)
    
    return urgency


def get_trade_specific_lifecycle_score(
    property_age: int | None,
    trade: str,
) -> float:
    """
    Calculate trade-specific lifecycle score.
    
    Different trades have different peak maintenance windows.
    """
    if property_age is None:
        return 0.0
    
    trade = trade.lower()
    
    if trade == "roofing":
        # Roofing peaks at 15-25 years
        if 15 <= property_age <= 25:
            return 0.9
        elif 10 <= property_age < 15 or 25 < property_age <= 30:
            return 0.6
        else:
            return 0.3
    
    elif trade == "hvac":
        # HVAC peaks at 10-20 years
        if 10 <= property_age <= 20:
            return 0.9
        elif 5 <= property_age < 10 or 20 < property_age <= 25:
            return 0.6
        else:
            return 0.3
    
    elif trade == "siding":
        # Siding peaks at 20-30 years
        if 20 <= property_age <= 30:
            return 0.9
        elif 15 <= property_age < 20 or 30 < property_age <= 35:
            return 0.6
        else:
            return 0.3
    
    elif trade == "electrical":
        # Electrical peaks at 20-30 years
        if 20 <= property_age <= 30:
            return 0.9
        elif 15 <= property_age < 20 or 30 < property_age <= 35:
            return 0.6
        else:
            return 0.3
    
    else:
        # Default: use general maintenance window
        return calculate_maintenance_urgency(property_age)

