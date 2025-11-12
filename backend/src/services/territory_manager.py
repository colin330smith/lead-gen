"""Territory management service for contractor assignments."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.contractor import Contractor, ContractorTerritory
from ..utils.logging import get_logger

_logger = get_logger(component="territory_manager")


class TerritoryManager:
    """Manages contractor territory assignments with exclusivity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def assign_territory(
        self,
        contractor_id: int,
        zip_code: str,
        trade: str,
        is_exclusive: bool = True,
        expires_at: datetime | None = None,
    ) -> ContractorTerritory:
        """
        Assign a territory (ZIP code + trade) to a contractor.
        
        If exclusive, ensures no other contractor has this territory.
        """
        _logger.info(
            "Assigning territory",
            contractor_id=contractor_id,
            zip_code=zip_code,
            trade=trade,
            is_exclusive=is_exclusive,
        )
        
        # Check if contractor exists
        contractor = await self.session.get(Contractor, contractor_id)
        if not contractor:
            raise ValueError(f"Contractor {contractor_id} not found")
        
        # If exclusive, check for existing assignments
        if is_exclusive:
            existing = await self.session.execute(
                select(ContractorTerritory).where(
                    ContractorTerritory.zip_code == zip_code,
                    ContractorTerritory.trade == trade,
                    ContractorTerritory.status == "active",
                    ContractorTerritory.is_exclusive == True,
                )
            )
            existing_territory = existing.scalar_one_or_none()
            
            if existing_territory:
                if existing_territory.contractor_id != contractor_id:
                    raise ValueError(
                        f"ZIP {zip_code} and trade {trade} already assigned to "
                        f"contractor {existing_territory.contractor_id} (exclusive)"
                    )
                else:
                    # Already assigned to this contractor
                    _logger.info("Territory already assigned to contractor")
                    return existing_territory
        
        # Create or update territory
        territory = await self.session.execute(
            select(ContractorTerritory).where(
                ContractorTerritory.contractor_id == contractor_id,
                ContractorTerritory.zip_code == zip_code,
                ContractorTerritory.trade == trade,
            )
        )
        existing_territory = territory.scalar_one_or_none()
        
        if existing_territory:
            existing_territory.status = "active"
            existing_territory.is_exclusive = is_exclusive
            existing_territory.expires_at = expires_at
            existing_territory.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(existing_territory)
            return existing_territory
        else:
            new_territory = ContractorTerritory(
                contractor_id=contractor_id,
                zip_code=zip_code,
                trade=trade,
                is_exclusive=is_exclusive,
                status="active",
                expires_at=expires_at,
            )
            self.session.add(new_territory)
            await self.session.commit()
            await self.session.refresh(new_territory)
            
            _logger.success(
                "Territory assigned",
                contractor_id=contractor_id,
                zip_code=zip_code,
                trade=trade,
            )
            return new_territory

    async def get_contractor_territories(
        self,
        contractor_id: int,
        trade: str | None = None,
        active_only: bool = True,
    ) -> list[ContractorTerritory]:
        """Get all territories for a contractor."""
        query = select(ContractorTerritory).where(
            ContractorTerritory.contractor_id == contractor_id
        )
        
        if trade:
            query = query.where(ContractorTerritory.trade == trade)
        
        if active_only:
            query = query.where(ContractorTerritory.status == "active")
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_available_zip_codes(
        self,
        trade: str,
    ) -> list[str]:
        """Get ZIP codes available for assignment (not exclusively assigned)."""
        # Get all ZIP codes with properties
        from ..models.property import Property
        from sqlalchemy import func, distinct
        
        all_zips = await self.session.execute(
            select(distinct(Property.situs_zip)).where(
                Property.situs_zip.isnot(None)
            )
        )
        all_zip_list = [row[0] for row in all_zips.fetchall()]
        
        # Get exclusively assigned ZIP codes
        assigned = await self.session.execute(
            select(ContractorTerritory.zip_code).where(
                ContractorTerritory.trade == trade,
                ContractorTerritory.status == "active",
                ContractorTerritory.is_exclusive == True,
            )
        )
        assigned_zips = {row[0] for row in assigned.fetchall()}
        
        # Return available ZIP codes
        available = [zip_code for zip_code in all_zip_list if zip_code not in assigned_zips]
        
        return available

    async def revoke_territory(
        self,
        contractor_id: int,
        zip_code: str,
        trade: str,
    ) -> None:
        """Revoke a territory assignment."""
        territory = await self.session.execute(
            select(ContractorTerritory).where(
                ContractorTerritory.contractor_id == contractor_id,
                ContractorTerritory.zip_code == zip_code,
                ContractorTerritory.trade == trade,
            )
        )
        territory_obj = territory.scalar_one_or_none()
        
        if territory_obj:
            territory_obj.status = "paused"
            territory_obj.updated_at = datetime.utcnow()
            await self.session.commit()
            _logger.info("Territory revoked", contractor_id=contractor_id, zip_code=zip_code, trade=trade)
        else:
            raise ValueError(f"Territory not found for contractor {contractor_id}, ZIP {zip_code}, trade {trade}")

