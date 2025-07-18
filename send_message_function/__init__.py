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
    acs = acs_service
    blob_service = azure_blob_service
    log = logger
    log.info("[AUDIT] Entró a send_message_function.main")
    try:
        
        # Check HTTP method
        if req.method != "POST":
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Method not allowed. Use POST."
                }),
                status_code=405,
                mimetype='application/json'
            )
        
        # Get request data
        body = req.get_json()
        
        # Validate required data
        if not body:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Empty request body"
                }),
                status_code=400,
                mimetype='application/json'
            )
        
        to_number = body.get('to_number')
        message = body.get('message')
        
        if not to_number or not message:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Missing required parameters: to_number, message"
                }),
                status_code=400,
                mimetype='application/json'
            )
        
        # Validate phone number
        if not acs.validate_phone_number(to_number):
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
        message_id = acs.send_whatsapp_text_message(to_number, message)
        
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
        log.error(f"Error in send message function: {e}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            }),
            status_code=500,
            mimetype='application/json'
        )


def save_outgoing_message(to_number: str, message: str, message_id: str, azure_blob_service_instance=None, logger_instance=None) -> None:
    """
    Save outgoing message to Azure Blob Storage.
    
    Args:
        to_number: Destination phone number
        message: Message content
        message_id: Message ID from ACS
        azure_blob_service_instance: instancia de azure_blob_service (opcional)
        logger_instance: instancia de logger (opcional)
    """
    blob_service = azure_blob_service_instance or azure_blob_service
    log = logger_instance or logger
    try:
        conversation_id = f"acs_{to_number}"
        
        # Load existing conversation
        conversation_data = blob_service.load_conversation(conversation_id)
        
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
        blob_service.save_conversation(conversation_id, conversation_data["messages"])
        
        log.debug(f"Outgoing message saved for {to_number}")
        
    except Exception as e:
        log.error(f"Error saving outgoing message: {e}")


def get_message_status(message_id: str, azure_blob_service_instance=None, acs_service_instance=None, logger_instance=None) -> Optional[Dict[str, Any]]:
    """
    Get status of a sent message.
    
    Args:
        message_id: Message ID
        azure_blob_service_instance: instancia de azure_blob_service (opcional)
        acs_service_instance: instancia de acs_service (opcional)
        logger_instance: instancia de logger (opcional)
        
    Returns:
        Message status or None if not found
    """
    blob_service = azure_blob_service_instance or azure_blob_service
    acs = acs_service_instance or acs_service
    log = logger_instance or logger
    try:
        # Try to get status from blob storage
        blob_name = f"message_status/{message_id}.json"
        status_data = blob_service.download_json(blob_name)
        
        if status_data:
            return status_data
        
        # Fallback to ACS service
        return acs.get_message_status(message_id)
        
    except Exception as e:
        log.error(f"Error getting message status: {e}")
        return None 