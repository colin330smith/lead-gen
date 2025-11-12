# Travis County Deed Records Data Source

## Overview

Travis County Deed Records provide intent signals through property ownership changes. New owners often require immediate maintenance and improvements.

## Data Source

**Status:** Researching API access  
**Update Frequency:** Daily (estimated)  
**Historical Data:** Available (estimated 12+ months)

## API Research

### Potential Endpoints
- **Travis County Clerk:** TBD
- **Public Records Portal:** TBD
- **Bulk Download:** TBD (may require manual download)

### Expected Data Schema
- Deed ID (unique identifier)
- Property address
- Deed number
- Deed book/page
- Deed date
- Deed type (sale, transfer, etc.)
- Grantor (seller)
- Grantee (buyer)
- Sale price (if available)
- Legal description

### Access Pattern
- **Authentication:** Public records (may require registration)
- **Rate Limits:** TBD
- **Filtering:** By date range, property address
- **Access Method:** May be bulk download rather than API

## Implementation Status

- [ ] Access method identified
- [ ] Data format confirmed
- [ ] Rate limits/documentation reviewed
- [ ] Data schema validated
- [ ] Client implementation complete
- [ ] Historical data ingestion complete (12 months)

## Next Steps

1. Research Travis County Clerk public records access
2. Identify data access method (API vs. bulk download)
3. Test data access and structure
4. Implement client or download script
5. Ingest historical data (12 months)

## Use Cases

- **New Owner Maintenance:** Recent sale → new owner → maintenance needs
- **Property Improvements:** Recent purchase → likely improvements needed
- **Property Value:** Sale price → affordability indicator
- **Timing:** Days since sale → urgency indicator

## Integration Notes

- Link to properties via address or prop_id
- Store in `deed_records` table
- Use deed date for temporal signal decay
- Sale price is valuable for affordability scoring
- Combine with property age for lifecycle analysis

## Signal Strength

- **High:** Sale within 30 days + high property value
- **Medium:** Sale within 90 days + medium property value
- **Low:** Sale > 90 days ago

