# City of Austin 311 Service Requests Data Source

## Overview

City of Austin 311 service requests provide real-time intent signals for property maintenance needs. Requests often indicate active problems requiring contractor services.

## Data Source

**Status:** Researching API access  
**Update Frequency:** Real-time or daily  
**Historical Data:** Available (estimated 12+ months)

## API Research

### Potential Endpoints
- **Socrata/Open Data Portal:** `data.austintexas.gov` (most likely)
- **311 API:** TBD
- **Bulk Download:** TBD

### Expected Data Schema
- Request ID (unique identifier)
- Request type/category
- Request description
- Request date
- Status (open, closed, in progress)
- Location (address, coordinates)
- ZIP code
- Resolution date
- Department/agency

### Access Pattern
- **Authentication:** Likely public/open data
- **Rate Limits:** TBD
- **Pagination:** Likely supported
- **Filtering:** By date range, status, request type, location

## Implementation Status

- [ ] API endpoint identified
- [ ] Authentication method confirmed
- [ ] Rate limits documented
- [ ] Data schema validated
- [ ] Client implementation complete
- [ ] Historical data ingestion complete (12 months)

## Next Steps

1. Research `data.austintexas.gov` Socrata portal
2. Identify 311 service requests dataset
3. Test API access and data structure
4. Implement client with pagination
5. Ingest historical data (12 months)

## Use Cases

- **HVAC:** HVAC-related requests → HVAC service needs
- **Electrical:** Electrical requests → electrical service needs
- **Plumbing:** Plumbing requests → plumbing service needs
- **General:** Multiple requests → property maintenance needs

## Integration Notes

- Link to properties via address matching
- Store in `service_requests` table
- Use request date for temporal signal decay
- Request type is critical for trade-specific scoring
- Combine with violations for correlation

## Signal Strength by Type

- **High:** HVAC, Electrical (safety/comfort critical)
- **Medium:** Plumbing, General maintenance
- **Low:** Information requests, non-urgent

