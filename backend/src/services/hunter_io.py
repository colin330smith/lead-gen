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
    """Client for Hunter.io API for contact enrichment with email verification."""
    
    BASE_URL = "https://api.hunter.io/v2"
    
    # Verification statuses that indicate a valid, deliverable email
    VALID_VERIFICATION_STATUSES = {"valid", "accept_all"}
    
    # Minimum confidence score to accept an email (0-100)
    MIN_CONFIDENCE_SCORE = 70
    
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
    async def verify_email(self, email: str) -> dict[str, Any]:
        """Verify an email address using Hunter.io Email Verifier API.
        
        This MUST be called before sending any email to prevent bounces.
        
        Args:
            email: Email address to verify
            
        Returns:
            Dictionary with verification results:
            - status: 'valid', 'invalid', 'accept_all', 'webmail', 'disposable', 'unknown'
            - score: Confidence score 0-100
            - deliverable: Boolean indicating if email is safe to send to
            - reason: Reason for the status
        """
        params = {
            "api_key": self.api_key,
            "email": email,
        }
        
        try:
            response = await self.client.get("/email-verifier", params=params)
            response.raise_for_status()
            data = response.json()
            
            result = data.get("data", {})
            
            # Determine if email is deliverable based on status and score
            status = result.get("status", "unknown")
            score = result.get("score", 0)
            
            # Email is deliverable if:
            # 1. Status is 'valid' or 'accept_all' (catch-all domains)
            # 2. Score is above minimum threshold
            deliverable = (
                status in self.VALID_VERIFICATION_STATUSES and
                score >= self.MIN_CONFIDENCE_SCORE
            )
            
            verification_result = {
                "status": status,
                "score": score,
                "deliverable": deliverable,
                "reason": result.get("result", "unknown"),
                "mx_records": result.get("mx_records", False),
                "smtp_server": result.get("smtp_server", False),
                "smtp_check": result.get("smtp_check", False),
                "accept_all": result.get("accept_all", False),
                "block": result.get("block", False),
                "disposable": result.get("disposable", False),
                "webmail": result.get("webmail", False),
            }
            
            _logger.info(
                "Email verification result",
                email=email,
                status=status,
                score=score,
                deliverable=deliverable,
            )
            
            return verification_result
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                _logger.warning("Hunter.io rate limit exceeded during verification")
                raise
            else:
                _logger.error(
                    "Hunter.io verification API error",
                    status_code=e.response.status_code,
                    response=e.response.text,
                )
                raise
        except Exception as e:
            _logger.exception("Error verifying email via Hunter.io", email=email, error=str(e))
            raise
    
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
    
    async def find_and_verify_email(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        domain: str | None = None,
        company: str | None = None,
    ) -> HunterIOResponse | None:
        """Find AND verify an email address before returning it.
        
        This is the recommended method to use - it ensures we only return
        emails that have been verified as deliverable.
        
        Args:
            first_name: First name of the person
            last_name: Last name of the person
            domain: Domain name (e.g., 'example.com')
            company: Company name
            
        Returns:
            HunterIOResponse with verified email, or None if not found/invalid
        """
        # First, find the email
        email_response = await self.find_email(
            first_name=first_name,
            last_name=last_name,
            domain=domain,
            company=company,
        )
        
        if not email_response or not email_response.email:
            _logger.debug("No email found", first_name=first_name, last_name=last_name, domain=domain)
            return None
        
        # Now verify the email
        verification = await self.verify_email(email_response.email)
        
        if not verification.get("deliverable", False):
            _logger.warning(
                "Email found but failed verification - NOT returning",
                email=email_response.email,
                verification_status=verification.get("status"),
                verification_score=verification.get("score"),
                reason=verification.get("reason"),
            )
            return None
        
        # Update the response with verification data
        email_response.verification_status = verification.get("status")
        email_response.confidence_score = verification.get("score")
        
        _logger.info(
            "Email found and verified successfully",
            email=email_response.email,
            verification_status=verification.get("status"),
            verification_score=verification.get("score"),
        )
        
        return email_response
    
    async def enrich_contact(
        self,
        owner_name: str | None = None,
        owner_address: str | None = None,
        domain_hint: str | None = None,
    ) -> HunterIOResponse | None:
        """Enrich contact information for a property owner.
        
        Attempts to find AND VERIFY email using available information.
        Only returns emails that have been verified as deliverable.
        
        Args:
            owner_name: Full name or owner name from property record
            owner_address: Owner address (may contain domain hints)
            domain_hint: Optional domain hint (e.g., from email in address)
            
        Returns:
            HunterIOResponse with enriched and VERIFIED contact data, or None
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
        
        # Use find_and_verify_email instead of just find_email
        email_response = None
        if (first_name or last_name) and domain:
            email_response = await self.find_and_verify_email(
                first_name=first_name,
                last_name=last_name,
                domain=domain,
            )
        
        # Try phone finder if we have verified email
        phone = None
        if email_response and email_response.email:
            phone = await self.find_phone(email=email_response.email)
        
        # If we got verified email, return combined response
        if email_response:
            if phone:
                email_response.phone = phone
            return email_response
        
        # If no verified email but we have name, try phone finder directly
        if (first_name or last_name) and domain:
            phone = await self.find_phone(
                first_name=first_name,
                last_name=last_name,
                domain=domain,
            )
            if phone:
                return HunterIOResponse(phone=phone)
        
        return None
