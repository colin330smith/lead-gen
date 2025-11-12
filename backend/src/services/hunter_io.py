from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from ..models.contact_enrichment import HunterIOResponse
from ..utils.logging import get_logger

_logger = get_logger(component="hunter_io")

_settings = get_settings()


class HunterIOClient:
    """Client for Hunter.io API for contact enrichment."""
    
    BASE_URL = "https://api.hunter.io/v2"
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(_settings, "hunter_io_api_key", None)
        if not self.api_key:
            raise ValueError("Hunter.io API key is required. Set LOCALLIFT_HUNTER_IO_API_KEY environment variable.")
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={"User-Agent": "LocalLift/1.0"},
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def find_email(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        domain: str | None = None,
        company: str | None = None,
    ) -> HunterIOResponse | None:
        """Find email address using Hunter.io email finder API.
        
        Args:
            first_name: First name of the person
            last_name: Last name of the person
            domain: Domain name (e.g., 'example.com')
            company: Company name
            
        Returns:
            HunterIOResponse with email and metadata, or None if not found
        """
        params: dict[str, Any] = {
            "api_key": self.api_key,
        }
        
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if domain:
            params["domain"] = domain
        if company:
            params["company"] = company
        
        try:
            response = await self.client.get("/email-finder", params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data") and data["data"].get("email"):
                return HunterIOResponse.model_validate(data["data"])
            
            return None
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                _logger.debug("Email not found via Hunter.io", params=params)
                return None
            elif e.response.status_code == 429:
                _logger.warning("Hunter.io rate limit exceeded")
                raise
            else:
                _logger.error("Hunter.io API error", status_code=e.response.status_code, response=e.response.text)
                raise
        except Exception as e:
            _logger.exception("Error calling Hunter.io API", error=str(e))
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def find_phone(
        self,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        domain: str | None = None,
    ) -> str | None:
        """Find phone number using Hunter.io phone number finder API.
        
        Args:
            email: Email address
            first_name: First name
            last_name: Last name
            domain: Domain name
            
        Returns:
            Phone number string, or None if not found
        """
        params: dict[str, Any] = {
            "api_key": self.api_key,
        }
        
        if email:
            params["email"] = email
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if domain:
            params["domain"] = domain
        
        try:
            response = await self.client.get("/phone-number-finder", params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data") and data["data"].get("phone_number"):
                return data["data"]["phone_number"]
            
            return None
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                _logger.debug("Phone not found via Hunter.io", params=params)
                return None
            elif e.response.status_code == 429:
                _logger.warning("Hunter.io rate limit exceeded")
                raise
            else:
                _logger.error("Hunter.io API error", status_code=e.response.status_code, response=e.response.text)
                raise
        except Exception as e:
            _logger.exception("Error calling Hunter.io API", error=str(e))
            raise
    
    async def enrich_contact(
        self,
        owner_name: str | None = None,
        owner_address: str | None = None,
        domain_hint: str | None = None,
    ) -> HunterIOResponse | None:
        """Enrich contact information for a property owner.
        
        Attempts to find email and phone using available information.
        
        Args:
            owner_name: Full name or owner name from property record
            owner_address: Owner address (may contain domain hints)
            domain_hint: Optional domain hint (e.g., from email in address)
            
        Returns:
            HunterIOResponse with enriched contact data, or None
        """
        # Parse name
        first_name = None
        last_name = None
        if owner_name:
            name_parts = owner_name.strip().split(maxsplit=1)
            if len(name_parts) >= 1:
                first_name = name_parts[0]
            if len(name_parts) >= 2:
                last_name = name_parts[1]
        
        # Try to extract domain from address or use hint
        domain = domain_hint
        if not domain and owner_address:
            # Look for email-like patterns in address
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            matches = re.findall(email_pattern, owner_address)
            if matches:
                domain = matches[0].split("@")[1]
        
        # Try email finder first
        email_response = None
        if (first_name or last_name) and domain:
            email_response = await self.find_email(
                first_name=first_name,
                last_name=last_name,
                domain=domain,
            )
        
        # Try phone finder if we have email
        phone = None
        if email_response and email_response.email:
            phone = await self.find_phone(email=email_response.email)
        
        # If we got email, return combined response
        if email_response:
            if phone:
                email_response.phone = phone
            return email_response
        
        # If no email but we have name, try phone finder directly
        if (first_name or last_name) and domain:
            phone = await self.find_phone(
                first_name=first_name,
                last_name=last_name,
                domain=domain,
            )
            if phone:
                return HunterIOResponse(phone=phone)
        
        return None

