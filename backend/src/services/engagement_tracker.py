"""Engagement tracking service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.engagement import DeliveryLog, LeadEngagement
from ..models.lead import Lead
from ..utils.logging import get_logger

_logger = get_logger(component="engagement_tracker")


class EngagementTracker:
    """Service for tracking lead engagement."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def track_email_open(
        self,
        lead_id: int,
        tracking_id: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> LeadEngagement:
        """Track email open event."""
        engagement = LeadEngagement(
            lead_id=lead_id,
            engagement_type="email_opened",
            user_agent=user_agent,
            ip_address=ip_address,
            engagement_data={"tracking_id": tracking_id},
        )
        self.session.add(engagement)
        await self.session.commit()
        await self.session.refresh(engagement)
        
        _logger.info("Email open tracked", lead_id=lead_id, tracking_id=tracking_id)
        return engagement

    async def track_email_click(
        self,
        lead_id: int,
        tracking_id: str,
        click_url: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> LeadEngagement:
        """Track email click event."""
        engagement = LeadEngagement(
            lead_id=lead_id,
            engagement_type="email_clicked",
            user_agent=user_agent,
            ip_address=ip_address,
            engagement_data={
                "tracking_id": tracking_id,
                "click_url": click_url,
            },
        )
        self.session.add(engagement)
        await self.session.commit()
        await self.session.refresh(engagement)
        
        _logger.info("Email click tracked", lead_id=lead_id, tracking_id=tracking_id, url=click_url)
        return engagement

    async def track_webhook_received(
        self,
        lead_id: int,
        webhook_url: str,
        response_status: int,
    ) -> LeadEngagement:
        """Track webhook delivery receipt."""
        engagement = LeadEngagement(
            lead_id=lead_id,
            engagement_type="webhook_received",
            engagement_data={
                "webhook_url": webhook_url,
                "response_status": response_status,
            },
        )
        self.session.add(engagement)
        await self.session.commit()
        await self.session.refresh(engagement)
        
        return engagement

    async def track_api_access(
        self,
        lead_id: int,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> LeadEngagement:
        """Track API access to lead."""
        engagement = LeadEngagement(
            lead_id=lead_id,
            engagement_type="api_accessed",
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.session.add(engagement)
        await self.session.commit()
        await self.session.refresh(engagement)
        
        return engagement

    async def log_delivery(
        self,
        lead_id: int,
        delivery_method: str,
        status: str,
        contractor_id: int | None = None,
        recipient: str | None = None,
        tracking_id: str | None = None,
        error_message: str | None = None,
        retry_count: int = 0,
    ) -> DeliveryLog:
        """Log a delivery attempt."""
        delivery_log = DeliveryLog(
            lead_id=lead_id,
            contractor_id=contractor_id,
            delivery_method=delivery_method,
            status=status,
            recipient=recipient,
            tracking_id=tracking_id,
            error_message=error_message,
            retry_count=retry_count,
            delivered_at=datetime.utcnow() if status == "delivered" else None,
        )
        self.session.add(delivery_log)
        await self.session.commit()
        await self.session.refresh(delivery_log)
        
        _logger.info(
            "Delivery logged",
            lead_id=lead_id,
            method=delivery_method,
            status=status,
        )
        return delivery_log

    async def get_lead_engagement_stats(self, lead_id: int) -> dict[str, Any]:
        """Get engagement statistics for a lead."""
        from sqlalchemy import func, select
        
        # Count engagements by type
        engagement_query = select(
            LeadEngagement.engagement_type,
            func.count(LeadEngagement.id).label("count"),
        ).where(LeadEngagement.lead_id == lead_id).group_by(LeadEngagement.engagement_type)
        
        result = await self.session.execute(engagement_query)
        engagement_counts = {row.engagement_type: row.count for row in result.fetchall()}
        
        # Get delivery logs
        delivery_query = select(DeliveryLog).where(DeliveryLog.lead_id == lead_id)
        delivery_result = await self.session.execute(delivery_query)
        delivery_logs = delivery_result.scalars().all()
        
        # Calculate delivery success rate
        total_deliveries = len(delivery_logs)
        successful_deliveries = sum(1 for log in delivery_logs if log.status == "delivered")
        delivery_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0.0
        
        return {
            "lead_id": lead_id,
            "engagement_counts": engagement_counts,
            "total_engagements": sum(engagement_counts.values()),
            "delivery_stats": {
                "total_attempts": total_deliveries,
                "successful": successful_deliveries,
                "failed": total_deliveries - successful_deliveries,
                "success_rate": round(delivery_rate, 2),
            },
            "has_email_open": engagement_counts.get("email_opened", 0) > 0,
            "has_email_click": engagement_counts.get("email_clicked", 0) > 0,
            "has_webhook_received": engagement_counts.get("webhook_received", 0) > 0,
            "has_api_access": engagement_counts.get("api_accessed", 0) > 0,
        }

