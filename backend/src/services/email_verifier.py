"""
Email Verification Service

This service provides email verification capabilities using multiple methods:
1. Hunter.io Email Verifier API (primary)
2. DNS MX record check (fallback)
3. SMTP verification (optional, more aggressive)

IMPORTANT: Always verify emails before sending to prevent bounces!
"""

from __future__ import annotations

import asyncio
import dns.resolver
import re
import socket
from dataclasses import dataclass
from typing import Any

import httpx

from ..config import get_settings
from ..utils.logging import get_logger

_logger = get_logger(component="email_verifier")
_settings = get_settings()


@dataclass
class EmailVerificationResult:
    """Result of email verification."""
    email: str
    is_valid: bool
    is_deliverable: bool
    score: int  # 0-100 confidence score
    status: str  # valid, invalid, risky, unknown
    reason: str
    mx_records: bool
    smtp_check: bool | None
    is_disposable: bool
    is_catch_all: bool
    provider: str | None  # gmail, outlook, custom, etc.
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "email": self.email,
            "is_valid": self.is_valid,
            "is_deliverable": self.is_deliverable,
            "score": self.score,
            "status": self.status,
            "reason": self.reason,
            "mx_records": self.mx_records,
            "smtp_check": self.smtp_check,
            "is_disposable": self.is_disposable,
            "is_catch_all": self.is_catch_all,
            "provider": self.provider,
        }


