"""Lead verification and quality assurance service."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.lead import Lead
from ..models.property import Property
from ..models.contact_enrichment import ContactEnrichment
from ..utils.logging import get_logger

_logger = get_logger(component="lead_verification")


class LeadVerificationService:
    """Service for verifying lead quality and data completeness."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def verify_lead(self, lead_id: int) -> dict[str, Any]:
        """
        Verify a lead's quality and data completeness.
        
        Returns verification report with:
        - Data completeness score
        - Contact data availability
        - Property data quality
        - Signal verification
        """
        lead = await self.session.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        property = await self.session.get(Property, lead.prop_id)
        if not property:
            return {
                "lead_id": lead_id,
                "verified": False,
                "error": "Property not found",
            }
        
        verification = {
            "lead_id": lead_id,
            "verified": True,
            "scores": {},
            "data_quality": {},
            "warnings": [],
        }
        
        # Verify property data
        property_score = 0.0
        if property.situs_address:
            property_score += 0.3
        else:
            verification["warnings"].append("Missing property address")
        
        if property.situs_zip:
            property_score += 0.2
        else:
            verification["warnings"].append("Missing ZIP code")
        
        if property.market_value:
            property_score += 0.2
        else:
            verification["warnings"].append("Missing market value")
        
        if property.owner_name:
            property_score += 0.2
        else:
            verification["warnings"].append("Missing owner name")
        
        if property.owner_address:
            property_score += 0.1
        else:
            verification["warnings"].append("Missing owner address")
        
        verification["scores"]["property_data"] = property_score
        
        # Verify contact enrichment
        contact = await self.session.execute(
            select(ContactEnrichment).where(
                ContactEnrichment.prop_id == lead.prop_id,
                ContactEnrichment.enrichment_status == "success",
            )
        )
        contact_obj = contact.scalar_one_or_none()
        
        contact_score = 0.0
        if contact_obj:
            if contact_obj.owner_email:
                contact_score += 0.4
                if contact_obj.hunter_email_deliverability == "deliverable":
                    contact_score += 0.2
            if contact_obj.owner_phone:
                contact_score += 0.4
            verification["data_quality"]["has_contact_data"] = True
            verification["data_quality"]["email"] = contact_obj.owner_email
            verification["data_quality"]["phone"] = contact_obj.owner_phone
            verification["data_quality"]["email_deliverable"] = (
                contact_obj.hunter_email_deliverability == "deliverable"
            )
        else:
            verification["warnings"].append("No contact enrichment data")
            verification["data_quality"]["has_contact_data"] = False
        
        verification["scores"]["contact_data"] = contact_score
        
        # Verify signals
        signal_score = 0.0
        if lead.signal_count and lead.signal_count > 0:
            signal_score += 0.3
        if lead.violation_count and lead.violation_count > 0:
            signal_score += 0.3
        if lead.request_count and lead.request_count > 0:
            signal_score += 0.2
        
        verification["scores"]["signals"] = signal_score
        
        # Overall verification score
        overall_score = (property_score * 0.4) + (contact_score * 0.4) + (signal_score * 0.2)
        verification["scores"]["overall"] = overall_score
        verification["verified"] = overall_score >= 0.6  # Minimum threshold
        
        if not verification["verified"]:
            verification["warnings"].append(
                f"Overall verification score ({overall_score:.2f}) below threshold (0.6)"
            )
        
        return verification

    async def verify_batch(self, lead_ids: list[int]) -> list[dict[str, Any]]:
        """Verify multiple leads in batch."""
        results = []
        for lead_id in lead_ids:
            try:
                verification = await self.verify_lead(lead_id)
                results.append(verification)
            except Exception as e:
                _logger.exception("Error verifying lead", lead_id=lead_id, error=str(e))
                results.append({
                    "lead_id": lead_id,
                    "verified": False,
                    "error": str(e),
                })
        return results

