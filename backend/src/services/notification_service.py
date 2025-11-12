"""Notification service for contractors and admins."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.contractor import Contractor
from ..models.lead import Lead
from ..utils.logging import get_logger

_logger = get_logger(component="notification_service")


class NotificationService:
    """Service for sending notifications to contractors and admins."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def notify_new_leads_assigned(
        self,
        contractor_id: int,
        lead_count: int,
    ) -> dict[str, Any]:
        """Notify contractor of newly assigned leads."""
        contractor = await self.session.get(Contractor, contractor_id)
        if not contractor:
            raise ValueError(f"Contractor {contractor_id} not found")
        
        _logger.info(
            "Notifying contractor of new leads",
            contractor_id=contractor_id,
            lead_count=lead_count,
        )
        
        # In production, this would send email/SMS/push notification
        # For now, we log it
        notification = {
            "type": "new_leads_assigned",
            "contractor_id": contractor_id,
            "contractor_name": contractor.company_name,
            "lead_count": lead_count,
            "message": f"You have {lead_count} new lead(s) assigned to you.",
        }
        
        _logger.info("Notification sent", **notification)
        return notification

    async def notify_lead_delivered(
        self,
        lead_id: int,
        delivery_method: str,
    ) -> dict[str, Any]:
        """Notify contractor that lead was delivered."""
        lead = await self.session.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        if not lead.contractor_id:
            return {"notified": False, "error": "Lead not assigned"}
        
        contractor = await self.session.get(Contractor, lead.contractor_id)
        if not contractor:
            return {"notified": False, "error": "Contractor not found"}
        
        notification = {
            "type": "lead_delivered",
            "lead_id": lead_id,
            "contractor_id": contractor.id,
            "delivery_method": delivery_method,
            "message": f"Lead {lead_id} has been delivered via {delivery_method}.",
        }
        
        _logger.info("Delivery notification sent", **notification)
        return notification

    async def notify_lead_converted(
        self,
        lead_id: int,
        conversion_value: float | None = None,
    ) -> dict[str, Any]:
        """Notify admin of lead conversion."""
        lead = await self.session.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        notification = {
            "type": "lead_converted",
            "lead_id": lead_id,
            "contractor_id": lead.contractor_id,
            "conversion_value": conversion_value,
            "message": f"Lead {lead_id} has been converted" + (
                f" with value ${conversion_value:,.2f}" if conversion_value else ""
            ),
        }
        
        _logger.info("Conversion notification sent", **notification)
        return notification

    async def notify_delivery_failure(
        self,
        lead_id: int,
        delivery_method: str,
        error: str,
    ) -> dict[str, Any]:
        """Notify admin of delivery failure."""
        lead = await self.session.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        notification = {
            "type": "delivery_failure",
            "lead_id": lead_id,
            "contractor_id": lead.contractor_id,
            "delivery_method": delivery_method,
            "error": error,
            "message": f"Failed to deliver lead {lead_id} via {delivery_method}: {error}",
        }
        
        _logger.warning("Delivery failure notification", **notification)
        return notification

    async def get_contractor_notifications(
        self,
        contractor_id: int,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get recent notifications for a contractor."""
        # In production, this would query a notifications table
        # For now, return recent lead assignments
        from sqlalchemy import select
        
        query = select(Lead).where(
            Lead.contractor_id == contractor_id,
        ).order_by(Lead.assigned_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        leads = result.scalars().all()
        
        notifications = []
        for lead in leads:
            notifications.append({
                "type": "lead_assigned",
                "lead_id": lead.id,
                "trade": lead.trade,
                "intent_score": lead.intent_score,
                "assigned_at": lead.assigned_at.isoformat() if lead.assigned_at else None,
                "delivered_at": lead.delivered_at.isoformat() if lead.delivered_at else None,
            })
        
        return notifications