class EmailVerifier:
    """
    Email verification service with multiple verification methods.
    
    Usage:
        verifier = EmailVerifier()
        result = await verifier.verify("test@example.com")
        if result.is_deliverable:
            # Safe to send
            pass
    """
    
    # Known disposable email domains
    DISPOSABLE_DOMAINS = {
        "tempmail.com", "throwaway.email", "guerrillamail.com", "10minutemail.com",
        "mailinator.com", "temp-mail.org", "fakeinbox.com", "trashmail.com",
        "getnada.com", "maildrop.cc", "dispostable.com", "yopmail.com",
    }
    
    # Known webmail providers
    WEBMAIL_PROVIDERS = {
        "gmail.com": "gmail",
        "googlemail.com": "gmail",
        "outlook.com": "outlook",
        "hotmail.com": "outlook",
        "live.com": "outlook",
        "yahoo.com": "yahoo",
        "aol.com": "aol",
        "icloud.com": "icloud",
        "me.com": "icloud",
        "protonmail.com": "protonmail",
        "proton.me": "protonmail",
    }
    
    # Minimum score to consider email deliverable
    MIN_DELIVERABLE_SCORE = 70
    
    def __init__(self, hunter_api_key: str | None = None):
        self.hunter_api_key = hunter_api_key or getattr(_settings, "hunter_io_api_key", None)
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    def _validate_email_format(self, email: str) -> tuple[bool, str]:
        """Validate email format using regex."""
        if not email:
            return False, "Email is empty"
        
        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        # Check for common typos
        domain = email.split("@")[1].lower()
        typo_domains = {
            "gmial.com": "gmail.com",
            "gmal.com": "gmail.com",
            "gamil.com": "gmail.com",
            "outlok.com": "outlook.com",
            "outloo.com": "outlook.com",
            "hotmal.com": "hotmail.com",
            "yaho.com": "yahoo.com",
        }
        if domain in typo_domains:
            return False, f"Possible typo: did you mean {typo_domains[domain]}?"
        
        return True, "Format valid"
    
    def _check_disposable(self, email: str) -> bool:
        """Check if email is from a disposable domain."""
        domain = email.split("@")[1].lower()
        return domain in self.DISPOSABLE_DOMAINS
    
    def _get_provider(self, email: str) -> str | None:
        """Get email provider from domain."""
        domain = email.split("@")[1].lower()
        return self.WEBMAIL_PROVIDERS.get(domain)
    
    async def _check_mx_records(self, email: str) -> tuple[bool, list[str]]:
        """Check if domain has valid MX records."""
        domain = email.split("@")[1]
        try:
            # Run DNS query in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            mx_records = await loop.run_in_executor(
                None,
                lambda: dns.resolver.resolve(domain, 'MX')
            )
            records = [str(r.exchange).rstrip('.') for r in mx_records]
            return bool(records), records
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return False, []
        except Exception as e:
            _logger.warning("MX record check failed", domain=domain, error=str(e))
            return False, []
    
    async def _verify_with_hunter(self, email: str) -> dict[str, Any] | None:
        """Verify email using Hunter.io API."""
        if not self.hunter_api_key:
            _logger.warning("Hunter.io API key not configured, skipping Hunter verification")
            return None
        
        if not self._client:
            self._client = httpx.AsyncClient(timeout=30.0)
        
        try:
            response = await self._client.get(
                "https://api.hunter.io/v2/email-verifier",
                params={
                    "api_key": self.hunter_api_key,
                    "email": email,
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {})
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                _logger.warning("Hunter.io rate limit exceeded")
            else:
                _logger.error("Hunter.io API error", status_code=e.response.status_code)
            return None
        except Exception as e:
            _logger.exception("Error calling Hunter.io", error=str(e))
            return None
    
    async def verify(self, email: str, use_hunter: bool = True) -> EmailVerificationResult:
        """
        Verify an email address.
        
        Args:
            email: Email address to verify
            use_hunter: Whether to use Hunter.io API (recommended)
            
        Returns:
            EmailVerificationResult with verification details
        """
        email = email.strip().lower()
        
        # Step 1: Format validation
        format_valid, format_reason = self._validate_email_format(email)
        if not format_valid:
            return EmailVerificationResult(
                email=email,
                is_valid=False,
                is_deliverable=False,
                score=0,
                status="invalid",
                reason=format_reason,
                mx_records=False,
                smtp_check=None,
                is_disposable=False,
                is_catch_all=False,
                provider=None,
            )
        
        # Step 2: Check disposable
        is_disposable = self._check_disposable(email)
        if is_disposable:
            return EmailVerificationResult(
                email=email,
                is_valid=True,
                is_deliverable=False,
                score=10,
                status="disposable",
                reason="Disposable email domain",
                mx_records=True,  # Assume true for disposable
                smtp_check=None,
                is_disposable=True,
                is_catch_all=False,
                provider=None,
            )
        
        # Step 3: Check MX records
        has_mx, mx_records = await self._check_mx_records(email)
        if not has_mx:
            return EmailVerificationResult(
                email=email,
                is_valid=False,
                is_deliverable=False,
                score=0,
                status="invalid",
                reason="Domain has no MX records",
                mx_records=False,
                smtp_check=None,
                is_disposable=False,
                is_catch_all=False,
                provider=self._get_provider(email),
            )
        
        # Step 4: Use Hunter.io for comprehensive verification
        if use_hunter and self.hunter_api_key:
            hunter_result = await self._verify_with_hunter(email)
            if hunter_result:
                status = hunter_result.get("status", "unknown")
                score = hunter_result.get("score", 0)
                
                # Determine deliverability based on Hunter results
                is_deliverable = (
                    status in ("valid", "accept_all") and
                    score >= self.MIN_DELIVERABLE_SCORE
                )
                
                return EmailVerificationResult(
                    email=email,
                    is_valid=status != "invalid",
                    is_deliverable=is_deliverable,
                    score=score,
                    status=status,
                    reason=hunter_result.get("result", "Verified via Hunter.io"),
                    mx_records=hunter_result.get("mx_records", has_mx),
                    smtp_check=hunter_result.get("smtp_check"),
                    is_disposable=hunter_result.get("disposable", False),
                    is_catch_all=hunter_result.get("accept_all", False),
                    provider=self._get_provider(email),
                )
        
        # Step 5: Fallback - MX records only (less reliable)
        _logger.warning(
            "Using MX-only verification (less reliable)",
            email=email,
            reason="Hunter.io not available",
        )
        
        return EmailVerificationResult(
            email=email,
            is_valid=True,
            is_deliverable=False,  # Conservative - don't mark as deliverable without Hunter
            score=50,  # Medium confidence
            status="unknown",
            reason="MX records valid but email not fully verified",
            mx_records=has_mx,
            smtp_check=None,
            is_disposable=False,
            is_catch_all=False,
            provider=self._get_provider(email),
        )
    
    async def verify_batch(
        self,
        emails: list[str],
        use_hunter: bool = True,
        rate_limit_per_minute: int = 50,
    ) -> list[EmailVerificationResult]:
        """
        Verify a batch of email addresses.
        
        Args:
            emails: List of email addresses to verify
            use_hunter: Whether to use Hunter.io API
            rate_limit_per_minute: Rate limit for API calls
            
        Returns:
            List of EmailVerificationResult objects
        """
        results = []
        delay = 60.0 / rate_limit_per_minute
        
        for i, email in enumerate(emails):
            result = await self.verify(email, use_hunter=use_hunter)
            results.append(result)
            
            if i < len(emails) - 1:
                await asyncio.sleep(delay)
        
        return results
    
    async def filter_deliverable(
        self,
        emails: list[str],
        use_hunter: bool = True,
    ) -> list[str]:
        """
        Filter a list of emails to only include deliverable ones.
        
        This is the recommended method to use before any email campaign.
        
        Args:
            emails: List of email addresses to filter
            use_hunter: Whether to use Hunter.io API
            
        Returns:
            List of verified, deliverable email addresses
        """
        results = await self.verify_batch(emails, use_hunter=use_hunter)
        
        deliverable = [r.email for r in results if r.is_deliverable]
        rejected = [r for r in results if not r.is_deliverable]
        
        if rejected:
            _logger.warning(
                "Filtered out non-deliverable emails",
                total=len(emails),
                deliverable=len(deliverable),
                rejected=len(rejected),
                rejected_emails=[r.email for r in rejected],
                rejection_reasons={r.email: r.reason for r in rejected},
            )
        
        return deliverable


async def verify_email_before_send(email: str) -> tuple[bool, str]:
    """
    Convenience function to verify a single email before sending.
    
    Usage:
        is_safe, reason = await verify_email_before_send("test@example.com")
        if is_safe:
            # Send email
            pass
        else:
            print(f"Cannot send to {email}: {reason}")
    
    Returns:
        Tuple of (is_safe_to_send, reason)
    """
    async with EmailVerifier() as verifier:
        result = await verifier.verify(email)
        return result.is_deliverable, result.reason
