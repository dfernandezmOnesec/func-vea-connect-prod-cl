"""
Servicio de Redis para manejo de cache y almacenamiento temporal.
"""
import json
import logging
from typing import Optional, Any, Dict, List
import redis
from config.settings import settings
from unittest.mock import Mock

logger = logging.getLogger(__name__)


class RedisService:
    """Servicio para interactuar con Redis."""
    
    def __init__(self):
        """Inicializar conexión con Redis (lazy)."""
        self._redis_client = None
        self._initialized = False
    
    def _initialize_client(self):
        if self._initialized:
            return
        if settings.environment == "test":
            self._redis_client = Mock()
            self._initialized = True
            logger.warning("Redis mockeado en entorno de pruebas")
            return
        try:
            self._redis_client = redis.from_url(
                settings.redis_connection_string,
                decode_responses=True
            )
            if self._redis_client is not None:
                self._redis_client.ping()
            self._initialized = True
            logger.info("Conexión a Redis establecida correctamente")
        except Exception as e:
            logger.error(f"Error al conectar con Redis: {e}")
            raise
    
    @property
    def redis_client(self):
        if not self._initialized:
            self._initialize_client()
        return self._redis_client
    
    def set_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Almacenar valor en cache con TTL opcional.
        
        Args:
            key: Clave del cache
            value: Valor a almacenar (se serializa como JSON)
            ttl: Tiempo de vida en segundos (usa configuración por defecto si None)
            
        Returns:
            True si se almacenó correctamente
        """
        try:
            if self.redis_client is None:
                logger.warning("Redis no inicializado, set_cache ignorado")
                return False
            if ttl is None:
                ttl = settings.redis_cache_ttl
            
            serialized_value = json.dumps(value)
            result = self.redis_client.setex(key, ttl, serialized_value)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return bool(result)
        except Exception as e:
            logger.error(f"Error al establecer cache para {key}: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """
        Obtener valor del cache.
        
        Args:
            key: Clave del cache
            
        Returns:
            Valor deserializado o None si no existe
        """
        try:
            if self.redis_client is None:
                logger.warning("Redis no inicializado, get_cache ignorado")
                return None
            value = self.redis_client.get(key)
            if value is None:
                logger.debug(f"Cache miss: {key}")
                return None
            
            logger.debug(f"Cache hit: {key}")
            return json.loads(str(value))
        except Exception as e:
            logger.error(f"Error al obtener cache para {key}: {e}")
            return None
    
    def get(self, key: str) -> Optional[str]:
        """
        Obtener valor como string desde Redis.
        
        Args:
            key: Clave a obtener
            
        Returns:
            Valor como string o None si no existe
        """
        try:
            if self.redis_client is None:
                logger.warning("Redis no inicializado, get ignorado")
                return None
            value = self.redis_client.get(key)
            logger.debug(f"Redis get: {key}")
            return str(value) if value is not None else None
        except Exception as e:
            logger.error(f"Error al obtener {key}: {e}")
            return None
    
    def set_with_ttl(self, key: str, value: str, ttl_seconds: int) -> bool:
        """
        Almacenar valor con TTL específico.
        
        Args:
            key: Clave a almacenar
            value: Valor como string
            ttl_seconds: Tiempo de vida en segundos
            
        Returns:
            True si se almacenó correctamente
        """
        try:
            if self.redis_client is None:
                logger.warning("Redis no inicializado, set_with_ttl ignorado")
                return False
            result = self.redis_client.setex(key, ttl_seconds, value)
            logger.debug(f"Redis set with TTL: {key} (TTL: {ttl_seconds}s)")
            return bool(result)
        except Exception as e:
            logger.error(f"Error al establecer {key} con TTL: {e}")
            return False
    
    def find_similar_embeddings(self, query_embedding: List[float], top_k: int = 3) -> Optional[str]:
        """
        Buscar embeddings similares (simulado - en producción usar vector database).
        
        Args:
            query_embedding: Embedding de consulta
            top_k: Número de resultados a retornar
            
        Returns:
            Contenido similar encontrado o None
        """
        try:
            # Esta es una implementación simulada
            # En producción, usarías un vector database como Pinecone, Qdrant, o Redis Stack
            # con módulo de búsqueda vectorial
            
            logger.debug(f"Buscando embeddings similares (top_k={top_k})")
            
            # Simular contenido similar basado en la consulta
            # En una implementación real, calcularías similitud coseno o euclidiana
            sample_content = "Este es contenido de ejemplo que podría ser relevante para la consulta del usuario."
            
            return sample_content
            
        except Exception as e:
            logger.error(f"Error al buscar embeddings similares: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """
        Eliminar clave del cache.
        
        Args:
            key: Clave a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            if self.redis_client is None:
                logger.warning("Redis no inicializado, delete_cache ignorado")
                return False
            result = self.redis_client.delete(key)
            if isinstance(result, int):
                return result > 0
            return False
        except Exception as e:
            logger.error(f"Error al eliminar cache para {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Verificar si una clave existe en el cache.
        
        Args:
            key: Clave a verificar
            
        Returns:
            True si la clave existe
        """
        try:
            if self.redis_client is None:
                logger.warning("Redis no inicializado, exists ignorado")
                return False
            result = self.redis_client.exists(key)
            if isinstance(result, int):
                return result > 0
            return False
        except Exception as e:
            logger.error(f"Error al verificar existencia de {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """
        Obtener el TTL restante de una clave.
        
        Args:
            key: Clave a verificar
            
        Returns:
            TTL en segundos o None si no existe
        """
        try:
            if self.redis_client is None:
                logger.warning("Redis no inicializado, get_ttl ignorado")
                return None
            ttl = self.redis_client.ttl(key)
            if isinstance(ttl, int):
                return ttl if ttl > 0 else None
            return None
        except Exception as e:
            logger.error(f"Error al obtener TTL de {key}: {e}")
            return None
    
    def set_embedding_cache(self, text: str, embedding: list, ttl: Optional[int] = None) -> bool:
        """
        Almacenar embedding en cache con hash del texto como clave.
        
        Args:
            text: Texto original
            embedding: Vector de embedding
            ttl: Tiempo de vida específico para embeddings
            
        Returns:
            True si se almacenó correctamente
        """
        if ttl is None:
            ttl = settings.embedding_cache_ttl
        
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"embedding:{text_hash}"
        
        return self.set_cache(cache_key, embedding, ttl)
    
    def get_embedding_cache(self, text: str) -> Optional[list]:
        """
        Obtener embedding del cache usando hash del texto.
        
        Args:
            text: Texto original
            
        Returns:
            Vector de embedding o None si no existe
        """
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"embedding:{text_hash}"
        
        return self.get_cache(cache_key)
    
    def store_embedding(self, document_id: str, embedding: list, metadata: dict) -> bool:
        """
        Store document embedding and metadata in Redis.
        
        Args:
            document_id: Unique document identifier
            embedding: Embedding vector
            metadata: Document metadata
            
        Returns:
            True if storage successful
        """
        try:
            # Store embedding
            embedding_key = f"embedding:{document_id}"
            self.set_cache(embedding_key, embedding, ttl=settings.embedding_cache_ttl)
            
            # Store metadata
            metadata_key = f"metadata:{document_id}"
            self.set_cache(metadata_key, metadata, ttl=settings.embedding_cache_ttl)
            
            logger.info(f"Embedding stored for document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing embedding for document {document_id}: {e}")
            return False
    
    def close(self):
        """Cerrar conexión con Redis."""
        try:
            if self.redis_client is None:
                logger.warning("Redis no inicializado, close ignorado")
                return
            self.redis_client.close()
            logger.info("Conexión a Redis cerrada")
        except Exception as e:
            logger.error(f"Error al cerrar conexión con Redis: {e}")


# Instancia global del servicio
redis_service = RedisService() 