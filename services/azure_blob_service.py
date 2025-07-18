"""
Servicio de Azure Blob Storage para almacenamiento de archivos y datos.
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from config.settings import settings
import re

logger = logging.getLogger(__name__)


def sanitize_blob_name(name: str) -> str:
    """
    Sanitiza el nombre del blob para cumplir con las reglas de Azure Storage.
    Reemplaza espacios y caracteres no válidos, y evita / al inicio o final.
    """
    name = name.strip().replace(' ', '_')
    name = re.sub(r'[^a-zA-Z0-9/._-]', '', name)
    name = name.strip('/')
    return name


class AzureBlobService:
    """Servicio para interactuar con Azure Blob Storage."""
    
    def __init__(
        self,
        blob_service_client=None,
        container_client=None,
        logger_instance=None,
        container_name=None,
        settings_instance=None
    ):
        """Inicializar cliente de Azure Blob Storage con inyección de dependencias opcional."""
        self._blob_service_client = blob_service_client
        self._container_client = container_client
        self._initialized = blob_service_client is not None and container_client is not None
        self.settings = settings_instance or settings
        self.container_name = container_name or self.settings.blob_container_name
        self.logger = logger_instance or logger
    
    def _initialize_client(self):
        """Inicializar el cliente de Azure Blob Storage de forma lazy."""
        if self._initialized:
            return
            
        try:
            # Verificar que la cadena de conexión no esté vacía
            if not self.settings.azure_storage_connection_string:
                raise ValueError("Azure Storage connection string is not configured")
                
            self._blob_service_client = BlobServiceClient.from_connection_string(
                self.settings.azure_storage_connection_string
            )
            self._container_client = self._blob_service_client.get_container_client(
                self.container_name
            )
            
            # Crear contenedor si no existe
            self._ensure_container_exists()
            self._initialized = True
            self.logger.info(f"Cliente Azure Blob Storage inicializado para contenedor: {self.container_name}")
        except Exception as e:
            self.logger.error(f"Error al inicializar Azure Blob Storage: {e}")
            # En entorno de prueba, no lanzar excepción
            if self.settings.environment == "test":
                self.logger.warning("Azure Blob Storage no disponible en entorno de prueba")
                return
            raise
    
    @property
    def blob_service_client(self):
        """Obtener el cliente de blob service, inicializándolo si es necesario."""
        if not self._initialized:
            self._initialize_client()
        return self._blob_service_client
    
    @property
    def container_client(self):
        """Obtener el cliente de contenedor, inicializándolo si es necesario."""
        if not self._initialized:
            self._initialize_client()
        return self._container_client
    
    def _ensure_container_exists(self):
        """Asegurar que el contenedor existe."""
        try:
            if self._container_client is None:
                return
            self._container_client.get_container_properties()
        except Exception:
            if self._blob_service_client is not None:
                self._blob_service_client.create_container(self.container_name)
                self.logger.info(f"Contenedor {self.container_name} creado")
    
    def upload_text(self, blob_name: str, text: str, metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Subir texto como blob.
        
        Args:
            blob_name: Nombre del blob
            text: Texto a subir
            metadata: Metadatos opcionales
            
        Returns:
            True si se subió correctamente
        """
        try:
            blob_name = sanitize_blob_name(blob_name)
            if not self._initialized:
                self._initialize_client()
                if not self._initialized:
                    self.logger.warning("Azure Blob Storage no disponible")
                    return False
            assert self._container_client is not None
            blob_client = self._container_client.get_blob_client(blob_name)
            blob_client.upload_blob(text, overwrite=True, metadata=metadata)
            self.logger.debug(f"Texto subido como blob: {blob_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error al subir texto como blob {blob_name}: {e}")
            return False
    
    def upload_json(self, blob_name: str, data: Dict[str, Any], metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Subir datos JSON como blob.
        
        Args:
            blob_name: Nombre del blob
            data: Datos JSON a subir
            metadata: Metadatos opcionales
            
        Returns:
            True si se subió correctamente
        """
        try:
            blob_name = sanitize_blob_name(blob_name)
            json_text = json.dumps(data, ensure_ascii=False, indent=2)
            return self.upload_text(blob_name, json_text, metadata)
        except Exception as e:
            self.logger.error(f"Error al subir JSON como blob {blob_name}: {e}")
            return False
    
    def download_text(self, blob_name: str) -> Optional[str]:
        """
        Descargar texto de un blob.
        
        Args:
            blob_name: Nombre del blob
            
        Returns:
            Texto del blob o None si hay error
        """
        try:
            blob_name = sanitize_blob_name(blob_name)
            if not self._initialized:
                self._initialize_client()
                if not self._initialized or self._container_client is None:
                    self.logger.warning("Azure Blob Storage no disponible")
                    return None
            assert self._container_client is not None
            blob_client = self._container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            text = download_stream.readall().decode('utf-8')
            self.logger.debug(f"Texto descargado del blob: {blob_name}")
            return text
        except Exception as e:
            self.logger.error(f"Error al descargar texto del blob {blob_name}: {e}")
            return None
    
    def download_json(self, blob_name: str) -> Optional[Dict[str, Any]]:
        """
        Descargar datos JSON de un blob.
        
        Args:
            blob_name: Nombre del blob
            
        Returns:
            Datos JSON del blob o None si hay error
        """
        try:
            blob_name = sanitize_blob_name(blob_name)
            text = self.download_text(blob_name)
            if text:
                return json.loads(text)
            return None
        except Exception as e:
            self.logger.error(f"Error al descargar JSON del blob {blob_name}: {e}")
            return None
    
    def delete_blob(self, blob_name: str) -> bool:
        """
        Eliminar un blob.
        
        Args:
            blob_name: Nombre del blob a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            blob_name = sanitize_blob_name(blob_name)
            assert self._container_client is not None
            blob_client = self._container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            self.logger.debug(f"Blob eliminado: {blob_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error al eliminar blob {blob_name}: {e}")
            return False
    
    def list_blobs(self, name_starts_with: Optional[str] = None) -> List[str]:
        """
        Listar blobs en el contenedor.
        
        Args:
            name_starts_with: Filtro de nombres que empiecen con
            
        Returns:
            Lista de nombres de blobs
        """
        try:
            assert self._container_client is not None
            blobs = self._container_client.list_blobs(name_starts_with=name_starts_with)
            blob_names = [blob.name for blob in blobs]
            self.logger.debug(f"Listados {len(blob_names)} blobs")
            return blob_names
        except Exception as e:
            self.logger.error(f"Error al listar blobs: {e}")
            return []
    
    def blob_exists(self, blob_name: str) -> bool:
        """
        Verificar si un blob existe.
        
        Args:
            blob_name: Nombre del blob
            
        Returns:
            True si el blob existe
        """
        try:
            assert self._container_client is not None
            blob_client = self._container_client.get_blob_client(blob_name)
            blob_client.get_blob_properties()
            return True
        except Exception:
            return False
    
    def get_blob_metadata(self, blob_name: str) -> Optional[Dict[str, str]]:
        """
        Obtener metadatos de un blob.
        
        Args:
            blob_name: Nombre del blob
            
        Returns:
            Metadatos del blob o None si hay error
        """
        try:
            blob_name = sanitize_blob_name(blob_name)
            assert self._container_client is not None
            blob_client = self._container_client.get_blob_client(blob_name)
            properties = blob_client.get_blob_properties()
            return properties.metadata
        except Exception as e:
            self.logger.error(f"Error al obtener metadatos del blob {blob_name}: {e}")
            return None
    
    def save_conversation(self, conversation_id: str, messages: List[Dict[str, Any]]) -> bool:
        """
        Guardar conversación como JSON en blob storage.
        
        Args:
            conversation_id: ID único de la conversación
            messages: Lista de mensajes de la conversación
            
        Returns:
            True si se guardó correctamente
        """
        try:
            conversation_id = sanitize_blob_name(conversation_id)
            timestamp = datetime.utcnow().isoformat()
            data = {
                "conversation_id": conversation_id,
                "timestamp": timestamp,
                "messages": messages
            }
            
            blob_name = f"conversations/{conversation_id}.json"
            metadata = {
                "conversation_id": conversation_id,
                "timestamp": timestamp,
                "message_count": str(len(messages))
            }
            
            return self.upload_json(blob_name, data, metadata)
        except Exception as e:
            self.logger.error(f"Error al guardar conversación {conversation_id}: {e}")
            return False
    
    def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Cargar conversación desde blob storage.
        
        Args:
            conversation_id: ID de la conversación
            
        Returns:
            Datos de la conversación o None si no existe
        """
        try:
            conversation_id = sanitize_blob_name(conversation_id)
            blob_name = f"conversations/{conversation_id}.json"
            return self.download_json(blob_name)
        except Exception as e:
            self.logger.error(f"Error al cargar conversación {conversation_id}: {e}")
            return None
    
    def download_file(self, blob_name: str, local_file_path: str) -> bool:
        """
        Download file from blob storage to local path.
        
        Args:
            blob_name: Name of the blob to download
            local_file_path: Local path to save the file
            
        Returns:
            True if download successful
        """
        try:
            blob_name = sanitize_blob_name(blob_name)
            assert self._container_client is not None
            blob_client = self._container_client.get_blob_client(blob_name)
            with open(local_file_path, "wb") as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
            self.logger.info(f"File downloaded from blob: {blob_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error downloading file from blob {blob_name}: {e}")
            return False
    
    def update_blob_metadata(self, blob_name: str, metadata: Dict[str, str]) -> bool:
        """
        Update blob metadata.
        
        Args:
            blob_name: Name of the blob
            metadata: Metadata to update
            
        Returns:
            True if update successful
        """
        try:
            blob_name = sanitize_blob_name(blob_name)
            assert self._container_client is not None
            blob_client = self._container_client.get_blob_client(blob_name)
            blob_client.set_blob_metadata(metadata)
            self.logger.info(f"Metadata updated for blob: {blob_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating metadata for blob {blob_name}: {e}")
            return False


# Instancia global del servicio
azure_blob_service = AzureBlobService() 