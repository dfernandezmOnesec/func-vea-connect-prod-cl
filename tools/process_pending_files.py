import os
import logging
import json
from services.azure_blob_service import azure_blob_service
from azure.storage.queue import QueueClient
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
connect_str = settings.azure_storage_connection_string
container_name = settings.blob_container_name
queue_name = settings.queue_name
max_files_per_batch = int(os.getenv('MAX_FILES_PER_BATCH', 50))


def send_to_queue(queue_client, message):
    """Envía un mensaje a la cola."""
    queue_client.send_message(json.dumps(message))


def process_pending_files():
    """Escanea archivos pendientes y los envía a la cola si no tienen embeddings."""
    logger.info("Buscando archivos pendientes en Blob Storage...")
    blob_files = azure_blob_service.list_blobs(container_name)
    pending_files = []
    for blob in blob_files:
        metadata = azure_blob_service.get_blob_metadata(blob.name) or {}
        if not metadata.get('embeddings_added') == 'true':
            pending_files.append({'blob_name': blob.name})
    logger.info(f"Encontrados {len(pending_files)} archivos pendientes de procesar")
    queue_client = QueueClient.from_connection_string(connect_str, queue_name)
    processed_count = 0
    for i in range(0, len(pending_files), max_files_per_batch):
        batch = pending_files[i:i + max_files_per_batch]
        for file_info in batch:
            send_to_queue(queue_client, file_info)
        processed_count += len(batch)
        logger.info(f"Enviado lote de {len(batch)} archivos a la cola")
    logger.info(f"Total enviados a la cola: {processed_count}")
    return processed_count

if __name__ == "__main__":
    process_pending_files() 