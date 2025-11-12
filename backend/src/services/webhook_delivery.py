"""Webhook delivery service for leads."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from ..config import get_settings
from ..models.lead import Lead
from ..models.property import Property
from ..models.contractor import Contractor
from ..utils.logging import get_logger

_logger = get_logger(component="webhook_delivery")
_settings = get_settings()


class WebhookDeliveryService:
    """Service for delivering leads via webhooks."""

    def __init__(self):
        self.timeout = getattr(_settings, "webhook_timeout_seconds", 10.0)
        self.secret_key = getattr(_settings, "webhook_secret_key", None)

    async def deliver_lead_webhook(
        self,
        lead: Lead,
        contractor: Contractor,
        property: Property,
        webhook_url: str,
    ) -> dict[str, Any]:
        """
        Deliver a lead via webhook to contractor's endpoint.
        
        Returns delivery status and tracking info.
        """
        _logger.info(
            "Delivering lead via webhook",
            lead_id=lead.id,
            contractor_id=contractor.id,
            webhook_url=webhook_url,
        )
        
        try:
            # Prepare payload
            payload = self._prepare_webhook_payload(lead, contractor, property)
            
            # Generate signature if secret key is configured
            headers = {}
            if self.secret_key:
                signature = self._generate_signature(payload, self.secret_key)
                headers["X-LocalLift-Signature"] = signature
            
            # Send webhook with retry logic
            success = False
            error = None
            
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                reraise=True,
            ):
                with attempt:
                    try:
                        async with httpx.AsyncClient(timeout=self.timeout) as client:
                            response = await client.post(
                                webhook_url,
                                json=payload,
                                headers=headers,
                            )
                            response.raise_for_status()
                            success = True
                            _logger.success(
                                "Webhook delivered successfully",
                                lead_id=lead.id,
                                status_code=response.status_code,
                            )
                    except httpx.HTTPStatusError as e:
                        error = f"HTTP {e.response.status_code}: {e.response.text}"
                        _logger.warning(
                            "Webhook delivery failed",
                            lead_id=lead.id,
                            status_code=e.response.status_code,
                            error=error,
                        )
                        raise
                    except httpx.RequestError as e:
                        error = str(e)
                        _logger.warning("Webhook request error", lead_id=lead.id, error=error)
                        raise
            
            if success:
                return {
                    "delivered": True,
                    "method": "webhook",
                    "url": webhook_url,
                    "tracking_id": f"webhook_{lead.id}_{contractor.id}",
                }
            else:
                return {
                    "delivered": False,
                    "method": "webhook",
                    "error": error or "Unknown error",
                }
        
        except Exception as e:
            _logger.exception("Error delivering webhook", lead_id=lead.id, error=str(e))
            return {
                "delivered": False,
                "method": "webhook",
                "error": str(e),
            }

    def _prepare_webhook_payload(
        self,
        lead: Lead,
        contractor: Contractor,
        property: Property,
    ) -> dict[str, Any]:
        """Prepare webhook payload."""
        return {
            "event": "lead.assigned",
            "timestamp": lead.assigned_at.isoformat() if lead.assigned_at else None,
            "lead": {
                "id": lead.id,
                "prop_id": lead.prop_id,
                "trade": lead.trade,
                "intent_score": lead.intent_score,
                "quality_score": lead.quality_score,
                "status": lead.status,
                "zip_code": lead.zip_code,
                "market_value": lead.market_value,
                "signal_count": lead.signal_count,
                "violation_count": lead.violation_count,
                "request_count": lead.request_count,
                "generated_at": lead.generated_at.isoformat(),
                "expires_at": lead.expires_at.isoformat() if lead.expires_at else None,
            },
            "property": {
                "address": property.situs_address,
                "zip_code": property.situs_zip,
                "market_value": property.market_value,
                "owner_name": property.owner_name,
                "owner_address": property.owner_address,
            },
            "contractor": {
                "id": contractor.id,
                "company_name": contractor.company_name,
            },
        }

    def _generate_signature(self, payload: dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    def verify_signature(self, payload: dict[str, Any], signature: str) -> bool:
        """Verify webhook signature."""
        if not self.secret_key:
            return False
        
        expected_signature = self._generate_signature(payload, self.secret_key)
        return hmac.compare_digest(signature, expected_signature)

