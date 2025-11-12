"""Email delivery service for leads."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from ..config import get_settings
from ..models.lead import Lead
from ..models.property import Property
from ..models.contractor import Contractor
from ..utils.logging import get_logger

_logger = get_logger(component="email_delivery")
_settings = get_settings()


class EmailDeliveryService:
    """Service for delivering leads via email."""

    def __init__(self):
        self.smtp_host = getattr(_settings, "smtp_host", "smtp.gmail.com")
        self.smtp_port = getattr(_settings, "smtp_port", 587)
        self.smtp_user = getattr(_settings, "smtp_user", None)
        self.smtp_password = getattr(_settings, "smtp_password", None)
        self.from_email = getattr(_settings, "from_email", "noreply@locallift.com")

    async def deliver_lead_email(
        self,
        lead: Lead,
        contractor: Contractor,
        property: Property,
    ) -> dict[str, Any]:
        """
        Deliver a lead via email to contractor.
        
        Returns delivery status and tracking info.
        """
        _logger.info("Delivering lead via email", lead_id=lead.id, contractor_id=contractor.id)
        
        try:
            # Generate email content
            subject, html_body, text_body = self._generate_lead_email(
                lead, contractor, property
            )
            
            # Send email
            success = await self._send_email(
                to_email=contractor.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
            
            if success:
                _logger.success("Lead email delivered", lead_id=lead.id, contractor_id=contractor.id)
                return {
                    "delivered": True,
                    "method": "email",
                    "recipient": contractor.email,
                    "tracking_id": f"email_{lead.id}_{contractor.id}",
                }
            else:
                _logger.error("Failed to deliver lead email", lead_id=lead.id)
                return {
                    "delivered": False,
                    "method": "email",
                    "error": "SMTP delivery failed",
                }
        
        except Exception as e:
            _logger.exception("Error delivering lead email", lead_id=lead.id, error=str(e))
            return {
                "delivered": False,
                "method": "email",
                "error": str(e),
            }

    def _generate_lead_email(
        self,
        lead: Lead,
        contractor: Contractor,
        property: Property,
    ) -> tuple[str, str, str]:
        """Generate email subject and body for lead."""
        subject = f"New {lead.trade.title()} Lead - {property.situs_address or 'Property'} - Score: {lead.intent_score:.2f}"
        
        # HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">New Lead Available</h2>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Lead Details</h3>
                    <p><strong>Trade:</strong> {lead.trade.title()}</p>
                    <p><strong>Intent Score:</strong> {lead.intent_score:.2f}</p>
                    <p><strong>Quality Score:</strong> {lead.quality_score:.2f if lead.quality_score else 'N/A'}</p>
                    <p><strong>ZIP Code:</strong> {lead.zip_code or 'N/A'}</p>
                </div>
                
                <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Property Information</h3>
                    <p><strong>Address:</strong> {property.situs_address or 'N/A'}</p>
                    <p><strong>Market Value:</strong> ${property.market_value:,.0f if property.market_value else 'N/A'}</p>
                    <p><strong>Owner:</strong> {property.owner_name or 'N/A'}</p>
                </div>
                
                <div style="background: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Signal Summary</h3>
                    <p><strong>Total Signals:</strong> {lead.signal_count or 0}</p>
                    <p><strong>Violations:</strong> {lead.violation_count or 0}</p>
                    <p><strong>311 Requests:</strong> {lead.request_count or 0}</p>
                </div>
                
                <div style="margin: 20px 0; padding: 15px; background: #e3f2fd; border-radius: 5px;">
                    <p><strong>Lead ID:</strong> {lead.id}</p>
                    <p><strong>Generated:</strong> {lead.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Expires:</strong> {lead.expires_at.strftime('%Y-%m-%d %H:%M:%S') if lead.expires_at else 'N/A'}</p>
                </div>
                
                <p style="margin-top: 30px; color: #666; font-size: 12px;">
                    This lead was generated by Local Lift. Please log in to your dashboard for full details.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text body
        text_body = f"""
New Lead Available

Lead Details:
- Trade: {lead.trade.title()}
- Intent Score: {lead.intent_score:.2f}
- Quality Score: {lead.quality_score:.2f if lead.quality_score else 'N/A'}
- ZIP Code: {lead.zip_code or 'N/A'}

Property Information:
- Address: {property.situs_address or 'N/A'}
- Market Value: ${property.market_value:,.0f if property.market_value else 'N/A'}
- Owner: {property.owner_name or 'N/A'}

Signal Summary:
- Total Signals: {lead.signal_count or 0}
- Violations: {lead.violation_count or 0}
- 311 Requests: {lead.request_count or 0}

Lead ID: {lead.id}
Generated: {lead.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
Expires: {lead.expires_at.strftime('%Y-%m-%d %H:%M:%S') if lead.expires_at else 'N/A'}

This lead was generated by Local Lift.
        """
        
        return subject, html_body, text_body

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> bool:
        """Send email via SMTP."""
        if not self.smtp_user or not self.smtp_password:
            _logger.warning("SMTP credentials not configured, skipping email send")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email
            
            # Add body
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            _logger.exception("Error sending email", error=str(e))
            return False

