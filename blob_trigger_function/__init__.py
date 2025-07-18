import logging
import azure.functions as func
from core.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

def main(blob: func.InputStream):
    """
    Azure Function con trigger de Blob Storage para procesar archivos subidos automáticamente.
    """
    logger.info("[AUDIT] Entró a blob_trigger_function.main")
    try:
        blob_name = str(blob.name) if hasattr(blob, 'name') and blob.name else 'unknown_blob'
        logger.info(f"[DEBUG] Blob name: {blob_name}")
        logger.info(f"[DEBUG] Blob size: {blob.length if hasattr(blob, 'length') else 'unknown'}")
        
        logger.info(f"[DEBUG] Iniciando procesamiento del documento: {blob_name}")
        document_processor = DocumentProcessor()
        logger.info(f"[DEBUG] DocumentProcessor inicializado correctamente")
        
        success = document_processor.process_document_from_blob(blob, blob_name)
        logger.info(f"[DEBUG] Resultado del procesamiento: {success}")
        
        if success:
            logger.info(f"[SUCCESS] Documento procesado exitosamente desde blob trigger: {blob_name}")
        else:
            logger.error(f"[ERROR] Falló el procesamiento del documento desde blob trigger: {blob_name}")
    except Exception as e:
        logger.error(f"[ERROR] Excepción en blob_trigger_function: {e}")
        logger.error(f"[ERROR] Tipo de excepción: {type(e).__name__}")
        import traceback
        logger.error(f"[ERROR] Traceback completo: {traceback.format_exc()}")
        raise 