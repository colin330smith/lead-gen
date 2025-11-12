"""
URGENT: Generate real leads immediately for contractors/investors.
This script will:
1. Score properties quickly
2. Generate leads from high-intent properties
3. Create sample contractors
4. Assign leads to contractors
"""

import asyncio
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session, _engine
from ..models.property import Property
from ..models.lead_score import LeadScore
from ..models.lead import Lead
from ..models.contractor import Contractor
from ..scoring.scoring_service import score_property
from ..utils.logging import get_logger

_logger = get_logger(component="generate_immediate_leads")


async def create_sample_contractor(session: AsyncSession) -> Contractor:
    """Create sample contractors if none exist."""
    existing = await session.execute(select(Contractor).limit(1))
    contractor = existing.scalar_one_or_none()
    
    if contractor:
        _logger.info(f"Using existing contractor: {contractor.company_name}")
        return contractor
    
    # Create sample contractors for each trade
    contractors = []
    for trade, name in [
        ("roofing", "Austin Roofing Pro"),
        ("hvac", "Central Texas HVAC"),
        ("siding", "Premium Siding Solutions"),
        ("electrical", "Austin Electric Co"),
    ]:
        contractor = Contractor(
            company_name=name,
            contact_name="Demo Contact",
            email=f"contact@{name.lower().replace(' ', '')}.com",
            phone="512-555-0100",
            trades=trade,
            subscription_tier="pro",
            status="active",
        )
        session.add(contractor)
        contractors.append(contractor)
    
    await session.commit()
    for c in contractors:
        await session.refresh(c)
    
    _logger.info(f"Created {len(contractors)} sample contractors")
    return contractors[0]  # Return roofing contractor


async def quick_score_and_generate(session: AsyncSession, trade: str = "roofing", max_leads: int = 50) -> int:
    """Quickly score properties and generate leads."""
    _logger.info(f"Scoring properties for {trade} leads...")
    
    # Get properties that aren't scored yet, limit to reasonable number
    result = await session.execute(
        select(Property)
        .where(
            ~Property.prop_id.in_(select(LeadScore.prop_id).where(LeadScore.trade == trade))
        )
        .limit(1000)  # Score 1000 properties quickly
    )
    
    properties = result.scalars().all()
    if not properties:
        _logger.warning("No unscored properties found")
        return 0
    
    scored_count = 0
    high_intent_count = 0
    
    for prop in properties:
        prop_id = prop.prop_id
        zip_code = getattr(prop, 'zip_code', None) or getattr(prop, 'zip', None)
        market_value = getattr(prop, 'market_value', None) or getattr(prop, 'total_value', None)
        try:
            # Score the property
            score_result = await score_property(session, prop_id, trade=trade)
            score_value = score_result.get("score", 0.0)
            
            if score_value > 0:
                # Save score
                lead_score = LeadScore(
                    prop_id=prop_id,
                    trade=trade,
                    intent_score=score_value,
                    baseline_score=score_value,
                    score_components=score_result.get("components", {}),
                    signal_count=0,
                    calculated_at=datetime.utcnow(),
                    score_version="v1.0",
                )
                session.add(lead_score)
                scored_count += 1
                
                # If high intent, create lead immediately
                if score_value >= 0.6 and high_intent_count < max_leads:
                    lead = Lead(
                        prop_id=prop_id,
                        trade=trade,
                        intent_score=score_value,
                        quality_score=score_value,
                        status="generated",
                        zip_code=zip_code,
                        market_value=market_value,
                        signal_count=0,
                        violation_count=0,
                        request_count=0,
                    )
                    session.add(lead)
                    high_intent_count += 1
                    
                    if high_intent_count % 10 == 0:
                        await session.commit()
                        _logger.info(f"Generated {high_intent_count} leads so far...")
            
        except Exception as e:
            _logger.warning(f"Error processing property {prop_id}: {e}")
            continue
    
    await session.commit()
    _logger.info(f"✅ Scored {scored_count} properties, generated {high_intent_count} leads")
    return high_intent_count


async def assign_leads_to_contractor(session: AsyncSession, contractor: Contractor, max_leads: int = 20) -> int:
    """Assign unassigned leads to contractor."""
    result = await session.execute(
        select(Lead)
        .where(
            Lead.status == "generated",
            Lead.trade.in_(contractor.trades.split(",")),
            Lead.contractor_id.is_(None)
        )
        .order_by(Lead.intent_score.desc())
        .limit(max_leads)
    )
    
    leads = result.scalars().all()
    assigned = 0
    
    for lead in leads:
        lead.contractor_id = contractor.id
        lead.status = "assigned"
        lead.assigned_at = datetime.utcnow()
        lead.assigned_by = "system"
        assigned += 1
    
    await session.commit()
    _logger.info(f"✅ Assigned {assigned} leads to {contractor.company_name}")
    return assigned


async def main():
    """Main function to generate leads immediately."""
    _logger.info("=" * 70)
    _logger.info("🚀 URGENT: Generating REAL LEADS for contractors/investors")
    _logger.info("=" * 70)
    
    async for session in get_session():
        try:
            # Step 1: Check property count
            result = await session.execute(select(func.count(Property.prop_id)))
            prop_count = result.scalar()
            _logger.info(f"📊 Properties in database: {prop_count:,}")
            
            if prop_count == 0:
                _logger.error("❌ No properties! Run: python -m src.ingestion.property_universe")
                return
            
            # Step 2: Create contractors
            contractor = await create_sample_contractor(session)
            
            # Step 3: Quick score and generate leads
            leads_generated = await quick_score_and_generate(session, trade="roofing", max_leads=50)
            
            # Step 4: Assign leads
            if leads_generated > 0:
                assigned = await assign_leads_to_contractor(session, contractor, max_leads=20)
            
            # Final status
            result = await session.execute(
                select(func.count(Lead.id)).where(Lead.status == "assigned")
            )
            total_assigned = result.scalar()
            
            result = await session.execute(select(func.count(Lead.id)))
            total_leads = result.scalar()
            
            _logger.info("=" * 70)
            _logger.info("✅ SUCCESS! REAL LEADS GENERATED")
            _logger.info(f"   Total Leads: {total_leads}")
            _logger.info(f"   Assigned Leads: {total_assigned}")
            _logger.info(f"   Contractor: {contractor.company_name} (ID: {contractor.id})")
            _logger.info("")
            _logger.info("🌐 View leads at: http://localhost:3000/admin/leads")
            _logger.info("🌐 View contractor at: http://localhost:3000/admin/contractors")
            _logger.info("=" * 70)
            
        except Exception as e:
            _logger.exception(f"❌ Error: {e}")
            raise
        finally:
            break


if __name__ == "__main__":
    asyncio.run(main())
