# Austin Code Compliance Data Source

## Overview

Austin Code Compliance violations provide critical intent signals for property maintenance needs. Violations often indicate immediate or near-term contractor service requirements.

## Data Source

**Status:** Researching API access  
**Update Frequency:** Daily (estimated)  
**Historical Data:** Available (estimated 24+ months)

## API Research

### Potential Endpoints
- **Socrata/Open Data Portal:** `data.austintexas.gov` (most likely)
- **Direct API:** TBD
- **Bulk Download:** TBD

### Expected Data Schema
- Violation ID (unique identifier)
- Property address
- Violation type/category
- Violation description
- Violation date
- Compliance date
- Status (open, closed, resolved)
- Location (latitude, longitude)
- Inspector information

### Access Pattern
- **Authentication:** Likely public/open data (no auth required)
- **Rate Limits:** TBD (likely generous for public data)
- **Pagination:** Likely supported
- **Filtering:** By date range, status, violation type

## Implementation Status

- [ ] API endpoint identified
- [ ] Authentication method confirmed
- [ ] Rate limits documented
- [ ] Data schema validated
- [ ] Client implementation complete
- [ ] Historical data ingestion complete

## Next Steps

1. Research `data.austintexas.gov` Socrata portal
2. Identify code compliance dataset
3. Test API access and data structure
4. Implement client with pagination
5. Ingest historical data (24 months)

## Use Cases

- **Roofing:** Roof violations → immediate roofing needs
- **HVAC:** HVAC-related violations → HVAC service needs
- **Siding:** Exterior violations → siding/repair needs
- **General:** Multiple violations → property maintenance needs

## Integration Notes

- Link to properties via address matching
- Store in `code_violations` table
- Use violation date for temporal signal decay
- Combine with other signals for correlation analysis

