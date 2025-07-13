"""
Gestor de embeddings con cache en Redis y generación con OpenAI.
"""
import os
import logging
import json
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Gestor de embeddings con cache y generación."""
    
    def __init__(self, redis_client, openai_service):
        """Inicializar el gestor de embeddings."""
        self.redis_service = redis_client
        self.openai_service = openai_service
        logger.info("EmbeddingManager inicializado")
    
    def get_embedding(self, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """
        Obtener embedding para un texto, usando cache si está disponible.
        
        Args:
            text: Texto para generar embedding
            use_cache: Si usar cache (True por defecto)
            
        Returns:
            Vector de embedding o None si hay error
        """
        if not text or not text.strip():
            logger.warning("Texto vacío proporcionado para embedding")
            return None
        
        # Intentar obtener del cache primero
        if use_cache:
            cached_embedding = self.redis_service.get_embedding_cache(text)
            if cached_embedding:
                logger.debug(f"Embedding obtenido del cache para texto de {len(text)} caracteres")
                return cached_embedding
        
        # Generar nuevo embedding
        embedding = self.openai_service.generate_embedding(text)
        if embedding:
            # Guardar en cache
            if use_cache:
                self.redis_service.set_embedding_cache(text, embedding)
                logger.debug(f"Nuevo embedding generado y guardado en cache para texto de {len(text)} caracteres")
            else:
                logger.debug(f"Nuevo embedding generado (sin cache) para texto de {len(text)} caracteres")
            return embedding
        
        logger.error(f"No se pudo generar embedding para texto de {len(text)} caracteres")
        return None
    
    def get_embeddings_batch(self, texts: List[str], use_cache: bool = True) -> List[Optional[List[float]]]:
        """
        Obtener embeddings para múltiples textos.
        
        Args:
            texts: Lista de textos
            use_cache: Si usar cache
            
        Returns:
            Lista de embeddings (puede contener None para textos con error)
        """
        embeddings = []
        
        for text in texts:
            embedding = self.get_embedding(text, use_cache)
            embeddings.append(embedding)
        
        logger.debug(f"Procesados {len(texts)} textos para embeddings")
        return embeddings
    
    def find_similar_content(self, query_embedding: List[float], top_k: int = 3) -> Optional[str]:
        """
        Encontrar contenido similar usando embeddings.
        
        Args:
            query_embedding: Embedding de la consulta
            top_k: Número de resultados similares a retornar
            
        Returns:
            Contenido similar encontrado o None
        """
        try:
            if not self.validate_embedding(query_embedding):
                logger.warning("Embedding de consulta inválido")
                return None
            
            # Buscar contenido similar en Redis (simulado por ahora)
            # En una implementación real, usarías un vector database como Pinecone o Qdrant
            similar_content = self.redis_service.find_similar_embeddings(query_embedding, top_k)
            
            if similar_content:
                logger.debug(f"Encontrado contenido similar con {len(similar_content)} elementos")
                return similar_content
            
            logger.debug("No se encontró contenido similar")
            return None
            
        except Exception as e:
            logger.error(f"Error al buscar contenido similar: {e}")
            return None
    
    def save_conversation_context(self, user_number: str, context: List[Dict[str, Any]]) -> bool:
        """
        Guardar contexto de conversación en Redis.
        
        Args:
            user_number: Número de teléfono del usuario
            context: Lista de mensajes del contexto
            
        Returns:
            True si se guardó correctamente
        """
        try:
            key = f"conversation_context:{user_number}"
            data = json.dumps(context, ensure_ascii=False)
            
            # Guardar con TTL de 24 horas
            success = self.redis_service.set_with_ttl(key, data, ttl_seconds=86400)
            
            if success:
                logger.debug(f"Contexto de conversación guardado para {user_number}")
            else:
                logger.warning(f"No se pudo guardar contexto para {user_number}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error al guardar contexto de conversación: {e}")
            return False
    
    def get_conversation_context(self, user_number: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtener contexto de conversación desde Redis.
        
        Args:
            user_number: Número de teléfono del usuario
            
        Returns:
            Lista de mensajes del contexto o None si no existe
        """
        try:
            key = f"conversation_context:{user_number}"
            data = self.redis_service.get(key)
            
            if data:
                context = json.loads(data)
                logger.debug(f"Contexto de conversación cargado para {user_number}")
                return context
            
            logger.debug(f"No se encontró contexto para {user_number}")
            return None
            
        except Exception as e:
            logger.error(f"Error al cargar contexto de conversación: {e}")
            return None
    
    def save_message_status(self, message_id: str, status_data: Dict[str, Any]) -> bool:
        """
        Guardar estado de mensaje en Redis.
        
        Args:
            message_id: ID del mensaje
            status_data: Datos del estado
            
        Returns:
            True si se guardó correctamente
        """
        try:
            key = f"message_status:{message_id}"
            data = json.dumps(status_data, ensure_ascii=False)
            
            # Guardar con TTL de 7 días
            success = self.redis_service.set_with_ttl(key, data, ttl_seconds=604800)
            
            if success:
                logger.debug(f"Estado de mensaje guardado: {message_id}")
            else:
                logger.warning(f"No se pudo guardar estado para {message_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error al guardar estado de mensaje: {e}")
            return False
    
    def clear_embedding_cache(self, text: str) -> bool:
        """
        Limpiar cache de embedding para un texto específico.
        
        Args:
            text: Texto cuyo cache se quiere limpiar
            
        Returns:
            True si se limpió correctamente
        """
        try:
            return self.redis_service.delete_cache(f"embedding:{text}")
        except Exception as e:
            logger.error(f"Error al limpiar cache de embedding: {e}")
            return False
    
    def get_cache_stats(self) -> dict:
        """
        Obtener estadísticas del cache de embeddings.
        
        Returns:
            Diccionario con estadísticas del cache
        """
        try:
            # Listar todas las claves de embedding en cache
            import hashlib
            sample_text = "sample"
            sample_hash = hashlib.md5(sample_text.encode()).hexdigest()
            sample_key = f"embedding:{sample_hash}"
            
            # Esto es una aproximación - en Redis real podrías usar SCAN
            # para obtener todas las claves que empiecen con "embedding:"
            return {
                "cache_enabled": True,
                "sample_key_exists": self.redis_service.exists(sample_key),
                "sample_key_ttl": self.redis_service.get_ttl(sample_key)
            }
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de cache: {e}")
            return {"cache_enabled": False, "error": str(e)}
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validar que un embedding tiene el formato correcto.
        
        Args:
            embedding: Vector de embedding a validar
            
        Returns:
            True si el embedding es válido
        """
        if not embedding:
            return False
        
        if not isinstance(embedding, list):
            return False
        
        if not all(isinstance(x, (int, float)) for x in embedding):
            return False
        
        # Verificar que no esté vacío y tenga dimensiones razonables
        if len(embedding) == 0 or len(embedding) > 10000:
            return False
        
        return True
    
    def get_embedding_dimension(self, embedding: List[float]) -> Optional[int]:
        """
        Obtener la dimensión de un embedding.
        
        Args:
            embedding: Vector de embedding
            
        Returns:
            Dimensión del embedding o None si no es válido
        """
        if self.validate_embedding(embedding):
            return len(embedding)
        return None


# Instancia global solo si no es test
def _get_env():
    return os.getenv("ENVIRONMENT", "development")

embedding_manager = None
if _get_env() != "test":
    from services.redis_service import redis_service
    from services.openai_service import openai_service
    embedding_manager = EmbeddingManager(redis_service, openai_service) 