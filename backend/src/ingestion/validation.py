from __future__ import annotations

from typing import Dict, Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.property import Property
from ..utils.logging import get_logger

_logger = get_logger(component="data_validation")

REQUIRED_FIELDS: Iterable[str] = (
    "prop_id",
    "situs_address",
    "situs_zip",
    "market_value",
)

IMPORTANT_FIELDS: Iterable[str] = (
    "owner_name",
    "owner_address",
    "appraised_value",
    "situs_city",
)


async def _get_total_count(session: AsyncSession) -> int:
    stmt = select(func.count(Property.prop_id))
    return await session.scalar(stmt) or 0


async def _null_count(session: AsyncSession, column_name: str) -> int:
    column = getattr(Property, column_name)
    stmt = select(func.count()).where(column.is_(None))
    return await session.scalar(stmt) or 0


async def _empty_string_count(session: AsyncSession, column_name: str) -> int:
    column = getattr(Property, column_name)
    stmt = select(func.count()).where(column == "")
    return await session.scalar(stmt) or 0


async def _distinct_prop_id_count(session: AsyncSession) -> int:
    stmt = select(func.count(func.distinct(Property.prop_id)))
    return await session.scalar(stmt) or 0


async def _get_value_statistics(session: AsyncSession) -> Dict[str, float | int | None]:
    """Get statistics on market values."""
    stmt = select(
        func.count(Property.market_value).label("count"),
        func.avg(Property.market_value).label("avg"),
        func.min(Property.market_value).label("min"),
        func.max(Property.market_value).label("max"),
        func.percentile_cont(0.5).within_group(Property.market_value).label("median"),
    ).where(Property.market_value.isnot(None), Property.market_value > 0)
    
    result = await session.execute(stmt)
    row = result.first()
    
    return {
        "value_count": row.count if row else 0,
        "avg_market_value": float(row.avg) if row and row.avg else None,
        "min_market_value": float(row.min) if row and row.min else None,
        "max_market_value": float(row.max) if row and row.max else None,
        "median_market_value": float(row.median) if row and row.median else None,
    }


async def _get_zip_code_coverage(session: AsyncSession) -> Dict[str, int]:
    """Get ZIP code distribution."""
    stmt = select(
        Property.situs_zip,
        func.count(Property.prop_id).label("count")
    ).where(
        Property.situs_zip.isnot(None),
        Property.situs_zip != ""
    ).group_by(Property.situs_zip).order_by(func.count(Property.prop_id).desc()).limit(10)
    
    result = await session.execute(stmt)
    return {row.situs_zip: row.count for row in result.fetchall()}


async def run_quality_checks(session: AsyncSession) -> Dict[str, float | int | bool | Dict]:
    """Run comprehensive data quality checks on property data."""
    total = await _get_total_count(session)
    if total == 0:
        _logger.warning("Property table empty during validation")
        return {"total_records": 0}

    metrics: Dict[str, float | int | bool | Dict] = {
        "total_records": total,
    }

    # Check required fields
    for field in REQUIRED_FIELDS:
        missing = await _null_count(session, field)
        empty = await _empty_string_count(session, field) if hasattr(Property, field) else 0
        total_missing = missing + empty
        ratio = total_missing / total if total > 0 else 0.0
        metrics[f"missing_{field}_ratio"] = round(ratio, 4)
        metrics[f"missing_{field}_count"] = total_missing
        if ratio > 0.05:
            _logger.warning(
                "High null/empty ratio detected",
                field=field,
                ratio=ratio,
                missing=total_missing,
            )

    # Check important fields
    for field in IMPORTANT_FIELDS:
        missing = await _null_count(session, field)
        empty = await _empty_string_count(session, field) if hasattr(Property, field) else 0
        total_missing = missing + empty
        ratio = total_missing / total if total > 0 else 0.0
        metrics[f"missing_{field}_ratio"] = round(ratio, 4)
        metrics[f"missing_{field}_count"] = total_missing

    # Check for duplicates
    distinct_prop_ids = await _distinct_prop_id_count(session)
    metrics["duplicate_prop_ids"] = distinct_prop_ids != total
    metrics["unique_prop_ids"] = distinct_prop_ids
    if metrics["duplicate_prop_ids"]:
        _logger.error(
            "Duplicate prop_id values detected",
            total=total,
            distinct=distinct_prop_ids,
        )

    # Value statistics
    value_stats = await _get_value_statistics(session)
    metrics.update(value_stats)
    
    # Check for suspicious values (0 or negative)
    stmt = select(func.count(Property.prop_id)).where(
        Property.market_value.isnot(None),
        Property.market_value <= 0
    )
    invalid_values = await session.scalar(stmt) or 0
    metrics["invalid_market_values"] = invalid_values
    if invalid_values > 0:
        _logger.warning("Invalid market values detected", count=invalid_values)

    # ZIP code coverage
    zip_coverage = await _get_zip_code_coverage(session)
    metrics["top_zip_codes"] = zip_coverage

    # Overall data quality score (0-100)
    quality_score = 100.0
    for field in REQUIRED_FIELDS:
        ratio = metrics.get(f"missing_{field}_ratio", 0.0)
        quality_score -= ratio * 20  # Penalize missing required fields
    
    if metrics.get("duplicate_prop_ids"):
        quality_score -= 10  # Penalize duplicates
    
    metrics["data_quality_score"] = round(max(0, quality_score), 2)

    _logger.info("Data quality checks completed", **metrics)
    return metrics


__all__ = ["run_quality_checks"]
