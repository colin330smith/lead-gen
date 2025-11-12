"""Lead generation service for creating leads from scored properties."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.lead import Lead
from ..models.lead_score import LeadScore
from ..models.property import Property
from ..models.contractor import ContractorTerritory
from ..utils.logging import get_logger

_logger = get_logger(component="lead_generation")


class LeadGenerationService:
    """Service for generating leads from scored properties."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_leads(
        self,
        trade: str,
        min_score: float = 0.6,
        max_leads: int | None = None,
        zip_codes: list[str] | None = None,
        exclude_assigned: bool = True,
    ) -> list[Lead]:
        """
        Generate leads for a specific trade.
        
        Args:
            trade: Trade type (roofing, hvac, siding, electrical)
            min_score: Minimum intent score (0.0 to 1.0)
            max_leads: Maximum number of leads to generate
            zip_codes: Optional list of ZIP codes to filter
            exclude_assigned: Exclude properties already assigned to contractors
        
        Returns:
            List of generated Lead objects
        """
        _logger.info(
            "Generating leads",
            trade=trade,
            min_score=min_score,
            max_leads=max_leads,
        )
        
        # Query high-intent properties
        query = (
            select(LeadScore, Property)
            .join(Property, LeadScore.prop_id == Property.prop_id)
            .where(
                LeadScore.trade == trade,
                LeadScore.intent_score >= min_score,
            )
            .order_by(LeadScore.intent_score.desc())
        )
        
        # Filter by ZIP codes if provided
        if zip_codes:
            query = query.where(Property.situs_zip.in_(zip_codes))
        
        # Exclude already assigned properties
        if exclude_assigned:
            existing_leads = select(Lead.prop_id).where(
                Lead.trade == trade,
                Lead.status.in_(["assigned", "delivered"]),
            )
            query = query.where(~LeadScore.prop_id.in_(existing_leads))
        
        # Limit results
        if max_leads:
            query = query.limit(max_leads)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        leads = []
        for score_row, property_row in rows:
            # Check if lead already exists
            existing = await self.session.execute(
                select(Lead).where(
                    Lead.prop_id == score_row.prop_id,
                    Lead.trade == trade,
                    Lead.status == "generated",
                )
            )
            if existing.scalar_one_or_none():
                continue  # Skip if already generated
            
            # Calculate quality score
            quality_score = await self._calculate_quality_score(
                score_row, property_row
            )
            
            # Create lead
            lead = Lead(
                prop_id=score_row.prop_id,
                trade=trade,
                intent_score=score_row.intent_score,
                quality_score=quality_score,
                status="generated",
                zip_code=property_row.situs_zip,
                market_value=property_row.market_value,
                signal_count=score_row.signal_count,
                violation_count=score_row.violation_count,
                request_count=score_row.request_count,
                expires_at=datetime.utcnow() + timedelta(days=30),  # Leads expire in 30 days
                metadata={
                    "baseline_score": score_row.baseline_score,
                    "score_components": score_row.score_components,
                },
            )
            
            self.session.add(lead)
            leads.append(lead)
        
        await self.session.commit()
        
        _logger.success("Leads generated", count=len(leads), trade=trade)
        return leads

    async def _calculate_quality_score(
        self,
        score: LeadScore,
        property: Property,
    ) -> float:
        """
        Calculate overall quality score for a lead.
        
        Factors:
        - Intent score (primary)
        - Contact data availability
        - Property value
        - Signal recency
        """
        quality = score.intent_score  # Start with intent score
        
        # Boost for high-value properties
        if property.market_value:
            if property.market_value > 500_000:
                quality += 0.1
            elif property.market_value > 300_000:
                quality += 0.05
        
        # Boost for recent signals
        if score.signal_count and score.signal_count > 0:
            quality += min(0.1, score.signal_count * 0.02)
        
        # Check for contact enrichment
        from ..models.contact_enrichment import ContactEnrichment
        contact = await self.session.execute(
            select(ContactEnrichment).where(
                ContactEnrichment.prop_id == property.prop_id,
                ContactEnrichment.enrichment_status == "success",
            )
        )
        if contact.scalar_one_or_none():
            quality += 0.1  # Boost for available contact data
        
        return min(1.0, quality)

    async def assign_lead_to_contractor(
        self,
        lead_id: int,
        contractor_id: int,
        assigned_by: str = "system",
    ) -> Lead:
        """Assign a lead to a contractor."""
        lead = await self.session.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        # Check territory exclusivity
        if lead.zip_code:
            territory = await self.session.execute(
                select(ContractorTerritory).where(
                    ContractorTerritory.contractor_id == contractor_id,
                    ContractorTerritory.zip_code == lead.zip_code,
                    ContractorTerritory.trade == lead.trade,
                    ContractorTerritory.status == "active",
                )
            )
            if not territory.scalar_one_or_none():
                raise ValueError(
                    f"Contractor {contractor_id} does not have territory for "
                    f"ZIP {lead.zip_code} and trade {lead.trade}"
                )
        
        lead.contractor_id = contractor_id
        lead.status = "assigned"
        lead.assigned_at = datetime.utcnow()
        lead.assigned_by = assigned_by
        
        await self.session.commit()
        await self.session.refresh(lead)
        
        _logger.info("Lead assigned", lead_id=lead_id, contractor_id=contractor_id)
        return lead

    async def mark_lead_delivered(
        self,
        lead_id: int,
        delivery_method: str = "api",
    ) -> Lead:
        """Mark a lead as delivered."""
        lead = await self.session.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        lead.status = "delivered"
        lead.delivered_at = datetime.utcnow()
        lead.delivery_method = delivery_method
        
        await self.session.commit()
        await self.session.refresh(lead)
        
        return lead

    async def mark_lead_converted(
        self,
        lead_id: int,
        conversion_value: float | None = None,
    ) -> Lead:
        """Mark a lead as converted."""
        lead = await self.session.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        lead.status = "converted"
        lead.converted_at = datetime.utcnow()
        if conversion_value:
            lead.conversion_value = conversion_value
        
        await self.session.commit()
        await self.session.refresh(lead)
        
        return lead

