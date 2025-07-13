"""
Azure Communication Services for WhatsApp messaging.
"""
import logging
from typing import Optional, Dict, Any
import httpx
from config.settings import settings
from services.redis_service import redis_service

logger = logging.getLogger(__name__)

class ACSService:
    """
    Service for Azure Communication Services WhatsApp messaging via REST API.
    Uses acs_whatsapp_endpoint and acs_whatsapp_api_key from settings.
    """
    def __init__(self):
        self.endpoint = settings.acs_whatsapp_endpoint
        self.api_key = settings.acs_whatsapp_api_key
        self.phone_number = settings.acs_phone_number

    def send_whatsapp_message(self, to_number: str, message: str) -> Optional[str]:
        """
        Send WhatsApp message using ACS WhatsApp REST API.
        Args:
            to_number: Destination phone number (E.164)
            message: Message content
        Returns:
            Message ID if sent successfully, None otherwise
        """
        try:
            url = f"{self.endpoint}/messages:send?api-version=2023-03-31-preview"
            headers = {
                "Content-Type": "application/json",
                "Authorization": self.api_key
            }
            body = {
                "channel": "whatsapp",
                "from": self.phone_number,
                "to": to_number,
                "message": {
                    "content": message
                }
            }
            logger.info(f"[ACS WhatsApp] Sending message to {to_number} via {self.endpoint}")
            response = httpx.post(url, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"[ACS WhatsApp] Message sent. Response: {data}")
            return data.get("messageId")
        except httpx.HTTPStatusError as e:
            logger.error(f"[ACS WhatsApp] HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"[ACS WhatsApp] Error sending message: {e}", exc_info=True)
        return None

    def get_message_status(self, message_id: str) -> dict:
        """
        Consulta el estado del mensaje en Redis.
        """
        status = redis_service.get(f"message_status:{message_id}")
        if status:
            return {
                "message_id": message_id,
                "status": status
            }
        else:
            return {
                "message_id": message_id,
                "status": "unknown",
                "note": "No delivery report found. It may not have arrived yet."
            }

    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate phone number format (E.164).
        Args:
            phone_number: Phone number to validate
        Returns:
            True if valid format
        """
        try:
            if not phone_number:
                return False
            cleaned = ''.join(filter(str.isdigit, phone_number))
            if len(cleaned) < 10:
                return False
            return True
        except Exception as e:
            logger.error(f"Error validating phone number {phone_number}: {e}")
            return False

acs_service = ACSService() 