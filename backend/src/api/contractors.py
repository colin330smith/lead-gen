"""FastAPI endpoints for contractor management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.contractor import Contractor, ContractorTerritory
from ..services.territory_manager import TerritoryManager
from ..utils.logging import get_logger

_logger = get_logger(component="contractors_api")

router = APIRouter(prefix="/api/v1/contractors", tags=["contractors"])


@router.get("/")
async def list_contractors(
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """List contractors."""
    try:
        query = select(Contractor)
        
        if status:
            query = query.where(Contractor.status == status)
        
        query = query.limit(limit).offset(offset)
        
        result = await session.execute(query)
        contractors = result.scalars().all()
        
        return {
            "contractors": [
                {
                    "id": contractor.id,
                    "company_name": contractor.company_name,
                    "contact_name": contractor.contact_name,
                    "email": contractor.email,
                    "trades": contractor.trades,
                    "subscription_tier": contractor.subscription_tier,
                    "status": contractor.status,
                }
                for contractor in contractors
            ],
            "total": len(contractors),
        }
    except Exception as e:
        _logger.exception("Error listing contractors", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_contractor(
    company_name: str = Query(...),
    contact_name: str | None = Query(None),
    email: str | None = Query(None),
    phone: str | None = Query(None),
    trades: str = Query(..., description="Comma-separated trades"),
    subscription_tier: str = Query("starter", description="starter, growth, pro, scale"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create a new contractor."""
    try:
        contractor = Contractor(
            company_name=company_name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            trades=trades,
            subscription_tier=subscription_tier,
        )
        session.add(contractor)
        await session.commit()
        await session.refresh(contractor)
        
        return {
            "id": contractor.id,
            "company_name": contractor.company_name,
            "status": contractor.status,
        }
    except Exception as e:
        _logger.exception("Error creating contractor", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{contractor_id}/territories")
async def assign_territory(
    contractor_id: int,
    zip_code: str = Query(..., description="ZIP code"),
    trade: str = Query(..., description="Trade type"),
    is_exclusive: bool = Query(True, description="Exclusive territory"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Assign a territory to a contractor."""
    try:
        manager = TerritoryManager(session)
        territory = await manager.assign_territory(
            contractor_id=contractor_id,
            zip_code=zip_code,
            trade=trade,
            is_exclusive=is_exclusive,
        )
        
        return {
            "id": territory.id,
            "contractor_id": territory.contractor_id,
            "zip_code": territory.zip_code,
            "trade": territory.trade,
            "is_exclusive": territory.is_exclusive,
            "status": territory.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _logger.exception("Error assigning territory", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{contractor_id}/territories")
async def get_contractor_territories(
    contractor_id: int,
    trade: str | None = Query(None, description="Filter by trade"),
    active_only: bool = Query(True, description="Active territories only"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get territories for a contractor."""
    try:
        manager = TerritoryManager(session)
        territories = await manager.get_contractor_territories(
            contractor_id=contractor_id,
            trade=trade,
            active_only=active_only,
        )
        
        return {
            "contractor_id": contractor_id,
            "territories": [
                {
                    "id": t.id,
                    "zip_code": t.zip_code,
                    "trade": t.trade,
                    "is_exclusive": t.is_exclusive,
                    "status": t.status,
                    "assigned_at": t.assigned_at.isoformat(),
                }
                for t in territories
            ],
            "total": len(territories),
        }
    except Exception as e:
        _logger.exception("Error getting territories", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{contractor_id}")
async def get_contractor(
    contractor_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get a single contractor by ID."""
    try:
        contractor = await session.get(Contractor, contractor_id)
        if not contractor:
            raise HTTPException(status_code=404, detail="Contractor not found")
        
        return {
            "id": contractor.id,
            "company_name": contractor.company_name,
            "contact_name": contractor.contact_name,
            "email": contractor.email,
            "phone": contractor.phone,
            "trades": contractor.trades,
            "subscription_tier": contractor.subscription_tier,
            "status": contractor.status,
            "created_at": contractor.created_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        _logger.exception("Error getting contractor", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

