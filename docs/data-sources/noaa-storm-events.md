# NOAA Storm Events Data Source

## Overview

NOAA Storm Events Database provides weather event data that correlates strongly with property damage and maintenance needs. Hail, wind, and severe weather events are high-value intent signals.

## Data Source

**Status:** Researching API access  
**Update Frequency:** Daily (estimated)  
**Historical Data:** Available (decades of data)

## API Research

### Known Endpoints
- **NCEI Storm Events Database:** `www.ncei.noaa.gov/stormevents/`
- **API Access:** Likely REST API or bulk download
- **Data Format:** CSV, JSON (TBD)

### Expected Data Schema
- Event ID (unique identifier)
- Event type (hail, wind, tornado, etc.)
- Event date/time
- Location (county, state, coordinates)
- Magnitude (hail size, wind speed, etc.)
- Damage description
- Property damage estimates

### Access Pattern
- **Authentication:** Public data (no auth required)
- **Rate Limits:** TBD
- **Filtering:** By date range, event type, geographic area
- **Geographic Coverage:** National (filter to Travis County, TX)

## Implementation Status

- [ ] API endpoint identified
- [ ] Data format confirmed
- [ ] Rate limits documented
- [ ] Data schema validated
- [ ] Client implementation complete
- [ ] Historical data ingestion complete (12 months)

## Next Steps

1. Research NCEI Storm Events API/documentation
2. Test data access and structure
3. Implement client with date range filtering
4. Filter to Travis County, TX
5. Ingest historical data (12 months)

## Use Cases

- **Roofing:** Hail events → roof damage → roofing needs
- **Siding:** Wind events → siding damage → siding needs
- **General:** Severe weather → property damage → contractor needs

## Integration Notes

- Link to properties via ZIP code and coordinates
- Store in `storm_events` table
- Use event date for temporal signal decay
- Magnitude is critical (larger hail = higher intent)
- Combine with code violations for correlation

## Signal Strength

- **High:** Hail > 1 inch, Wind > 60 mph, Tornado
- **Medium:** Hail 0.5-1 inch, Wind 40-60 mph
- **Low:** Hail < 0.5 inch, Wind < 40 mph

