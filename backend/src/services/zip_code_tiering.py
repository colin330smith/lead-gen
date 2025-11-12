from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.property import Property
from ..models.zip_code_tier import ZipCodeTier
from ..utils.logging import get_logger

_logger = get_logger(component="zip_code_tiering")

TIER_PREMIUM = "PREMIUM"
TIER_STANDARD = "STANDARD"
TIER_VALUE = "VALUE"


async def calculate_zip_code_statistics(session: AsyncSession, zip_code: str) -> dict[str, float | int | None]:
    """Calculate statistics for a ZIP code from property data."""
    
    current_year = datetime.now().year
    
    # Base query for properties in this ZIP code with market value
    base_query = select(
        func.count(Property.prop_id).label("total_properties"),
        func.avg(Property.market_value).label("avg_market_value"),
        func.percentile_cont(0.5).within_group(Property.market_value).label("median_market_value"),
        func.min(Property.market_value).label("min_market_value"),
        func.max(Property.market_value).label("max_market_value"),
        func.avg(
            func.case(
                (Property.first_improvement_year.isnot(None), current_year - Property.first_improvement_year),
                else_=None
            )
        ).label("avg_property_age"),
        func.avg(
            func.case(
                (Property.owner_name.isnot(None), 1),
                else_=0
            )
        ).label("pct_with_owner_data"),
        func.avg(
            func.case(
                (
                    func.lower(Property.land_type_desc).like("%single%family%")
                    | func.lower(Property.land_type_desc).like("%sf%")
                    | func.lower(Property.land_type_desc).like("%residential%"),
                    1
                ),
                else_=0
            )
        ).label("pct_single_family"),
        func.avg(
            func.case(
                (
                    func.lower(Property.land_type_desc).like("%residential%")
                    | func.lower(Property.land_type_desc).like("%home%")
                    | func.lower(Property.land_type_desc).like("%house%"),
                    1
                ),
                else_=0
            )
        ).label("pct_residential"),
    ).where(
        Property.situs_zip == zip_code,
        Property.market_value.isnot(None),
        Property.market_value > 0
    )
    
    result = await session.execute(base_query)
    row = result.first()
    
    if not row or row.total_properties == 0:
        return {
            "total_properties": 0,
            "avg_market_value": None,
            "median_market_value": None,
            "min_market_value": None,
            "max_market_value": None,
            "avg_property_age": None,
            "pct_with_owner_data": None,
            "pct_single_family": None,
            "pct_residential": None,
        }
    
    return {
        "total_properties": row.total_properties or 0,
        "avg_market_value": float(row.avg_market_value) if row.avg_market_value else None,
        "median_market_value": float(row.median_market_value) if row.median_market_value else None,
        "min_market_value": float(row.min_market_value) if row.min_market_value else None,
        "max_market_value": float(row.max_market_value) if row.max_market_value else None,
        "avg_property_age": float(row.avg_property_age) if row.avg_property_age else None,
        "pct_with_owner_data": float(row.pct_with_owner_data * 100) if row.pct_with_owner_data else None,
        "pct_single_family": float(row.pct_single_family * 100) if row.pct_single_family else None,
        "pct_residential": float(row.pct_residential * 100) if row.pct_residential else None,
    }


def calculate_tier_score(stats: dict[str, float | int | None]) -> float:
    """Calculate a tier score based on ZIP code statistics.
    
    Higher scores indicate premium ZIP codes.
    Score components:
    - Median market value (weighted 50%)
    - Average market value (weighted 20%)
    - Property age (newer = higher score, weighted 10%)
    - Owner data completeness (weighted 10%)
    - Residential concentration (weighted 10%)
    """
    
    if stats["total_properties"] == 0:
        return 0.0
    
    # Normalize median value (assume max ~$2M for Austin area)
    median_value = stats.get("median_market_value") or 0
    median_score = min(median_value / 2_000_000, 1.0) * 0.5
    
    # Normalize average value
    avg_value = stats.get("avg_market_value") or 0
    avg_score = min(avg_value / 2_000_000, 1.0) * 0.2
    
    # Property age (newer = better, max age 50 years)
    avg_age = stats.get("avg_property_age") or 50
    age_score = max(0, (50 - avg_age) / 50) * 0.1
    
    # Owner data completeness
    owner_pct = stats.get("pct_with_owner_data") or 0
    owner_score = (owner_pct / 100) * 0.1
    
    # Residential concentration
    residential_pct = stats.get("pct_residential") or 0
    residential_score = (residential_pct / 100) * 0.1
    
    total_score = median_score + avg_score + age_score + owner_score + residential_score
    return round(total_score, 4)


