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

# Configuración de logging global
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


def main(event: func.EventGridEvent) -> None:
    """
    Main function to handle Event Grid events from ACS WhatsApp.
    
    Args:
        event: Event Grid event containing ACS message data
    """
    logger.info("[AUDIT] Entró a event_grid_handler.main")
    try:
        
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
        if isinstance(message_data, str):
            message_data = json.loads(message_data)
        logger.info(f"WhatsApp message received: {json.dumps(message_data, indent=2)}")

        # Soporta ambos formatos: dict anidado o plano
        from_number = None
        if isinstance(message_data.get('from'), dict):
            from_number = message_data['from'].get('phoneNumber')
        elif isinstance(message_data.get('from'), str):
            from_number = message_data['from']

        message_content = None
        if isinstance(message_data.get('message'), dict):
            message_content = message_data['message'].get('content')
        elif message_data.get('content'):
            message_content = message_data['content']

        message_id = message_data.get('id') or message_data.get('messageId')
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
        if isinstance(report_data, str):
            report_data = json.loads(report_data)
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
    try:
        logger.info(f"Processing WhatsApp message from {from_number}: {message_content}")

        # Normaliza el mensaje a minúsculas para comparar
        msg = message_content.lower()

        if "donativo" in msg:
            template_name = "vea_info_donativos"
            parameters = [
                {"name": "customer_name", "value": "Juan Pérez"},
                {"name": "ministry_name", "value": "Ministerio Esperanza"},
                {"name": "bank_name", "value": "BBVA"},
                {"name": "beneficiary_name", "value": "Iglesia Esperanza"},
                {"name": "account_number", "value": "1234567890"},
                {"name": "clabe_number", "value": "012345678901234567"},
                {"name": "contact_name", "value": "Padre Juan"},
                {"name": "contact_phone", "value": "5551234567"}
            ]
        elif "evento" in msg:
            template_name = "vea_event_info"
            parameters = [
                "Juan Pérez",           # customer_name
                "Retiro Espiritual",    # event_name
                "20 de julio, 2024",    # event_date
                "Parroquia San Juan"    # event_location
            ]
        elif "contacto" in msg:
            template_name = "vea_contacto_ministerio"
            parameters = [
                "Juan Pérez",           # customer_name
                "Ministerio Esperanza", # ministry_name
                "Padre Juan",           # contact_name
                "5551234567"            # contact_phone
            ]
        elif "solicitud" in msg:
            template_name = "vea_request_received"
            parameters = [
                "Juan Pérez",           # customer_name
                "Solicitud de oración"  # request_summary
            ]
        else:
            # Si no coincide, responde usando IA generativa
            ai_response = generate_response_with_rag(message_content, from_number)
            if not ai_response:
                ai_response = "¡Hola! Puedes escribir 'donativo', 'evento', 'contacto' o 'solicitud' para recibir información."
            sent_message_id = acs_service.send_whatsapp_text_message(from_number, ai_response)
            if sent_message_id:
                save_conversation_with_context(from_number, message_content, ai_response, timestamp, message_id, sent_message_id)
                logger.info(f"Response sent to {from_number}, message ID: {sent_message_id}")
            else:
                logger.error(f"Failed to send response to {from_number}")
            return

        # Envía la plantilla seleccionada
        sent_message_id = acs_service.send_whatsapp_template_message(
            from_number,
            template_name,
            "es_MX",
            parameters
        )

        if sent_message_id:
            save_conversation_with_context(from_number, message_content, f"[PLANTILLA {template_name} ENVIADA]", timestamp, message_id, sent_message_id)
            logger.info(f"Response sent to {from_number}, message ID: {sent_message_id}")
        else:
            logger.error(f"Failed to send response to {from_number}")

    except Exception as e:
        logger.error(f"Error processing incoming WhatsApp message: {e}")


