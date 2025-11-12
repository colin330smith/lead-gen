from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Iterable

import httpx
from tenacity import AsyncRetrying, RetryError, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..config import get_settings
from ..utils.logging import get_logger

_logger = get_logger(component="tcad_client")
_settings = get_settings()


class TCADClient:
    """Async client for the Travis County Appraisal District property layer."""

    def __init__(
        self,
        base_url: str | None = None,
        page_size: int | None = None,
        timeout: float | None = None,
        retry_attempts: int | None = None,
        retry_backoff: float | None = None,
    ) -> None:
        self._base_url = base_url or _settings.tcad_base_url
        self._page_size = page_size or _settings.tcad_page_size
        self._timeout = timeout or _settings.request_timeout_seconds
        self._retry_attempts = retry_attempts or _settings.request_retry_attempts
        self._retry_backoff = retry_backoff or _settings.request_retry_backoff
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "TCADClient":
        await self._ensure_client()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.aclose()

    async def _ensure_client(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)

    async def aclose(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        await self._ensure_client()
        assert self._client is not None  # for type checker

        retrying = AsyncRetrying(
            retry=retry_if_exception_type(httpx.HTTPError),
            wait=wait_exponential(multiplier=self._retry_backoff, min=self._retry_backoff, max=10),
            stop=stop_after_attempt(self._retry_attempts),
            reraise=True,
        )

        async for attempt in retrying:
            with attempt:
                response = await self._client.get(self._base_url + "/query", params=params)
                response.raise_for_status()
                payload = response.json()
                if "error" in payload:
                    raise RuntimeError(f"TCAD API error: {payload['error']}")
                return payload
        raise RuntimeError("Unreachable retry loop")

    async def count(self, where: str = "1=1") -> int:
        params = {
            "f": "json",
            "where": where,
            "returnCountOnly": "true",
            "returnGeometry": "false",
        }
        payload = await self._request(params)
        count = int(payload.get("count", 0))
        _logger.info("TCAD count fetched", where=where, count=count)
        return count

    async def fetch_page(
        self,
        *,
        offset: int,
        where: str,
        out_fields: Iterable[str],
        order_by: str,
        return_geometry: bool,
    ) -> list[dict[str, Any]]:
        params = {
            "f": "json",
            "where": where,
            "outFields": ",".join(out_fields),
            "orderByFields": order_by,
            "resultRecordCount": self._page_size,
            "resultOffset": offset,
            "returnGeometry": str(return_geometry).lower(),
        }
        payload = await self._request(params)
        features = payload.get("features", [])
        if payload.get("exceededTransferLimit"):
            _logger.warning(
                "Transfer limit exceeded; consider reducing page size",
                offset=offset,
                page_size=self._page_size,
            )
        _logger.debug(
            "Fetched TCAD page",
            offset=offset,
            fetched=len(features),
        )
        return features

    async def iter_features(
        self,
        *,
        where: str = "1=1",
        out_fields: Iterable[str] | None = None,
        order_by: str = "PROP_ID ASC",
        return_geometry: bool = True,
    ) -> AsyncIterator[list[dict[str, Any]]]:
        fields = list(out_fields) if out_fields else ["*"]
        total = await self.count(where)
        if total == 0:
            _logger.warning("TCAD query returned zero records", where=where)
            return

        offset = 0
        while offset < total:
            try:
                features = await self.fetch_page(
                    offset=offset,
                    where=where,
                    out_fields=fields,
                    order_by=order_by,
                    return_geometry=return_geometry,
                )
            except RetryError as exc:
                _logger.exception("Failed to fetch page after retries", offset=offset)
                raise exc from exc.last_attempt.exception

            if not features:
                break

            yield features
            offset += self._page_size
            await asyncio.sleep(0.1)  # polite pacing


__all__ = ["TCADClient"]
