"""
Batch Push Results Azure Function.

This function is triggered by Queue Storage messages to process files,
generate embeddings, and store them in Redis for semantic search.
"""
import azure.functions as func
import logging
import json
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path

from config.settings import settings
from services.azure_blob_service import azure_blob_service
from services.openai_service import openai_service
from services.redis_service import redis_service
from services.computer_vision_service import computer_vision_service
from core.document_processor import DocumentProcessor

# Configuración de logging global
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


def main(msg: func.QueueMessage) -> None:
    """
    Processes queue messages to generate embeddings for documents.
    
    Args:
        msg: The queue message containing file information.
    """
    logger.info("[AUDIT] Entró a batch_push_results.main")
    try:
        # Parse queue message
        message_body = msg.get_body().decode('utf-8')
        queue_data = json.loads(message_body)
        
        blob_name = queue_data.get("blob_name")
        blob_url = queue_data.get("blob_url")
        file_size = queue_data.get("file_size", 0)
        content_type = queue_data.get("content_type", "")
        
        logger.info(f"Processing queue message for blob: {blob_name}")
        
        if not blob_name:
            logger.error("Queue message missing blob_name")
            return
        
        # Process document
        document_processor = DocumentProcessor()
        success = document_processor.process_document_from_queue(
            blob_name=blob_name,
            blob_url=blob_url,
            file_size=file_size,
            content_type=content_type
        )
        
        if success:
            logger.info(f"Successfully processed document: {blob_name}")
        else:
            logger.error(f"Failed to process document: {blob_name}")
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse queue message JSON: {e}")
        raise
    except Exception as e:
        error_message = f"Failed to process queue message: {str(e)}"
        logger.error(error_message)
        raise 