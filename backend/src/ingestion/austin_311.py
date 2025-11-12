"""Client for City of Austin 311 service requests data."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, AsyncIterator

import httpx

from .base_client import BaseIngestionClient
from ..utils.logging import get_logger

_logger = get_logger(component="austin_311")

# Socrata API endpoint
AUSTIN_SOCRATA_BASE = "https://data.austintexas.gov"
AUSTIN_311_DATASET = "xwdj-i9he"  # Austin 311 Public Data


class Austin311Client(BaseIngestionClient):
    """Client for Austin 311 service requests via Socrata API."""

    def __init__(self):
        super().__init__(base_url=AUSTIN_SOCRATA_BASE)
        self.dataset_id = AUSTIN_311_DATASET

    async def iter_records(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 5000,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Iterate over 311 service requests.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            limit: Maximum records per page
        """
        # Default to last 12 months if no dates provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        url = f"{self.base_url}/resource/{self.dataset_id}.json"
        
        offset = 0
        while True:
            params = {
                "$limit": limit,
                "$offset": offset,
                "$order": "sr_created_date DESC",
            }
            
            # Build date filter
            date_filter_parts = []
            if start_date:
                date_filter_parts.append(f"sr_created_date >= '{start_date}T00:00:00.000'")
            if end_date:
                date_filter_parts.append(f"sr_created_date <= '{end_date}T23:59:59.999'")
            
            if date_filter_parts:
                params["$where"] = " AND ".join(date_filter_parts)

            try:
                response = await self._fetch(url, params=params)
                data = response.json()
                
                if not data:
                    break
                
                for record in data:
                    yield self._normalize_record(record)
                
                # Check if we've reached the end
                if len(data) < limit:
                    break
                
                offset += limit
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    _logger.error("Dataset not found", dataset_id=self.dataset_id)
                    raise
                raise

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize record to our schema."""
        # Parse location coordinates
        lat = self._parse_float(record.get("sr_location_lat"))
        lng = self._parse_float(record.get("sr_location_long"))
        
        # Build full address
        address_parts = []
        if record.get("sr_location_street_number"):
            address_parts.append(record["sr_location_street_number"])
        if record.get("sr_location_street_name"):
            address_parts.append(record["sr_location_street_name"])
        full_address = " ".join(address_parts) if address_parts else record.get("sr_location", "")
        
        return {
            "request_id": record.get("sr_number"),
            "request_type": record.get("sr_type_desc"),
            "request_category": record.get("sr_department_desc"),
            "request_description": record.get("sr_type_desc"),  # Use type as description
            "request_status": record.get("sr_status_desc", "").lower().replace(" ", "_"),
            "address": full_address,
            "zip_code": record.get("sr_location_zip_code"),
            "latitude": lat,
            "longitude": lng,
            "requested_date": self._parse_date(record.get("sr_created_date")),
            "closed_date": self._parse_date(record.get("sr_closed_date")),
            "last_updated": self._parse_datetime(record.get("sr_updated_date")),
            "city": record.get("sr_location_city"),
            "county": record.get("sr_location_county"),
            "raw_data": record,
        }

    @staticmethod
    def _parse_date(date_str: str | None) -> str | None:
        """Parse date string to YYYY-MM-DD format."""
        if not date_str:
            return None
        try:
            # Handle ISO format with time
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d")
            # Handle other formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y"]:
                try:
                    dt = datetime.strptime(date_str.split(" ")[0], fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    @staticmethod
    def _parse_datetime(date_str: str | None) -> str | None:
        """Parse datetime string to ISO format."""
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.isoformat()
        except Exception:
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

