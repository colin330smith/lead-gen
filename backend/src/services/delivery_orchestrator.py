"""Orchestrates lead delivery across multiple channels."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.contractor import Contractor
from ..models.lead import Lead
from ..models.property import Property
from ..services.email_delivery import EmailDeliveryService
from ..services.engagement_tracker import EngagementTracker
from ..services.lead_generation import LeadGenerationService
from ..services.webhook_delivery import WebhookDeliveryService
from ..utils.logging import get_logger

_logger = get_logger(component="delivery_orchestrator")


class DeliveryOrchestrator:
    """Orchestrates lead delivery via multiple channels."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.email_service = EmailDeliveryService()
        self.webhook_service = WebhookDeliveryService()
        self.engagement_tracker = EngagementTracker(session)
        self.lead_service = LeadGenerationService(session)

    async def deliver_lead(
        self,
        lead_id: int,
        delivery_methods: list[str] | None = None,
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Deliver a lead via specified methods.
        
        Args:
            lead_id: Lead to deliver
            delivery_methods: List of methods (email, webhook, api). Default: all configured
            webhook_url: Optional webhook URL (if not in contractor settings)
        
        Returns:
            Delivery results for each method
        """
        _logger.info("Delivering lead", lead_id=lead_id, methods=delivery_methods)
        
        # Get lead and related data
        lead = await self.session.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        if not lead.contractor_id:
            raise ValueError(f"Lead {lead_id} not assigned to contractor")
        
        contractor = await self.session.get(Contractor, lead.contractor_id)
        if not contractor:
            raise ValueError(f"Contractor {lead.contractor_id} not found")
        
        property = await self.session.get(Property, lead.prop_id)
        if not property:
            raise ValueError(f"Property {lead.prop_id} not found")
        
        # Default to all methods if not specified
        if not delivery_methods:
            delivery_methods = ["email"]
            # Add webhook if contractor has webhook URL configured
            if webhook_url or getattr(contractor, "webhook_url", None):
                delivery_methods.append("webhook")
        
        results = {}
        
        # Deliver via email
        if "email" in delivery_methods:
            if not contractor.email:
                _logger.warning("Contractor has no email, skipping email delivery", contractor_id=contractor.id)
                results["email"] = {
                    "delivered": False,
                    "error": "Contractor email not configured",
                }
            else:
                email_result = await self.email_service.deliver_lead_email(
                    lead, contractor, property
                )
                results["email"] = email_result
                
                # Log delivery
                await self.engagement_tracker.log_delivery(
                    lead_id=lead_id,
                    delivery_method="email",
                    status="delivered" if email_result.get("delivered") else "failed",
                    contractor_id=contractor.id,
                    recipient=contractor.email,
                    tracking_id=email_result.get("tracking_id"),
                    error_message=email_result.get("error"),
                )
        
        # Deliver via webhook
        if "webhook" in delivery_methods:
            webhook_url_to_use = webhook_url or getattr(contractor, "webhook_url", None)
            if not webhook_url_to_use:
                _logger.warning("No webhook URL configured, skipping webhook delivery", contractor_id=contractor.id)
                results["webhook"] = {
                    "delivered": False,
                    "error": "Webhook URL not configured",
                }
            else:
                webhook_result = await self.webhook_service.deliver_lead_webhook(
                    lead, contractor, property, webhook_url_to_use
                )
                results["webhook"] = webhook_result
                
                # Log delivery
                await self.engagement_tracker.log_delivery(
                    lead_id=lead_id,
                    delivery_method="webhook",
                    status="delivered" if webhook_result.get("delivered") else "failed",
                    contractor_id=contractor.id,
                    recipient=webhook_url_to_use,
                    tracking_id=webhook_result.get("tracking_id"),
                    error_message=webhook_result.get("error"),
                )
        
        # Mark lead as delivered if at least one method succeeded
        if any(r.get("delivered", False) for r in results.values()):
            await self.lead_service.mark_lead_delivered(lead_id, delivery_method=",".join(delivery_methods))
            _logger.success("Lead delivered successfully", lead_id=lead_id, results=results)
        else:
            _logger.error("All delivery methods failed", lead_id=lead_id, results=results)
        
        return {
            "lead_id": lead_id,
            "contractor_id": contractor.id,
            "results": results,
            "success": any(r.get("delivered", False) for r in results.values()),
        }

    async def deliver_assigned_leads(
        self,
        contractor_id: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Deliver all assigned but not yet delivered leads.
        
        Args:
            contractor_id: Optional contractor filter
            limit: Maximum leads to deliver
        
        Returns:
            Delivery summary
        """
        from sqlalchemy import select
        
        query = select(Lead).where(
            Lead.status == "assigned",
            Lead.delivered_at.is_(None),
        )
        
        if contractor_id:
            query = query.where(Lead.contractor_id == contractor_id)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        leads = result.scalars().all()
        
        _logger.info("Delivering assigned leads", count=len(leads), contractor_id=contractor_id)
        
        delivered = 0
        failed = 0
        results = []
        
        for lead in leads:
            try:
                delivery_result = await self.deliver_lead(lead.id)
                if delivery_result.get("success"):
                    delivered += 1
                else:
                    failed += 1
                results.append(delivery_result)
            except Exception as e:
                _logger.exception("Error delivering lead", lead_id=lead.id, error=str(e))
                failed += 1
        
        _logger.success(
            "Bulk delivery complete",
            total=len(leads),
            delivered=delivered,
            failed=failed,
        )
        
        return {
            "total": len(leads),
            "delivered": delivered,
            "failed": failed,
            "results": results,
        }

