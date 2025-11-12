"""Service for collecting and processing contractor feedback."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.feedback import LeadFeedback
from ..models.lead import Lead
from ..utils.logging import get_logger

_logger = get_logger(component="feedback_collector")


class FeedbackCollector:
    """Service for collecting and managing contractor feedback."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def submit_feedback(
        self,
        lead_id: int,
        contractor_id: int,
        outcome: str,
        converted: bool = False,
        conversion_value: float | None = None,
        lead_quality_rating: int | None = None,
        accuracy_rating: int | None = None,
        contact_quality_rating: int | None = None,
        feedback_text: str | None = None,
        notes: str | None = None,
    ) -> LeadFeedback:
        """
        Submit feedback for a lead.
        
        Args:
            lead_id: Lead ID
            contractor_id: Contractor ID
            outcome: won, lost, no_response, not_interested, wrong_lead
            converted: Whether lead converted
            conversion_value: Revenue if converted
            lead_quality_rating: 1-5 rating
            accuracy_rating: 1-5 rating
            contact_quality_rating: 1-5 rating
            feedback_text: Free-form feedback
            notes: Additional notes
        """
        _logger.info("Submitting feedback", lead_id=lead_id, contractor_id=contractor_id, outcome=outcome)
        
        # Validate outcome
        valid_outcomes = ["won", "lost", "no_response", "not_interested", "wrong_lead"]
        if outcome not in valid_outcomes:
            raise ValueError(f"Invalid outcome: {outcome}. Must be one of {valid_outcomes}")
        
        # Validate ratings
        if lead_quality_rating and not (1 <= lead_quality_rating <= 5):
            raise ValueError("lead_quality_rating must be between 1 and 5")
        if accuracy_rating and not (1 <= accuracy_rating <= 5):
            raise ValueError("accuracy_rating must be between 1 and 5")
        if contact_quality_rating and not (1 <= contact_quality_rating <= 5):
            raise ValueError("contact_quality_rating must be between 1 and 5")
        
        # Check if feedback already exists
        existing = await self.session.execute(
            select(LeadFeedback).where(
                LeadFeedback.lead_id == lead_id,
                LeadFeedback.contractor_id == contractor_id,
            )
        )
        existing_feedback = existing.scalar_one_or_none()
        
        if existing_feedback:
            # Update existing feedback
            existing_feedback.outcome = outcome
            existing_feedback.converted = converted
            existing_feedback.conversion_value = conversion_value
            existing_feedback.lead_quality_rating = lead_quality_rating
            existing_feedback.accuracy_rating = accuracy_rating
            existing_feedback.contact_quality_rating = contact_quality_rating
            existing_feedback.feedback_text = feedback_text
            existing_feedback.notes = notes
            if converted and conversion_value:
                existing_feedback.conversion_date = datetime.utcnow()
            
            await self.session.commit()
            await self.session.refresh(existing_feedback)
            
            # Update lead conversion status
            await self._update_lead_conversion(lead_id, converted, conversion_value)
            
            _logger.success("Feedback updated", feedback_id=existing_feedback.id)
            return existing_feedback
        else:
            # Create new feedback
            feedback = LeadFeedback(
                lead_id=lead_id,
                contractor_id=contractor_id,
                outcome=outcome,
                converted=converted,
                conversion_value=conversion_value,
                conversion_date=datetime.utcnow() if converted else None,
                lead_quality_rating=lead_quality_rating,
                accuracy_rating=accuracy_rating,
                contact_quality_rating=contact_quality_rating,
                feedback_text=feedback_text,
                notes=notes,
            )
            
            self.session.add(feedback)
            await self.session.commit()
            await self.session.refresh(feedback)
            
            # Update lead conversion status
            await self._update_lead_conversion(lead_id, converted, conversion_value)
            
            _logger.success("Feedback submitted", feedback_id=feedback.id)
            return feedback

    async def _update_lead_conversion(
        self,
        lead_id: int,
        converted: bool,
        conversion_value: float | None,
    ) -> None:
        """Update lead conversion status."""
        lead = await self.session.get(Lead, lead_id)
        if lead and converted:
            lead.status = "converted"
            lead.converted_at = datetime.utcnow()
            if conversion_value:
                lead.conversion_value = conversion_value
            await self.session.commit()

    async def get_feedback_stats(
        self,
        contractor_id: int | None = None,
        trade: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, Any]:
        """Get feedback statistics."""
        query = select(LeadFeedback)
        
        if contractor_id:
            query = query.where(LeadFeedback.contractor_id == contractor_id)
        
        if date_from:
            query = query.where(LeadFeedback.submitted_at >= date_from)
        
        if date_to:
            query = query.where(LeadFeedback.submitted_at <= date_to)
        
        result = await self.session.execute(query)
        all_feedback = result.scalars().all()
        
        # Filter by trade if needed
        if trade:
            lead_ids = [f.lead_id for f in all_feedback]
            if lead_ids:
                from ..models.lead import Lead
                leads = await self.session.execute(
                    select(Lead).where(Lead.id.in_(lead_ids), Lead.trade == trade)
                )
                valid_lead_ids = {lead.id for lead in leads.scalars().all()}
                all_feedback = [f for f in all_feedback if f.lead_id in valid_lead_ids]
        
        # Calculate statistics
        total = len(all_feedback)
        if total == 0:
            return {
                "total_feedback": 0,
                "conversion_rate": 0.0,
                "outcome_distribution": {},
                "avg_ratings": {},
            }
        
        converted = sum(1 for f in all_feedback if f.converted)
        conversion_rate = (converted / total * 100) if total > 0 else 0.0
        
        # Outcome distribution
        outcome_counts = {}
        for feedback in all_feedback:
            outcome_counts[feedback.outcome] = outcome_counts.get(feedback.outcome, 0) + 1
        
        # Average ratings
        quality_ratings = [f.lead_quality_rating for f in all_feedback if f.lead_quality_rating]
        accuracy_ratings = [f.accuracy_rating for f in all_feedback if f.accuracy_rating]
        contact_ratings = [f.contact_quality_rating for f in all_feedback if f.contact_quality_rating]
        
        avg_quality = sum(quality_ratings) / len(quality_ratings) if quality_ratings else None
        avg_accuracy = sum(accuracy_ratings) / len(accuracy_ratings) if accuracy_ratings else None
        avg_contact = sum(contact_ratings) / len(contact_ratings) if contact_ratings else None
        
        # Total revenue
        total_revenue = sum(f.conversion_value or 0 for f in all_feedback if f.converted)
        
        return {
            "total_feedback": total,
            "converted": converted,
            "conversion_rate": round(conversion_rate, 2),
            "total_revenue": round(total_revenue, 2),
            "outcome_distribution": outcome_counts,
            "avg_ratings": {
                "lead_quality": round(avg_quality, 2) if avg_quality else None,
                "accuracy": round(avg_accuracy, 2) if avg_accuracy else None,
                "contact_quality": round(avg_contact, 2) if avg_contact else None,
            },
        }

