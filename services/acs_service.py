"""
Azure Communication Services for WhatsApp messaging.
"""
import logging
from typing import Optional, Dict, Any, List
import httpx
from config.settings import settings
from services.redis_service import redis_service
import os
from azure.communication.messages import NotificationMessagesClient
from azure.communication.messages.models import TextNotificationContent
from azure.communication.messages.models import (
    TemplateNotificationContent, MessageTemplate, MessageTemplateText, WhatsAppMessageTemplateBindings, WhatsAppMessageTemplateBindingsComponent
)

logger = logging.getLogger(__name__)

class ACSService:
    """
    Service for Azure Communication Services WhatsApp messaging via SDK avanzado.
    """
    def __init__(self):
        self.endpoint = settings.acs_whatsapp_endpoint
        self.api_key = settings.acs_whatsapp_api_key
        self.phone_number = settings.acs_phone_number

    def send_whatsapp_text_message(self, to_number: str, content: str) -> str:
        logger.info(f"[AUDIT] Intentando enviar mensaje de texto a {to_number}: '{content[:50]}'")
        connection_string = os.getenv("COMMUNICATION_SERVICES_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("COMMUNICATION_SERVICES_CONNECTION_STRING is not set")
        channel_id = os.getenv("WHATSAPP_CHANNEL_ID_GUID")
        if not channel_id:
            raise ValueError("WHATSAPP_CHANNEL_ID_GUID is not set")
        try:
            client = NotificationMessagesClient.from_connection_string(connection_string)
            text_options = TextNotificationContent(
                channel_registration_id=channel_id,
                to=[to_number],
                content=content
            )
            message_responses = client.send(text_options)
            message_id = message_responses.receipts[0].message_id
            logger.info(f"[AUDIT] Mensaje de texto enviado a {to_number} con message_id: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"[AUDIT] Error enviando mensaje de texto a {to_number}: {e}", exc_info=True)
            raise

    def send_whatsapp_template_message(self, to_number: str, template_name: str, template_language: str = "es_MX", parameters: Optional[list] = None) -> str:
        logger.info(f"[AUDIT] Intentando enviar plantilla '{template_name}' a {to_number} con parámetros: {parameters}")
        connection_string = os.getenv("COMMUNICATION_SERVICES_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("COMMUNICATION_SERVICES_CONNECTION_STRING is not set")
        channel_id = os.getenv("WHATSAPP_CHANNEL_ID_GUID")
        if not channel_id:
            raise ValueError("WHATSAPP_CHANNEL_ID_GUID is not set")
        if parameters is None:
            parameters = []
        try:
            client = NotificationMessagesClient.from_connection_string(connection_string)
            template = MessageTemplate(name=template_name, language=template_language)
            if parameters:
                # Crear valores y bindings para los parámetros del body
                values = []
                bindings_body = []
                for idx, param in enumerate(parameters, start=1):
                    param_name = f"param{idx}"
                    values.append(MessageTemplateText(name=param_name, text=str(param)))
                    bindings_body.append(WhatsAppMessageTemplateBindingsComponent(ref_value=param_name))
                bindings = WhatsAppMessageTemplateBindings(body=bindings_body)
                template.bindings = bindings
                template.template_values = values
            template_options = TemplateNotificationContent(
                channel_registration_id=channel_id,
                to=[to_number],
                template=template
            )
            message_responses = client.send(template_options)
            message_id = message_responses.receipts[0].message_id
            logger.info(f"[AUDIT] Plantilla '{template_name}' enviada a {to_number} con message_id: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"[AUDIT] Error enviando plantilla '{template_name}' a {to_number}: {e}", exc_info=True)
            raise

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