"""
WhatsApp Bot Function for processing ACS Event Grid events.
"""
import logging
import json
import azure.functions as func
from datetime import datetime
from typing import Dict, Any, Optional
from config.settings import settings
from services.openai_service import openai_service
from services.azure_blob_service import azure_blob_service
from services.acs_service import acs_service

# Configuración de logging global
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


def main(event: func.EventGridEvent) -> None:
    logger.info("[AUDIT] Entró a whatsapp_bot_function.main")
    logger.info(f"[DEBUG] Event received in whatsapp_bot_function: {event.event_type}")
    # Procesar eventos de WhatsApp (AdvancedMessageReceived)
    if event.event_type != "Microsoft.Communication.AdvancedMessageReceived":
        logger.info(f"[DEBUG] Skipping event type: {event.event_type}")
        return
    try:
        event_data = event.get_json()
        if isinstance(event_data, str):
            event_data = json.loads(event_data)
        logger.info(f"[DEBUG] Event data received: {json.dumps(event_data, indent=2)}")
        message_details = _extract_message_details(event_data)
        if not message_details:
            logger.error("[DEBUG] Failed to extract message details from event data")
            return
        user_number = message_details["from_number"]
        message_content = message_details["message"]
        timestamp = message_details["timestamp"]
        logger.info(f"[DEBUG] Processing message from {user_number}: {message_content[:50]}...")
        conversation_id = f"whatsapp_{user_number}"
        conversation_context = _load_conversation_context(conversation_id)
        ai_response = _generate_ai_response(user_number, message_content, conversation_context)
        if not ai_response:
            logger.error(f"[DEBUG] Failed to generate AI response for user {user_number}")
            return
        message_id = acs_service.send_whatsapp_text_message(user_number, ai_response)
        if not message_id:
            logger.error(f"[DEBUG] Failed to send WhatsApp response to {user_number}")
            return
        _save_conversation(conversation_id, user_number, message_content, ai_response, timestamp)
        logger.info(f"[DEBUG] Successfully processed message from {user_number}, response sent with ID: {message_id}")
    except Exception as e:
        logger.error(f"[DEBUG] Error processing Event Grid event: {e}", exc_info=True)
        raise


def _extract_message_details(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract message details from Event Grid event data.
    
    Args:
        event_data: Raw event data from Event Grid
        
    Returns:
        Dictionary with message details or None if extraction fails
    """
    try:
        # Navigate through the event data structure
        data = event_data.get("data", {})
        
        # Extract message details
        from_number = data.get("from")
        message = data.get("message")
        received_timestamp = data.get("receivedTimestamp")
        
        if not from_number or not message:
            logger.error(f"Missing required fields in event data: from={from_number}, message={message}")
            return None
        
        return {
            "from_number": from_number,
            "message": message,
            "timestamp": received_timestamp or datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error extracting message details: {e}")
        return None


def _load_conversation_context(conversation_id: str) -> Optional[list]:
    """
    Load conversation context from Azure Blob Storage.
    
    Args:
        conversation_id: Unique conversation identifier
        
    Returns:
        List of previous messages or None if not found
    """
    try:
        conversation_data = azure_blob_service.load_conversation(conversation_id)
        if conversation_data and "messages" in conversation_data:
            logger.info(f"Loaded conversation context for {conversation_id}: {len(conversation_data['messages'])} messages")
            return conversation_data["messages"]
        else:
            logger.info(f"No existing conversation context found for {conversation_id}")
            return []
            
    except Exception as e:
        logger.error(f"Error loading conversation context for {conversation_id}: {e}")
        return []


def _generate_ai_response(user_number: str, message: str, conversation_context: Optional[list]) -> Optional[str]:
    """
    Generate AI response using OpenAI service.
    
    Args:
        user_number: User's phone number
        message: User's message
        conversation_context: Previous conversation messages
        
    Returns:
        Generated response or None if generation fails
    """
    try:
        response = openai_service.generate_chat_response_with_context(
            user_number=user_number,
            message=message,
            conversation_context=conversation_context
        )
        
        if response:
            logger.info(f"AI response generated for {user_number}: {len(response)} characters")
        else:
            logger.error(f"Failed to generate AI response for {user_number}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating AI response for {user_number}: {e}")
        return None


def _send_whatsapp_response(user_number: str, message: str) -> Optional[str]:
    """
    Send WhatsApp response using ACS service.
    
    Args:
        user_number: Recipient's phone number
        message: Message to send
        
    Returns:
        Message ID if sent successfully, None otherwise
    """
    try:
        message_id = acs_service.send_whatsapp_text_message(user_number, message)
        
        if message_id:
            logger.info(f"WhatsApp message sent to {user_number}, ID: {message_id}")
        else:
            logger.error(f"Failed to send WhatsApp message to {user_number}")
        
        return message_id
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {user_number}: {e}")
        return None


def _save_conversation(conversation_id: str, user_number: str, user_message: str, ai_response: str, timestamp: str) -> None:
    """
    Save conversation to Azure Blob Storage.
    
    Args:
        conversation_id: Unique conversation identifier
        user_number: User's phone number
        user_message: User's original message
        ai_response: AI's response
        timestamp: Message timestamp
    """
    try:
        # Load existing conversation
        existing_data = azure_blob_service.load_conversation(conversation_id)
        messages = existing_data.get("messages", []) if existing_data else []
        
        # Add user message
        messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": timestamp,
            "from_number": user_number
        })
        
        # Add AI response
        messages.append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": f"ai_response_{timestamp}"
        })
        
        # Save updated conversation
        success = azure_blob_service.save_conversation(conversation_id, messages)
        
        if success:
            logger.info(f"Conversation saved for {conversation_id}: {len(messages)} total messages")
        else:
            logger.error(f"Failed to save conversation for {conversation_id}")
            
    except Exception as e:
        logger.error(f"Error saving conversation for {conversation_id}: {e}") 