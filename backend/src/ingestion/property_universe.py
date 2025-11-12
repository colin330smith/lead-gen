from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Iterable

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import _session_factory, create_tables, init_database
from ..models.property import Property, bulk_properties_from_features
from ..utils.logging import configure_logging, get_logger
from .tcad_client import TCADClient
from .validation import run_quality_checks

_logger = get_logger(component="property_ingestion")
_settings = get_settings()

TCAD_FIELDS: list[str] = [
    "PROP_ID",
    "geo_id",
    "py_owner_name",
    "py_address",
    "situs_address",
    "situs_zip",
    "land_type_desc",
    "land_state_cd",
    "entities",
    "legal_desc",
    "deed_num",
    "deed_book_id",
    "deed_book_page",
    "deed_date",
    "market_value",
    "appraised_val",
    "assessed_val",
    "imprv_homesite_val",
    "imprv_non_homesite_val",
    "land_homesite_val",
    "land_non_homesite_val",
    "tcad_acres",
    "GIS_acres",
    "situs_num",
    "situs_street",
    "situs_street_prefx",
    "situs_street_suffix",
    "situs_city",
    "F1year_imprv",
    "py_owner_id",
    "CENTROID_X",
    "CENTROID_Y",
]


async def _export_raw_page(export_dir: Path, page_index: int, features: list[dict]) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    file_path = export_dir / f"tcad_page_{page_index:05d}.json"
    file_path.write_text(json.dumps(features, indent=2))


async def _upsert_properties(session: AsyncSession, properties: Iterable[Property]) -> int:
    props = list(properties)
    if not props:
        return 0

    # Deduplicate by prop_id, keeping the last occurrence
    seen = {}
    for prop in props:
        seen[prop.prop_id] = prop
    props = list(seen.values())

    # Batch inserts to avoid PostgreSQL parameter limit (65,535 parameters)
    # With ~35 fields per property, we can safely do ~1000 rows per batch
    # But SQL statement size is also a concern, so use smaller batches
    BATCH_SIZE = 100
    total_inserted = 0
    
    for i in range(0, len(props), BATCH_SIZE):
        batch = props[i : i + BATCH_SIZE]
        records = [prop.to_record() for prop in batch]
        stmt = insert(Property).values(records)
        update_columns = {
            key: stmt.excluded[key]
            for key in records[0].keys()
            if key not in {"prop_id"}
        }
        stmt = stmt.on_conflict_do_update(index_elements=[Property.prop_id], set_=update_columns)
        await session.execute(stmt)
        total_inserted += len(records)
    
    return total_inserted


async def ingest_property_universe() -> None:
    configure_logging(_settings.log_level)
    await init_database()
    await create_tables()

    total_inserted = 0
    page_index = 0

    async with _session_factory() as session:  # type: ignore[call-arg]
        async with TCADClient() as client:
            async for features in client.iter_features(
                where="1=1",
                out_fields=TCAD_FIELDS,
                order_by="PROP_ID ASC",
                return_geometry=True,
            ):
                properties = bulk_properties_from_features(features)
                inserted = await _upsert_properties(session, properties)
                await session.commit()

                if _settings.export_dir:
                    await _export_raw_page(Path(_settings.export_dir), page_index, features)

                total_inserted += inserted
                page_index += 1
                _logger.info(
                    "Processed TCAD page",
                    page=page_index,
                    inserted=inserted,
                    total=total_inserted,
                )

        metrics = await run_quality_checks(session)

    if total_inserted == 0:
        _logger.warning("No properties ingested from TCAD")
        raise RuntimeError("TCAD ingestion failed - no properties inserted")
    elif total_inserted < 350_000:
        _logger.warning(
            "Property count below expected threshold",
            total_records=total_inserted,
            expected_minimum=350_000,
            note="TCAD API should return ~376,596 records for full Travis County dataset"
        )
        _logger.info("Property ingestion completed with warnings", total_records=total_inserted, quality_metrics=metrics)
    else:
        _logger.success("Property ingestion completed", total_records=total_inserted, quality_metrics=metrics)


if __name__ == "__main__":
    asyncio.run(ingest_property_universe())
