"""Base client for data source ingestion with common patterns."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from ..utils.logging import get_logger

_logger = get_logger(component="ingestion_client")
_settings = get_settings()


class BaseIngestionClient(ABC):
    """Base class for data source ingestion clients."""

    def __init__(
        self,
        base_url: str,
        timeout: float | None = None,
        max_retries: int = 5,
    ):
        self.base_url = base_url
        self.timeout = timeout or _settings.request_timeout_seconds
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": "LocalLift/1.0"},
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _fetch(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Fetch data from API with retry logic."""
        try:
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                _logger.warning("Rate limit exceeded", url=url)
                raise
            elif e.response.status_code >= 500:
                _logger.error("Server error", url=url, status_code=e.response.status_code)
                raise
            else:
                _logger.error("HTTP error", url=url, status_code=e.response.status_code, response=e.response.text)
                raise
        except Exception as e:
            _logger.exception("Error fetching data", url=url, error=str(e))
            raise

    @abstractmethod
    async def iter_records(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Iterate over records from the data source."""
        raise NotImplementedError

    async def fetch_all(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Fetch all records (or up to limit) from the data source."""
        records = []
        async for record in self.iter_records(start_date=start_date, end_date=end_date, **kwargs):
            records.append(record)
            if limit and len(records) >= limit:
                break
        return records

