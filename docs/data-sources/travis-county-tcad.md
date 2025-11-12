---
title: Travis County Appraisal District (TCAD) Property Data
description: Reference for accessing parcel-level property attributes from the Travis County GIS REST API.
last_updated: 2025-11-12
---

# Travis County Appraisal District (TCAD) Property Data

## Overview

Travis County publishes parcel-level appraisal data through its ArcGIS Server instance.  
The layer `Travis County Property (TCAD)` (`MapServer/3`) contains enriched parcel
attributes including ownership, situs address, valuation history, acreage, and deed
metadata. This dataset will be the primary source for building the Local Lift property
universe.

- **Base service**: `https://gis.traviscountytx.gov/server1/rest/services/Boundaries_and_Jurisdictions/TCAD/MapServer`
- **Primary layer ID**: `0` (Full TCAD parcel dataset with all properties - ~376,596 records)
- **Alternative (filtered)**: `TCAD_Travis_County_Property/MapServer/3` (County-owned properties only - ~740 records)
- **Spatial reference**: EPSG `2277` (NAD83 / Texas Central (ftUS))
- **Geometry**: Polygon (parcel footprint)

## Access Pattern

All queries are executed via HTTP `GET` to the `/query` endpoint:

```
GET /query?where=<WHERE>&outFields=<FIELDS>&f=json&resultRecordCount=<N>&resultOffset=<OFFSET>&orderByFields=<FIELD>
```

Key parameters:

| Parameter | Notes |
|-----------|-------|
| `where` | SQL-like filter. Use `1=1` to fetch all parcels. |
| `outFields` | Comma-separated list or `*`. Always limit to the fields required for ingestion. |
| `f` | Response format. Use `json` for structured responses. |
| `resultRecordCount` | Maximum records per page (default `2000`). Must not exceed server limit (`2000`). |
| `resultOffset` | Zero-based offset for pagination. |
| `orderByFields` | Required when paginating to ensure deterministic ordering (e.g. `PROP_ID ASC`). |
| `returnGeometry` | Set to `true` when geometry is required (default); use `false` to skip polygon payload. |
| `outSR` | Desired spatial reference (optional). Default is layer SR (`2277`). |

Pagination strategy:

1. Set `orderByFields=PROP_ID ASC`.
2. Loop with `resultOffset = page_index * page_size`.
3. Continue until `features` array is empty.

## Authentication & Rate Limits

The layer is public and does **not** require authentication or API keys.

ArcGIS Server does not publish explicit rate limits, but best practice is:

- Throttle to ~5 requests per second.
- Include a short delay (100–200 ms) between pages.
- Implement exponential backoff on HTTP 429 / 5xx responses.

## Important Fields

| Field | Description |
|-------|-------------|
| `PROP_ID` | TCAD internal property identifier (int). Stable primary key. |
| `geo_id` | Geographic ID / parcel identifier string. |
| `py_owner_name` | Owner name (uppercase, often includes ampersands). |
| `py_address` | Owner mailing address. |
| `situs_address` | Property situs address (includes city/ZIP). |
| `situs_zip` | Property ZIP code (string). |
| `land_type_desc` | TCAD land use classification (e.g., `SINGLE FAMILY RESIDENCE`). |
| `market_value`, `appraised_val`, `assessed_val` | Valuation figures (integers). |
| `imprv_homesite_val`, `imprv_non_homesite_val`, `land_homesite_val`, `land_non_homesite_val` | Valuation components. |
| `tcad_acres`, `GIS_acres` | Parcel acreage (double). |
| `legal_desc` | Legal description (string). |
| `deed_num`, `deed_book_id`, `deed_book_page`, `deed_date` | Deed metadata. |
| `entities` | Taxing entities for the parcel. |
| `CENTROID_X`, `CENTROID_Y` | Precomputed centroids in EPSG 2277. |

> **Data quality note**: `py_owner_name` and address fields can contain placeholder blanks (`" "`). Downstream pipeline should normalize whitespace and treat empty strings as `None`.

## Example Query

```http
GET https://gis.traviscountytx.gov/server1/rest/services/Boundaries_and_Jurisdictions/TCAD/MapServer/0/query\
    ?f=json\
    &where=1=1\
    &outFields=PROP_ID,py_owner_name,py_address,situs_address,situs_zip,market_value,tcad_acres\
    &orderByFields=PROP_ID%20ASC\
    &resultRecordCount=1000\
    &resultOffset=0
```

## Downloading in Bulk

ArcGIS supports exporting to file geodatabase or CSV via the `Export` operation, but
the Travis County server has the capability disabled for anonymous users. The pipeline
must therefore paginate the `query` endpoint and write the results locally.

## Data Freshness

`editingInfo.lastEditDate` indicates the dataset is refreshed regularly (timestamps observed within the last 24 hours).  
Plan to run a **daily incremental sync** once the ingestion pipeline is in production. For now, full refresh is acceptable.

## Usage Guidelines

- Respect the public data terms: data provided “for informational purposes” without warranties.
- Preserve `PROP_ID` as the immutable primary key.
- Convert monetary fields to integers (cents) or decimals as appropriate in PostgreSQL.
- Normalize owner and address strings (strip whitespace, title-case where helpful).
- Retain raw geometry (EPSG 2277) for spatial operations and derive WGS84 centroids for downstream use.

## Related Layers

- `Boundaries_and_Jurisdictions/TCAD_public/MapServer/0`: Similar parcel geometry without ownership details.
- `services.arcgis.com/0L95CJ0VTaxqcmED/.../EXTERNAL_tcad_parcel`: Mirror of parcel footprints (useful fallback for geometry).
- `services1.arcgis.com/7DRakJXKPEhwv0fM/.../(TCAD)_Parcel_poly_2020`: Historical parcel polygons (2020 snapshot) with limited attributes.

These secondary layers are **not** required for the core property universe but can help with change detection or geometry validation.

## Next Steps

1. Implement the ingestion client using `httpx` with async pagination.
2. Persist raw payloads in PostgreSQL using an `upsert` keyed on `PROP_ID`.
3. Log request metadata (URL, elapsed time, feature counts) with `loguru`.
4. Add validation checks (e.g., verify record count ≥ 370k, field completeness >95%).
