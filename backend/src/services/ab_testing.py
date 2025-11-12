"""A/B testing service for comparing model versions."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.feedback import ABTest, LeadFeedback
from ..models.lead import Lead
from ..utils.logging import get_logger

_logger = get_logger(component="ab_testing")


class ABTestingService:
    """Service for managing A/B tests between model versions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ab_test(
        self,
        test_name: str,
        model_a_version: str,
        model_b_version: str,
        split_ratio: float = 0.5,
        description: str | None = None,
    ) -> ABTest:
        """Create a new A/B test."""
        _logger.info("Creating A/B test", test_name=test_name, model_a=model_a_version, model_b=model_b_version)
        
        ab_test = ABTest(
            test_name=test_name,
            model_a_version=model_a_version,
            model_b_version=model_b_version,
            split_ratio=split_ratio,
            status="draft",
            description=description,
        )
        
        self.session.add(ab_test)
        await self.session.commit()
        await self.session.refresh(ab_test)
        
        return ab_test

    async def start_ab_test(self, test_id: int) -> ABTest:
        """Start an A/B test."""
        ab_test = await self.session.get(ABTest, test_id)
        if not ab_test:
            raise ValueError(f"A/B test {test_id} not found")
        
        ab_test.status = "running"
        ab_test.started_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(ab_test)
        
        _logger.info("A/B test started", test_id=test_id, test_name=ab_test.test_name)
        return ab_test

    async def assign_lead_to_test(
        self,
        lead_id: int,
        test_id: int,
    ) -> str:
        """
        Assign a lead to either model A or B based on split ratio.
        
        Returns: 'model_a' or 'model_b'
        """
        import random
        
        ab_test = await self.session.get(ABTest, test_id)
        if not ab_test or ab_test.status != "running":
            raise ValueError(f"A/B test {test_id} is not running")
        
        # Use lead_id as seed for consistent assignment
        random.seed(lead_id + test_id)
        assignment = "model_a" if random.random() < ab_test.split_ratio else "model_b"
        
        _logger.debug("Lead assigned to test", lead_id=lead_id, test_id=test_id, assignment=assignment)
        return assignment

    async def analyze_ab_test(self, test_id: int) -> dict[str, Any]:
        """Analyze A/B test results."""
        ab_test = await self.session.get(ABTest, test_id)
        if not ab_test:
            raise ValueError(f"A/B test {test_id} not found")
        
        # Get leads assigned to each model
        # In a real implementation, we'd track which model was used for each lead
        # For now, we'll use a simplified approach based on lead_id hash
        
        # Get all leads with feedback during test period
        if not ab_test.started_at:
            return {
                "error": "Test has not started yet",
            }
        
        query = (
            select(Lead, LeadFeedback)
            .join(LeadFeedback, Lead.id == LeadFeedback.lead_id)
            .where(LeadFeedback.submitted_at >= ab_test.started_at)
        )
        
        if ab_test.ended_at:
            query = query.where(LeadFeedback.submitted_at <= ab_test.ended_at)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        # Assign leads to models based on hash
        model_a_leads = []
        model_b_leads = []
        
        for lead, feedback in rows:
            import hashlib
            lead_hash = int(hashlib.md5(f"{lead.id}{test_id}".encode()).hexdigest(), 16)
            assignment = "model_a" if (lead_hash % 100) < (ab_test.split_ratio * 100) else "model_b"
            
            if assignment == "model_a":
                model_a_leads.append((lead, feedback))
            else:
                model_b_leads.append((lead, feedback))
        
        # Calculate conversion rates
        model_a_converted = sum(1 for _, f in model_a_leads if f.converted)
        model_a_total = len(model_a_leads)
        model_a_rate = (model_a_converted / model_a_total * 100) if model_a_total > 0 else 0.0
        
        model_b_converted = sum(1 for _, f in model_b_leads if f.converted)
        model_b_total = len(model_b_leads)
        model_b_rate = (model_b_converted / model_b_total * 100) if model_b_total > 0 else 0.0
        
        # Simple statistical test (chi-square would be better in production)
        # For now, just compare rates
        difference = model_b_rate - model_a_rate
        significance = abs(difference) > 5.0  # 5% difference threshold (simplified)
        
        winner = None
        if significance:
            winner = "model_b" if model_b_rate > model_a_rate else "model_a"
        else:
            winner = "no_difference"
        
        # Update test results
        ab_test.model_a_conversion_rate = model_a_rate
        ab_test.model_b_conversion_rate = model_b_rate
        ab_test.statistical_significance = 0.05 if significance else 0.5  # Simplified p-value
        ab_test.winner = winner
        
        await self.session.commit()
        
        return {
            "test_id": test_id,
            "test_name": ab_test.test_name,
            "model_a": {
                "version": ab_test.model_a_version,
                "conversion_rate": round(model_a_rate, 2),
                "total_leads": model_a_total,
                "converted": model_a_converted,
            },
            "model_b": {
                "version": ab_test.model_b_version,
                "conversion_rate": round(model_b_rate, 2),
                "total_leads": model_b_total,
                "converted": model_b_converted,
            },
            "difference": round(difference, 2),
            "statistically_significant": significance,
            "winner": winner,
        }

    async def complete_ab_test(self, test_id: int) -> ABTest:
        """Complete an A/B test."""
        ab_test = await self.session.get(ABTest, test_id)
        if not ab_test:
            raise ValueError(f"A/B test {test_id} not found")
        
        # Analyze results
        await self.analyze_ab_test(test_id)
        
        ab_test.status = "completed"
        ab_test.ended_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(ab_test)
        
        _logger.info("A/B test completed", test_id=test_id, winner=ab_test.winner)
        return ab_test

