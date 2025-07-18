"""
HTTP trigger function to delete documents from storage, Redis, and queues.
"""
import logging
import json
import azure.functions as func
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import settings
from services.azure_blob_service import azure_blob_service
from services.redis_service import redis_service
from core.embedding_manager import embedding_manager

# Configuración de logging global
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


def main(req: func.HttpRequest, azure_blob_service_instance=None, redis_service_instance=None, embedding_manager_instance=None, logger_instance=None) -> func.HttpResponse:
    """
    Main function to delete documents.
    
    Args:
        req: HTTP request from Azure Functions
        azure_blob_service_instance: instancia de azure_blob_service (opcional)
        redis_service_instance: instancia de redis_service (opcional)
        embedding_manager_instance: instancia de embedding_manager (opcional)
        logger_instance: instancia de logger (opcional)
        
    Returns:
        HttpResponse with result
    """
    blob_service = azure_blob_service_instance or azure_blob_service
    redis_srv = redis_service_instance or redis_service
    embed_mgr = embedding_manager_instance or embedding_manager
    log = logger_instance or logger
    log.info("[AUDIT] Entró a delete_document_function.main")
    try:
        
        # Check HTTP method
        if req.method != "DELETE":
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Method not allowed. Use DELETE."
                }),
                status_code=405,
                mimetype='application/json'
            )
        
        # Get request data
        try:
            body = req.get_json()
        except Exception:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Empty request body"
                }),
                status_code=400,
                mimetype='application/json'
            )
        
        # Validate required data
        if not body or not isinstance(body, dict) or (not body.get('document_id') and not body.get('blob_name')):
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Missing required parameters: document_id or blob_name"
                }),
                status_code=400,
                mimetype='application/json'
            )
        
        document_id = body.get('document_id')
        blob_name = body.get('blob_name')
        
        # Delete document from all services
        deletion_result = delete_document_completely(
            document_id, blob_name,
            azure_blob_service_instance=blob_service,
            redis_service_instance=redis_srv,
            embedding_manager_instance=embed_mgr,
            logger_instance=log
        )
        
        if deletion_result['success']:
            return func.HttpResponse(
                json.dumps({
                    "success": True,
                    "message": "Document deleted successfully",
                    "document_id": document_id,
                    "blob_name": blob_name,
                    "deletion_details": deletion_result['details'],
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=200,
                mimetype='application/json'
            )
        else:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "message": "Failed to delete document completely",
                    "document_id": document_id,
                    "blob_name": blob_name,
                    "deletion_details": deletion_result['details'],
                    "error": deletion_result.get('error', 'Unknown error')
                }),
                status_code=500,
                mimetype='application/json'
            )
            
    except Exception as e:
        log.error(f"Error in delete document function: {e}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            }),
            status_code=500,
            mimetype='application/json'
        )


def delete_document_completely(document_id: Optional[str] = None, blob_name: Optional[str] = None, azure_blob_service_instance=None, redis_service_instance=None, embedding_manager_instance=None, logger_instance=None) -> Dict[str, Any]:
    """
    Delete document from all services (Storage, Redis, Embeddings).
    
    Args:
        document_id: Document ID to delete
        blob_name: Blob name to delete
        azure_blob_service_instance: instancia de azure_blob_service (opcional)
        redis_service_instance: instancia de redis_service (opcional)
        embedding_manager_instance: instancia de embedding_manager (opcional)
        logger_instance: instancia de logger (opcional)
        
    Returns:
        Dictionary with deletion results
    """
    blob_service = azure_blob_service_instance or azure_blob_service
    redis_srv = redis_service_instance or redis_service
    embed_mgr = embedding_manager_instance or embedding_manager
    log = logger_instance or logger
    deletion_details = {
        'storage_deleted': False,
        'redis_deleted': False,
        'embeddings_deleted': False,
        'errors': []
    }
    
    try:
        # 1. Delete from Azure Storage
        if blob_name:
            storage_deleted = blob_service.delete_blob(blob_name)
            deletion_details['storage_deleted'] = storage_deleted
            if not storage_deleted:
                deletion_details['errors'].append(f"Failed to delete blob: {blob_name}")
            else:
                log.info(f"Blob deleted from storage: {blob_name}")
        
        # 2. Delete from Redis (embeddings and metadata)
        if document_id:
            # Delete embeddings
            embedding_keys = [
                f"embedding:{document_id}",
                f"document_metadata:{document_id}",
                f"document_chunks:{document_id}"
            ]
            
            redis_deleted = True
            for key in embedding_keys:
                if redis_srv.delete(key):
                    log.info(f"Redis key deleted: {key}")
                else:
                    redis_deleted = False
                    deletion_details['errors'].append(f"Failed to delete Redis key: {key}")
            
            deletion_details['redis_deleted'] = redis_deleted
        
        # 3. Delete from embedding manager
        if document_id:
            try:
                embeddings_deleted = embed_mgr.delete_document_embeddings(document_id)
                deletion_details['embeddings_deleted'] = embeddings_deleted
                if not embeddings_deleted:
                    deletion_details['errors'].append(f"Failed to delete embeddings for document: {document_id}")
                else:
                    log.info(f"Embeddings deleted for document: {document_id}")
            except Exception as e:
                deletion_details['errors'].append(f"Error deleting embeddings: {str(e)}")
                log.error(f"Error deleting embeddings for {document_id}: {e}")
        
        # Determine overall success
        success = (
            deletion_details['storage_deleted'] or not blob_name,
            deletion_details['redis_deleted'] or not document_id,
            deletion_details['embeddings_deleted'] or not document_id
        )
        
        overall_success = all(success)
        
        if overall_success:
            log.info(f"Document deleted successfully - Document ID: {document_id}, Blob: {blob_name}")
        else:
            log.warning(f"Partial deletion - Document ID: {document_id}, Blob: {blob_name}, Details: {deletion_details}")
        
        return {
            'success': overall_success,
            'details': deletion_details,
            'error': '; '.join(deletion_details['errors']) if deletion_details['errors'] else None
        }
        
    except Exception as e:
        error_msg = f"Error in delete_document_completely: {str(e)}"
        log.error(error_msg)
        deletion_details['errors'].append(error_msg)
        return {
            'success': False,
            'details': deletion_details,
            'error': error_msg
        }


def get_document_info(document_id: str) -> Optional[Dict[str, Any]]:
    """
    Get document information before deletion.
    
    Args:
        document_id: Document ID
        
    Returns:
        Document information or None if not found
    """
    try:
        # Get metadata from Redis
        metadata = redis_service.get_json(f"document_metadata:{document_id}")
        
        # Get blob name from metadata
        blob_name = metadata.get('blob_name') if metadata else None
        
        return {
            'document_id': document_id,
            'blob_name': blob_name,
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"Error getting document info for {document_id}: {e}")
        return None 