def generate_response_with_rag(
    user_message: str,
    user_number: str,
    embedding_manager=embedding_manager,
    openai_service=openai_service,
    logger=logger
) -> str | None:
    """
    Generate response using OpenAI with RAG (Retrieval-Augmented Generation).
    Args:
        user_message: User message
        user_number: User phone number
        embedding_manager: gestor de embeddings/contexto (mockeable)
        openai_service: servicio de openai (mockeable)
        logger: logger (mockeable)
    Returns:
        Generated response or None if error
    """
    try:
        # Get embedding for user message
        user_embedding = embedding_manager.get_embedding(user_message)
        if user_embedding is None:
            return None
        # Find similar content using RAG
        similar_content = embedding_manager.find_similar_content(user_embedding, top_k=3)
        # Load conversation history with Redis for active context
        conversation_history = load_conversation_history_with_redis(user_number, embedding_manager=embedding_manager, logger=logger)
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


def save_conversation_with_context(
    user_number: str,
    user_message: str,
    bot_response: str,
    timestamp: str,
    incoming_id: str,
    outgoing_id: str,
    embedding_manager=embedding_manager,
    azure_blob_service=azure_blob_service,
    logger=logger
) -> None:
    """
    Guarda la conversación con contexto en Blob y Redis.
    Args:
        user_number: número del usuario
        user_message: mensaje del usuario
        bot_response: respuesta del bot
        timestamp: timestamp del mensaje
        incoming_id: id del mensaje entrante
        outgoing_id: id del mensaje saliente
        embedding_manager: gestor de embeddings/contexto (mockeable)
        azure_blob_service: servicio de blob (mockeable)
        logger: logger (mockeable)
    """
    try:
        # Cargar conversación existente
        conversation = azure_blob_service.load_conversation(user_number) or {
            "conversation_id": f"acs_{user_number}",
            "user_number": user_number,
            "messages": []
        }
        # Agregar mensajes
        conversation["messages"].append({
            "role": "user",
            "content": user_message,
            "timestamp": timestamp,
            "message_id": incoming_id
        })
        conversation["messages"].append({
            "role": "assistant",
            "content": bot_response,
            "timestamp": timestamp,
            "message_id": outgoing_id
        })
        # Guardar en Blob
        azure_blob_service.save_conversation(conversation)
        # Guardar en Redis/contexto
        embedding_manager.save_conversation_context(user_number, conversation["messages"])
        logger.debug(f"Conversación guardada para {user_number}")
    except Exception as e:
        logger.error(f"Error guardando conversación: {e}")


def load_conversation_history_with_redis(
    user_number: str,
    embedding_manager=embedding_manager,
    azure_blob_service=azure_blob_service,
    logger=logger
) -> list:
    """
    Load conversation history for a user, first from Redis, then fallback to Blob Storage.
    Args:
        user_number: User phone number
        embedding_manager: gestor de embeddings/contexto (mockeable)
        azure_blob_service: servicio de blob (mockeable)
        logger: logger (mockeable)
    Returns:
        List of conversation messages
    """
    try:
        # Primero intenta cargar de Redis
        context = embedding_manager.get_conversation_context(user_number)
        if context:
            logger.debug(f"Contexto cargado de Redis para {user_number}")
            return context
        # Si no hay en Redis, intenta cargar de Blob
        blob_data = azure_blob_service.load_conversation(user_number)
        if blob_data and "messages" in blob_data:
            logger.debug(f"Contexto cargado de Blob para {user_number}")
            # Guarda en Redis para futuras consultas
            embedding_manager.save_conversation_context(user_number, blob_data["messages"])
            return blob_data["messages"]
        logger.debug(f"No se encontró contexto para {user_number}")
        return []
    except Exception as e:
        logger.error(f"Error loading conversation history from Redis: {e}")
        return []


def update_message_status(message_id: str, status: str, timestamp: str) -> None:
    """
    Update message status in storage.
    
    Args:
        message_id: Message ID
        status: Delivery status
        timestamp: Delivery timestamp
    """
    try:
        # Save status to blob storage
        blob_name = f"message_status/{message_id}.json"
        status_data = {
            "message_id": message_id,
            "status": status,
            "timestamp": timestamp
        }
        azure_blob_service.upload_json(blob_name, status_data)
        logger.info(f"Message status updated for {message_id}")
    except Exception as e:
        logger.error(f"Error updating message status: {e}") 