def assign_tier(score: float) -> Literal["PREMIUM", "STANDARD", "VALUE"]:
    """Assign tier based on score.
    
    Thresholds:
    - PREMIUM: score >= 0.6
    - STANDARD: 0.3 <= score < 0.6
    - VALUE: score < 0.3
    """
    if score >= 0.6:
        return TIER_PREMIUM
    elif score >= 0.3:
        return TIER_STANDARD
    else:
        return TIER_VALUE


async def calculate_all_zip_code_tiers(session: AsyncSession) -> dict[str, int]:
    """Calculate and update tiers for all ZIP codes in the property database."""
    
    # Get all unique ZIP codes
    zip_query = select(Property.situs_zip).where(
        Property.situs_zip.isnot(None),
        Property.situs_zip != ""
    ).distinct()
    
    result = await session.execute(zip_query)
    zip_codes = [row[0] for row in result.fetchall()]
    
    _logger.info("Calculating ZIP code tiers", total_zip_codes=len(zip_codes))
    
    stats_by_tier = {TIER_PREMIUM: 0, TIER_STANDARD: 0, TIER_VALUE: 0}
    processed = 0
    
    for zip_code in zip_codes:
        try:
            stats = await calculate_zip_code_statistics(session, zip_code)
            
            if stats["total_properties"] == 0:
                continue
            
            score = calculate_tier_score(stats)
            tier = assign_tier(score)
            
            # Upsert tier record
            tier_record = ZipCodeTier(
                zip_code=zip_code,
                tier=tier,
                total_properties=stats["total_properties"],
                avg_market_value=stats["avg_market_value"],
                median_market_value=stats["median_market_value"],
                min_market_value=stats["min_market_value"],
                max_market_value=stats["max_market_value"],
                pct_single_family=stats["pct_single_family"],
                pct_residential=stats["pct_residential"],
                avg_property_age=stats["avg_property_age"],
                pct_with_owner_data=stats["pct_with_owner_data"],
                tier_score=score,
                last_calculated_at=datetime.utcnow(),
            )
            
            # Use PostgreSQL ON CONFLICT for upsert
            from sqlalchemy.dialects.postgresql import insert
            stmt = insert(ZipCodeTier).values(
                zip_code=tier_record.zip_code,
                tier=tier_record.tier,
                total_properties=tier_record.total_properties,
                avg_market_value=tier_record.avg_market_value,
                median_market_value=tier_record.median_market_value,
                min_market_value=tier_record.min_market_value,
                max_market_value=tier_record.max_market_value,
                pct_single_family=tier_record.pct_single_family,
                pct_residential=tier_record.pct_residential,
                avg_property_age=tier_record.avg_property_age,
                pct_with_owner_data=tier_record.pct_with_owner_data,
                tier_score=tier_record.tier_score,
                last_calculated_at=tier_record.last_calculated_at,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["zip_code"],
                set_={
                    "tier": stmt.excluded.tier,
                    "total_properties": stmt.excluded.total_properties,
                    "avg_market_value": stmt.excluded.avg_market_value,
                    "median_market_value": stmt.excluded.median_market_value,
                    "min_market_value": stmt.excluded.min_market_value,
                    "max_market_value": stmt.excluded.max_market_value,
                    "pct_single_family": stmt.excluded.pct_single_family,
                    "pct_residential": stmt.excluded.pct_residential,
                    "avg_property_age": stmt.excluded.avg_property_age,
                    "pct_with_owner_data": stmt.excluded.pct_with_owner_data,
                    "tier_score": stmt.excluded.tier_score,
                    "last_calculated_at": stmt.excluded.last_calculated_at,
                }
            )
            await session.execute(stmt)
            
            stats_by_tier[tier] += 1
            processed += 1
            
            if processed % 10 == 0:
                _logger.info("ZIP code tiering progress", processed=processed, total=len(zip_codes))
        
        except Exception as e:
            _logger.exception("Error calculating tier for ZIP code", zip_code=zip_code, error=str(e))
            continue
    
    await session.commit()
    
    _logger.success(
        "ZIP code tiering completed",
        total_processed=processed,
        premium=stats_by_tier[TIER_PREMIUM],
        standard=stats_by_tier[TIER_STANDARD],
        value=stats_by_tier[TIER_VALUE],
    )
    
    return stats_by_tier

