import logging
import os
import azure.functions as func
from azure.storage.queue import QueueClient
from services.azure_blob_service import azure_blob_service
from config.settings import settings

logger = logging.getLogger(__name__)

connect_str = settings.azure_storage_connection_string
container_name = settings.blob_container_name
queue_name = settings.queue_name


def main(blob: func.InputStream):
    logger.info(f"[AUDIT] Nuevo archivo detectado: {blob.name} ({blob.length if hasattr(blob, 'length') else 'unknown'} bytes)")
    try:
        file_name = blob.name if hasattr(blob, 'name') else None
        if not file_name:
            logger.warning("No se pudo obtener el nombre del archivo del blob.")
            return
        # Ignorar carpetas especiales o archivos ya procesados
        if file_name.lower().endswith(".zip") or "converted/" in file_name or "processed/" in file_name:
            logger.info(f"Archivo ignorado: {file_name}")
            return
        # Verificar metadatos
        metadata = azure_blob_service.get_blob_metadata(file_name) or {}
        if metadata.get("embeddings_added") == "true":
            logger.info(f"El archivo {file_name} ya tiene embeddings")
            return
        # Enviar a la cola
        queue_client = QueueClient.from_connection_string(connect_str, queue_name)
        queue_client.send_message(f'{{"blob_name": "{file_name}"}}')
        logger.info(f"Archivo enviado a la cola para procesamiento batch: {file_name}")
    except Exception as e:
        logger.error(f"Error en trigger de blob_to_queue: {str(e)}")
        raise 