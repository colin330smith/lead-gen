"""Client for NOAA Storm Events data."""

from __future__ import annotations

import gzip
import io
from datetime import datetime
from typing import Any, AsyncIterator
from urllib.parse import urljoin

import csv
import httpx

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from .base_client import BaseIngestionClient
from ..utils.logging import get_logger

_logger = get_logger(component="noaa_storm_events")

NOAA_BASE_URL = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
TRAVIS_COUNTY_FIPS = "48453"  # Travis County, TX FIPS code


class NOAAStormEventsClient(BaseIngestionClient):
    """Client for NOAA Storm Events data via CSV downloads."""

    def __init__(self):
        super().__init__(base_url=NOAA_BASE_URL)

    async def iter_records(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        years: list[int] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Iterate over storm events.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            years: List of years to fetch (e.g., [2023, 2024])
        """
        # Default to last 12 months if no dates/years provided
        if not years:
            if start_date:
                start_year = int(start_date.split("-")[0])
            else:
                start_year = datetime.now().year - 1
            if end_date:
                end_year = int(end_date.split("-")[0])
            else:
                end_year = datetime.now().year
            years = list(range(start_year, end_year + 1))

        for year in years:
            filename = f"StormEvents_details-ftp_v1.0_d{year}_c*.csv.gz"
            # Try to find the latest version for this year
            url = f"{self.base_url}StormEvents_details-ftp_v1.0_d{year}_c*.csv.gz"
            
            # For now, construct known filename pattern
            # In production, would list directory to find latest
            try:
                # Try common filename patterns
                for month in range(1, 13):
                    test_url = f"{self.base_url}StormEvents_details-ftp_v1.0_d{year}_c{year:04d}{month:02d}*.csv.gz"
                    # Actually, we need to list the directory or use a known pattern
                    pass
                
                # Use a more direct approach - construct likely filename
                # Latest files typically have current year/month in name
                current_date = datetime.now()
                likely_filename = f"StormEvents_details-ftp_v1.0_d{year}_c{current_date.year:04d}{current_date.month:02d}*.csv.gz"
                
                # For now, fetch the file directly (will need to handle actual filename discovery)
                file_url = f"{self.base_url}StormEvents_details-ftp_v1.0_d{year}_c20250520.csv.gz"
                
                _logger.info("Fetching NOAA storm events", year=year, url=file_url)
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(file_url)
                    if response.status_code == 404:
                        _logger.warning("File not found, trying alternative", year=year, url=file_url)
                        continue
                    response.raise_for_status()
                    
                    # Decompress and parse CSV
                    with gzip.open(io.BytesIO(response.content), "rt", encoding="latin-1") as f:
                        if HAS_PANDAS:
                            df = pd.read_csv(f, low_memory=False)
                            
                            # Filter to Travis County, TX
                            if "CZ_FIPS" in df.columns:
                                df = df[df["CZ_FIPS"] == TRAVIS_COUNTY_FIPS]
                            elif "STATE_FIPS" in df.columns and "CZ_FIPS" in df.columns:
                                # Texas FIPS is 48, Travis County is 453
                                df = df[(df["STATE_FIPS"] == "48") & (df["CZ_FIPS"] == "453")]
                            
                            # Filter by date if provided
                            if start_date or end_date:
                                if "BEGIN_DATE" in df.columns:
                                    df["BEGIN_DATE_PARSED"] = pd.to_datetime(df["BEGIN_DATE"], errors="coerce")
                                    if start_date:
                                        df = df[df["BEGIN_DATE_PARSED"] >= pd.to_datetime(start_date)]
                                    if end_date:
                                        df = df[df["BEGIN_DATE_PARSED"] <= pd.to_datetime(end_date)]
                            
                            # Yield records
                            for _, row in df.iterrows():
                                record = self._normalize_record(row.to_dict())
                                if record:
                                    yield record
                        else:
                            # Fallback to CSV reader
                            reader = csv.DictReader(f)
                            for row in reader:
                                # Filter to Travis County
                                cz_fips = row.get("CZ_FIPS", "")
                                if cz_fips == TRAVIS_COUNTY_FIPS or (row.get("STATE_FIPS") == "48" and cz_fips == "453"):
                                    record = self._normalize_record(row)
                                    if record:
                                        yield record
                                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    _logger.warning("Storm events file not found for year", year=year)
                    continue
                raise
            except Exception as e:
                _logger.exception("Error processing storm events", year=year, error=str(e))
                continue

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Normalize record to our schema."""
        try:
            # Parse event date
            begin_date = record.get("BEGIN_DATE") or record.get("BEGIN_DATE_TIME")
            event_date = None
            if begin_date:
                try:
                    if HAS_PANDAS:
                        event_date = pd.to_datetime(begin_date).strftime("%Y-%m-%d")
                    else:
                        # Simple date parsing
                        from datetime import datetime as dt
                        # Try common formats
                        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
                            try:
                                event_date = dt.strptime(begin_date.split(" ")[0], fmt).strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue
                except Exception:
                    pass
            
            # Get event type
            event_type = record.get("EVENT_TYPE") or record.get("EVENTTYPE")
            
            # Get magnitude (varies by event type)
            magnitude = None
            magnitude_type = None
            if event_type and "HAIL" in event_type.upper():
                magnitude = self._parse_float(record.get("MAGNITUDE") or record.get("MAG"))
                magnitude_type = "inches"
            elif event_type and "WIND" in event_type.upper():
                magnitude = self._parse_float(record.get("MAGNITUDE") or record.get("MAG"))
                magnitude_type = "mph"
            
            # Get location
            lat = self._parse_float(record.get("BEGIN_LAT") or record.get("LATITUDE"))
            lng = self._parse_float(record.get("BEGIN_LON") or record.get("LONGITUDE"))
            
            # Get county and state
            county = record.get("CZ_NAME") or "Travis"
            state = record.get("STATE") or "TX"
            
            # Get ZIP if available
            zip_code = record.get("CZ_FIPS")  # Not directly available, would need lookup
            
            # Create event ID
            event_id = f"NOAA-{record.get('EPISODE_ID', 'unknown')}-{record.get('EVENT_ID', 'unknown')}"
            
            return {
                "event_id": event_id,
                "event_type": event_type,
                "event_date": event_date,
                "event_time": begin_date,  # Keep full datetime string
                "county": county,
                "state": state,
                "latitude": lat,
                "longitude": lng,
                "zip_code": zip_code,
                "magnitude": magnitude,
                "magnitude_type": magnitude_type,
                "damage_description": record.get("DAMAGE_PROPERTY") or record.get("EVENT_NARRATIVE"),
                "raw_data": record,
            }
        except Exception as e:
            _logger.warning("Error normalizing storm event record", error=str(e), record_keys=list(record.keys())[:5])
            return None

    @staticmethod
    def _parse_float(value: str | float | None) -> float | None:
        """Parse float value."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

