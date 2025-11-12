"""Client for Austin Code Compliance violations data."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, AsyncIterator

import httpx

from .base_client import BaseIngestionClient
from ..utils.logging import get_logger

_logger = get_logger(component="austin_code_compliance")

# Socrata API endpoint
AUSTIN_SOCRATA_BASE = "https://data.austintexas.gov"
# Using Repeat Offender Violations dataset - has violation cases with dates and addresses
# Note: This is a subset (repeat offenders), but provides violation data
# May need to supplement with other datasets if available
CODE_COMPLIANCE_DATASET = "cdze-ufp8"  # Repeat Offender Violation Cases


class AustinCodeComplianceClient(BaseIngestionClient):
    """Client for Austin Code Compliance violations via Socrata API."""

    def __init__(self):
        super().__init__(base_url=AUSTIN_SOCRATA_BASE)
        self.dataset_id = CODE_COMPLIANCE_DATASET

    async def iter_records(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 5000,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Iterate over code compliance violations.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            limit: Maximum records per page
        """
        # Default to last 24 months if no dates provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

        # Socrata API endpoint pattern (to be confirmed)
        url = f"{self.base_url}/resource/{self.dataset_id}.json"
        
        offset = 0
        while True:
            params = {
                "$limit": limit,
                "$offset": offset,
                "$order": "violation_case_date DESC",
            }
            
            # Add date filters if provided
            if start_date:
                params["$where"] = f"violation_case_date >= '{start_date}T00:00:00.000'"
            if end_date:
                if "$where" in params:
                    params["$where"] += f" AND violation_case_date <= '{end_date}T23:59:59.999'"
                else:
                    params["$where"] = f"violation_case_date <= '{end_date}T23:59:59.999'"

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
                    _logger.error("Dataset not found. Need to identify correct dataset ID.")
                    raise
                raise

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize record to our schema."""
        # Map from Repeat Offender Violations dataset schema
        violation_date = record.get("violation_case_date")
        if violation_date:
            violation_date = self._parse_date(violation_date)
        
        return {
            "violation_id": record.get("violation_case_number") or f"CV-{record.get('rop_registration_number', 'unknown')}",
            "address": record.get("registered_address"),
            "violation_type": "Code Violation",  # General type from this dataset
            "violation_description": f"Repeat Offender Violation - Case {record.get('violation_case_number', 'N/A')}",
            "violation_date": violation_date,
            "compliance_date": None,  # Not available in this dataset
            "status": "open" if record.get("registration_status") == "Active" else "closed",
            "latitude": self._parse_float(record.get("latitude")),
            "longitude": self._parse_float(record.get("longitude")),
            "zip_code": record.get("zip_code"),
            "city": record.get("city"),
            "state": record.get("state"),
            "raw_data": record,
        }

    @staticmethod
    def _parse_date(date_str: str | None) -> str | None:
        """Parse date string to YYYY-MM-DD format."""
        if not date_str:
            return None
        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                try:
                    dt = datetime.strptime(date_str.split("T")[0], fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return None
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

