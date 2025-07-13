"""
Event Grid trigger function to handle ACS WhatsApp events.
"""
import logging
import json
import azure.functions as func
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from config.settings import settings
from services.openai_service import openai_service
from services.azure_blob_service import azure_blob_service
from services.acs_service import acs_service
from core.embedding_manager import embedding_manager
from services.redis_service import redis_service

logger = logging.getLogger(__name__)


def main(event: func.EventGridEvent) -> None:
    """
    Main function to handle Event Grid events from ACS WhatsApp.
    
    Args:
        event: Event Grid event containing ACS message data
    """
    try:
        # Configure logging
        logging.basicConfig(level=getattr(logging, settings.log_level))
        
        logger.info(f"Event Grid event received: {event.event_type}")
        
        # Handle different event types for WhatsApp
        if event.event_type == "Microsoft.Communication.AdvancedMessageReceived":
            handle_whatsapp_message_received(event)
        elif event.event_type == "Microsoft.Communication.AdvancedMessageDeliveryReportReceived":
            handle_whatsapp_delivery_report(event)
        else:
            logger.info(f"Unhandled event type: {event.event_type}")
            
    except Exception as e:
        logger.error(f"Error processing Event Grid event: {e}")


def handle_whatsapp_message_received(event: func.EventGridEvent) -> None:
    """
    Handle WhatsApp message received events from ACS.
    
    Args:
        event: Event Grid event with WhatsApp message data
    """
    try:
        # Extract WhatsApp message data from event
        message_data = event.get_json()
        logger.info(f"WhatsApp message received: {json.dumps(message_data, indent=2)}")
        
        # Extract message details for WhatsApp
        from_number = message_data.get('from', {}).get('phoneNumber')
        message_content = message_data.get('message', {}).get('content')
        message_id = message_data.get('id')
        received_timestamp = message_data.get('receivedTimestamp')
        channel_type = message_data.get('channelType', 'whatsapp')
        
        # Validate required fields
        if not from_number or not message_content:
            logger.warning("Missing from_number or message_content in WhatsApp event")
            return
            
        if channel_type != 'whatsapp':
            logger.info(f"Ignoring non-WhatsApp message from channel: {channel_type}")
            return
        
        # Process the message
        process_incoming_whatsapp_message(from_number, message_content, message_id, received_timestamp)
        
    except Exception as e:
        logger.error(f"Error handling WhatsApp message received event: {e}")


def handle_whatsapp_delivery_report(event: func.EventGridEvent) -> None:
    """
    Handle WhatsApp delivery report events from ACS.
    
    Args:
        event: Event Grid event with delivery report data
    """
    try:
        # Extract delivery report data
        report_data = event.get_json()
        logger.info(f"WhatsApp delivery report: {json.dumps(report_data, indent=2)}")
        
        # Extract report details
        message_id = report_data.get('id')
        delivery_status = report_data.get('status')
        delivery_timestamp = report_data.get('deliveryTimestamp')
        
        # Update message status in storage
        update_message_status(message_id, delivery_status, delivery_timestamp)
        
    except Exception as e:
        logger.error(f"Error handling WhatsApp delivery report: {e}")


def process_incoming_whatsapp_message(from_number: str, message_content: str, message_id: str, timestamp: str) -> None:
    """
    Process incoming WhatsApp message and generate response with RAG.
    
    Args:
        from_number: Sender phone number
        message_content: Message content
        message_id: Message ID
        timestamp: Message timestamp
    """
    try:
        logger.info(f"Processing WhatsApp message from {from_number}: {message_content}")
        
        # Generate response using OpenAI with RAG
        response_text = generate_response_with_rag(message_content, from_number)
        
        if response_text:
            # Send response using ACS
            sent_message_id = acs_service.send_whatsapp_message(from_number, response_text)
            
            if sent_message_id:
                # Save conversation with enhanced context
                save_conversation_with_context(from_number, message_content, response_text, timestamp, message_id, sent_message_id)
                logger.info(f"Response sent to {from_number}, message ID: {sent_message_id}")
            else:
                logger.error(f"Failed to send response to {from_number}")
        else:
            logger.error("Failed to generate response")
            
    except Exception as e:
        logger.error(f"Error processing incoming WhatsApp message: {e}")


