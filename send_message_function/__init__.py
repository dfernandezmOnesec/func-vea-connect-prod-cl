"""
HTTP trigger function to send WhatsApp messages using ACS.
"""
import logging
import json
import azure.functions as func
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import settings
from services.azure_blob_service import azure_blob_service
from services.acs_service import acs_service

# Configuración de logging global
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main function to send WhatsApp messages.
    
    Args:
        req: HTTP request from Azure Functions
        
    Returns:
        HttpResponse with result
    """
    logger.info("[AUDIT] Entró a send_message_function.main")
    try:
        
        # Check HTTP method
        if req.method != "POST":
            return func.HttpResponse(
                "Method not allowed. Use POST.",
                status_code=405
            )
        
        # Get request data
        body = req.get_json()
        
        # Validate required data
        if not body:
            return func.HttpResponse(
                "Empty request body",
                status_code=400
            )
        
        to_number = body.get('to_number')
        message = body.get('message')
        
        if not to_number or not message:
            return func.HttpResponse(
                "Missing required parameters: to_number, message",
                status_code=400
            )
        
        # Validate phone number
        if not acs_service.validate_phone_number(to_number):
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Invalid phone number format",
                    "to_number": to_number
                }),
                status_code=400,
                mimetype='application/json'
            )
        
        # Send message
        message_id = acs_service.send_whatsapp_message(to_number, message)
        
        if message_id:
            # Save to history
            save_outgoing_message(to_number, message, message_id)
            
            return func.HttpResponse(
                json.dumps({
                    "success": True,
                    "message": "Message sent successfully",
                    "to_number": to_number,
                    "message_id": message_id,
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=200,
                mimetype='application/json'
            )
        else:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Failed to send message",
                    "to_number": to_number
                }),
                status_code=500,
                mimetype='application/json'
            )
            
    except Exception as e:
        logger.error(f"Error in send message function: {e}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            }),
            status_code=500,
            mimetype='application/json'
        )


def save_outgoing_message(to_number: str, message: str, message_id: str) -> None:
    """
    Save outgoing message to Azure Blob Storage.
    
    Args:
        to_number: Destination phone number
        message: Message content
        message_id: Message ID from ACS
    """
    try:
        conversation_id = f"acs_{to_number}"
        
        # Load existing conversation
        conversation_data = azure_blob_service.load_conversation(conversation_id)
        
        if conversation_data is None:
            conversation_data = {
                "conversation_id": conversation_id,
                "user_number": to_number,
                "messages": []
            }
        
        # Add outgoing message
        conversation_data["messages"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "role": "assistant",
            "content": message,
            "message_id": message_id,
            "direction": "outgoing"
        })
        
        # Save conversation
        azure_blob_service.save_conversation(conversation_id, conversation_data["messages"])
        
        logger.debug(f"Outgoing message saved for {to_number}")
        
    except Exception as e:
        logger.error(f"Error saving outgoing message: {e}")


def get_message_status(message_id: str) -> Optional[Dict[str, Any]]:
    """
    Get status of a sent message.
    
    Args:
        message_id: Message ID
        
    Returns:
        Message status or None if not found
    """
    try:
        # Try to get status from blob storage
        blob_name = f"message_status/{message_id}.json"
        status_data = azure_blob_service.download_json(blob_name)
        
        if status_data:
            return status_data
        
        # Fallback to ACS service
        return acs_service.get_message_status(message_id)
        
    except Exception as e:
        logger.error(f"Error getting message status: {e}")
        return None 