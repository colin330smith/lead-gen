"""Script to link signals (violations, 311, storms, deeds) to properties."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import insert

from ..config import get_settings
from ..database import _session_factory, create_tables, init_database
from ..models.code_violation import CodeViolation
from ..models.service_request import ServiceRequest
from ..models.storm_event import StormEvent
from ..models.deed_record import DeedRecord
from ..services.property_matching import match_signal_to_property
from ..utils.logging import configure_logging, get_logger
from .austin_311 import Austin311Client
from .austin_code_compliance import AustinCodeComplianceClient
from .noaa_storm_events import NOAAStormEventsClient

_logger = get_logger(component="link_signals")
_settings = get_settings()


async def link_311_requests(session, start_date: str | None = None, end_date: str | None = None) -> dict[str, int]:
    """Link 311 service requests to properties."""
    _logger.info("Linking 311 service requests to properties")
    
    stats = {"total": 0, "matched": 0, "unmatched": 0, "high_confidence": 0, "medium_confidence": 0}
    
    async with Austin311Client() as client:
        async for record in client.iter_records(start_date=start_date, end_date=end_date):
            stats["total"] += 1
            
            # Match to property
            prop_id, confidence, match_method = await match_signal_to_property(
                session, record, "311"
            )
            
            # Prepare record for database
            db_record = {
                "request_id": record["request_id"],
                "prop_id": prop_id,
                "address": record["address"],
                "request_type": record["request_type"],
                "request_category": record["request_category"],
                "request_description": record["request_description"],
                "request_status": record["request_status"],
                "zip_code": record["zip_code"],
                "latitude": record["latitude"],
                "longitude": record["longitude"],
                "requested_date": record["requested_date"],
                "closed_date": record["closed_date"],
                "last_updated": record["last_updated"],
                "source": "austin_311",
                "raw_data": record.get("raw_data", {}),
            }
            
            # Upsert
            stmt = insert(ServiceRequest).values(**db_record)
            stmt = stmt.on_conflict_do_update(
                index_elements=["request_id"],
                set_={
                    "prop_id": stmt.excluded.prop_id,
                    "request_status": stmt.excluded.request_status,
                    "closed_date": stmt.excluded.closed_date,
                    "last_updated": stmt.excluded.last_updated,
                    "updated_at": datetime.utcnow(),
                }
            )
            await session.execute(stmt)
            
            if prop_id:
                stats["matched"] += 1
                if match_method == "high_confidence":
                    stats["high_confidence"] += 1
                elif match_method == "medium_confidence":
                    stats["medium_confidence"] += 1
            else:
                stats["unmatched"] += 1
            
            if stats["total"] % 100 == 0:
                await session.commit()
                _logger.info("311 linking progress", **stats)
    
    await session.commit()
    _logger.success("311 linking complete", **stats)
    return stats


async def link_code_violations(session, start_date: str | None = None, end_date: str | None = None) -> dict[str, int]:
    """Link code compliance violations to properties."""
    _logger.info("Linking code compliance violations to properties")
    
    stats = {"total": 0, "matched": 0, "unmatched": 0, "high_confidence": 0, "medium_confidence": 0}
    
    async with AustinCodeComplianceClient() as client:
        async for record in client.iter_records(start_date=start_date, end_date=end_date):
            stats["total"] += 1
            
            # Match to property
            prop_id, confidence, match_method = await match_signal_to_property(
                session, record, "violation"
            )
            
            # Prepare record for database
            db_record = {
                "violation_id": record["violation_id"],
                "prop_id": prop_id,
                "address": record["address"],
                "violation_type": record["violation_type"],
                "violation_description": record["violation_description"],
                "violation_status": record["status"],
                "violation_date": record["violation_date"],
                "compliance_date": record["compliance_date"],
                "latitude": record["latitude"],
                "longitude": record["longitude"],
                "source": "austin_code_compliance",
                "raw_data": record.get("raw_data", {}),
            }
            
            # Upsert
            stmt = insert(CodeViolation).values(**db_record)
            stmt = stmt.on_conflict_do_update(
                index_elements=["violation_id"],
                set_={
                    "prop_id": stmt.excluded.prop_id,
                    "violation_status": stmt.excluded.violation_status,
                    "compliance_date": stmt.excluded.compliance_date,
                    "updated_at": datetime.utcnow(),
                }
            )
            await session.execute(stmt)
            
            if prop_id:
                stats["matched"] += 1
                if match_method == "high_confidence":
                    stats["high_confidence"] += 1
                elif match_method == "medium_confidence":
                    stats["medium_confidence"] += 1
            else:
                stats["unmatched"] += 1
            
            if stats["total"] % 100 == 0:
                await session.commit()
                _logger.info("Violation linking progress", **stats)
    
    await session.commit()
    _logger.success("Violation linking complete", **stats)
    return stats


async def link_storm_events(session, start_date: str | None = None, end_date: str | None = None) -> dict[str, int]:
    """Link storm events to properties by ZIP code and coordinates."""
    _logger.info("Linking storm events to properties")
    
    stats = {"total": 0, "matched": 0, "unmatched": 0}
    
    async with NOAAStormEventsClient() as client:
        async for record in client.iter_records(start_date=start_date, end_date=end_date):
            if not record:
                continue
                
            stats["total"] += 1
            
            # For storm events, match by ZIP code (geographic area)
            # We'll link to all properties in the ZIP code
            zip_code = record.get("zip_code")
            
            if zip_code:
                from sqlalchemy import select
                from ..models.property import Property
                
                # Find all properties in this ZIP
                query = select(Property.prop_id).where(Property.situs_zip == zip_code)
                result = await session.execute(query)
                prop_ids = [row[0] for row in result.fetchall()]
                
                if prop_ids:
                    stats["matched"] += len(prop_ids)
                    # Note: Storm events are linked to ZIP codes, not individual properties
                    # We store the event once with ZIP code reference
                    db_record = {
                        "event_id": record["event_id"],
                        "event_type": record["event_type"],
                        "event_date": record["event_date"],
                        "event_time": record.get("event_time"),
                        "county": record.get("county"),
                        "state": record.get("state"),
                        "latitude": record["latitude"],
                        "longitude": record["longitude"],
                        "zip_code": zip_code,
                        "magnitude": record.get("magnitude"),
                        "magnitude_type": record.get("magnitude_type"),
                        "damage_description": record.get("damage_description"),
                        "source": "noaa_storm_events",
                        "raw_data": record.get("raw_data", {}),
                    }
                    
                    stmt = insert(StormEvent).values(**db_record)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["event_id"],
                        set_={
                            "damage_description": stmt.excluded.damage_description,
                            "updated_at": datetime.utcnow(),
                        }
                    )
                    await session.execute(stmt)
                else:
                    stats["unmatched"] += 1
            else:
                stats["unmatched"] += 1
            
            if stats["total"] % 50 == 0:
                await session.commit()
                _logger.info("Storm event linking progress", **stats)
    
    await session.commit()
    _logger.success("Storm event linking complete", **stats)
    return stats


async def link_all_signals(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, dict[str, int]]:
    """Link all signal types to properties."""
    configure_logging(_settings.log_level)
    await init_database()
    await create_tables()
    
    # Default to last 12 months
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    _logger.info("Starting signal linking", start_date=start_date, end_date=end_date)
    
    results = {}
    
    async with _session_factory() as session:  # type: ignore[call-arg]
        # Link each signal type
        results["311"] = await link_311_requests(session, start_date, end_date)
        results["violations"] = await link_code_violations(session, start_date, end_date)
        results["storm_events"] = await link_storm_events(session, start_date, end_date)
    
    _logger.success("All signal linking complete", results=results)
    return results


if __name__ == "__main__":
    asyncio.run(link_all_signals())