def generate_response_with_rag(user_message: str, user_number: str) -> Optional[str]:
    """
    Generate response using OpenAI with RAG (Retrieval-Augmented Generation).
    
    Args:
        user_message: User message
        user_number: User phone number
        
    Returns:
        Generated response or None if error
    """
    try:
        # Get embedding for user message
        user_embedding = embedding_manager.get_embedding(user_message)
        
        # Find similar content using RAG
        if user_embedding is not None:
            similar_content = embedding_manager.find_similar_content(user_embedding, top_k=3)
        else:
            similar_content = None
        
        # Load conversation history with Redis for active context
        conversation_history = load_conversation_history_with_redis(user_number)
        
        # Prepare messages for OpenAI with RAG context
        messages = []
        
        # Add system context with RAG information
        system_context = "You are a helpful and friendly assistant for WhatsApp. Respond clearly and concisely."
        if similar_content:
            system_context += f"\n\nRelevant context for this conversation:\n{similar_content}"
        
        messages.append({
            "role": "system",
            "content": system_context
        })
        
        # Add conversation history (last 10 messages for better context)
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Generate response
        response = openai_service.generate_chat_response(messages)
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating response with RAG: {e}")
        return None


def save_conversation_with_context(user_number: str, user_message: str, bot_response: str, 
                                 timestamp: str, incoming_message_id: str, outgoing_message_id: str) -> None:
    """
    Save conversation to both Azure Blob Storage and Redis for active context.
    
    Args:
        user_number: User phone number
        user_message: User message
        bot_response: Bot response
        timestamp: Message timestamp
        incoming_message_id: Incoming message ID
        outgoing_message_id: Outgoing message ID
    """
    try:
        conversation_id = f"acs_{user_number}"
        
        # Prepare conversation data
        conversation_data = {
            "conversation_id": conversation_id,
            "user_number": user_number,
            "messages": []
        }
        
        # Load existing conversation from blob
        existing_data = azure_blob_service.load_conversation(conversation_id)
        if existing_data and "messages" in existing_data:
            conversation_data["messages"] = existing_data["messages"]
        
        # Add user message
        user_msg = {
            "timestamp": timestamp,
            "role": "user",
            "content": user_message,
            "message_id": incoming_message_id,
            "direction": "incoming"
        }
        conversation_data["messages"].append(user_msg)
        
        # Add bot response
        bot_msg = {
            "timestamp": datetime.utcnow().isoformat(),
            "role": "assistant",
            "content": bot_response,
            "message_id": outgoing_message_id,
            "direction": "outgoing"
        }
        conversation_data["messages"].append(bot_msg)
        
        # Save to blob storage for long-term storage
        azure_blob_service.save_conversation(conversation_id, conversation_data["messages"])
        
        # Save to Redis for active context (last 20 messages)
        active_context = conversation_data["messages"][-20:]
        embedding_manager.save_conversation_context(user_number, active_context)
        
        logger.debug(f"Conversation saved for {user_number} (blob + redis)")
        
    except Exception as e:
        logger.error(f"Error saving conversation with context: {e}")


def load_conversation_history_with_redis(user_number: str) -> List[Dict[str, Any]]:
    """
    Load conversation history from Redis for active context, fallback to blob.
    
    Args:
        user_number: User phone number
        
    Returns:
        List of conversation messages
    """
    try:
        # Try to get active context from Redis first
        active_context = embedding_manager.get_conversation_context(user_number)
        
        if active_context:
            logger.debug(f"Loaded active context from Redis for {user_number}")
            return active_context
        
        # Fallback to blob storage
        conversation_id = f"acs_{user_number}"
        conversation_data = azure_blob_service.load_conversation(conversation_id)
        
        if conversation_data and "messages" in conversation_data:
            # Cache in Redis for future use
            embedding_manager.save_conversation_context(user_number, conversation_data["messages"][-20:])
            return conversation_data["messages"]
        
        return []
        
    except Exception as e:
        logger.error(f"Error loading conversation history with Redis: {e}")
        return []


def update_message_status(message_id: str, status: str, timestamp: str) -> None:
    """
    Update message status in storage.
    
    Args:
        message_id: Message ID
        status: Delivery status
        timestamp: Status timestamp
    """
    try:
        # Create status update record
        status_data = {
            "message_id": message_id,
            "status": status,
            "timestamp": timestamp,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Save to blob storage
        blob_name = f"message_status/{message_id}.json"
        azure_blob_service.upload_json(blob_name, status_data)
        
        # Also update in Redis for quick access
        embedding_manager.save_message_status(message_id, status_data)
        
        logger.debug(f"Message status updated: {message_id} -> {status}")
        
    except Exception as e:
        logger.error(f"Error updating message status: {e}") 