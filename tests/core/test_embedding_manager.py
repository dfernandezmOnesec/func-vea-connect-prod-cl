"""
Tests para el gestor de embeddings.
"""
import os
os.environ["ENVIRONMENT"] = "test"
from unittest.mock import MagicMock
from core.embedding_manager import EmbeddingManager

class TestEmbeddingManager:
    """Tests para EmbeddingManager."""
    
    def test_init(self):
        mock_redis = MagicMock()
        mock_openai = MagicMock()
        manager = EmbeddingManager(mock_redis, mock_openai)
        assert manager.redis_service is not None
        assert manager.openai_service is not None
    
    def test_get_embedding_with_cache_hit(self):
        mock_redis = MagicMock()
        mock_openai = MagicMock()
        mock_redis.get_embedding_cache.return_value = [0.1, 0.2, 0.3]
        manager = EmbeddingManager(mock_redis, mock_openai)
        result = manager.get_embedding("texto de prueba")
        assert result == [0.1, 0.2, 0.3]
        mock_redis.get_embedding_cache.assert_called_once_with("texto de prueba")
        mock_openai.generate_embedding.assert_not_called()
    
    def test_get_embedding_with_cache_miss(self):
        mock_redis = MagicMock()
        mock_openai = MagicMock()
        mock_redis.get_embedding_cache.return_value = None
        mock_openai.generate_embedding.return_value = [0.4, 0.5, 0.6]
        manager = EmbeddingManager(mock_redis, mock_openai)
        result = manager.get_embedding("texto de prueba")
        assert result == [0.4, 0.5, 0.6]
        mock_redis.get_embedding_cache.assert_called_once_with("texto de prueba")
        mock_openai.generate_embedding.assert_called_once_with("texto de prueba")
        mock_redis.set_embedding_cache.assert_called_once_with("texto de prueba", [0.4, 0.5, 0.6])
    
    def test_get_embedding_empty_text(self):
        mock_redis = MagicMock()
        mock_openai = MagicMock()
        manager = EmbeddingManager(mock_redis, mock_openai)
        result = manager.get_embedding("")
        assert result is None
        mock_redis.get_embedding_cache.assert_not_called()
        mock_openai.generate_embedding.assert_not_called()
    
    def test_get_embedding_without_cache(self):
        mock_redis = MagicMock()
        mock_openai = MagicMock()
        mock_openai.generate_embedding.return_value = [0.7, 0.8, 0.9]
        manager = EmbeddingManager(mock_redis, mock_openai)
        result = manager.get_embedding("texto de prueba", use_cache=False)
        assert result == [0.7, 0.8, 0.9]
        mock_redis.get_embedding_cache.assert_not_called()
        mock_openai.generate_embedding.assert_called_once_with("texto de prueba")
        mock_redis.set_embedding_cache.assert_not_called()
    
    def test_get_embeddings_batch(self):
        mock_redis = MagicMock()
        mock_openai = MagicMock()
        mock_redis.get_embedding_cache.return_value = None
        mock_openai.generate_embedding.return_value = [0.1, 0.2, 0.3]
        manager = EmbeddingManager(mock_redis, mock_openai)
        texts = ["texto1", "texto2", "texto3"]
        results = manager.get_embeddings_batch(texts)
        assert len(results) == 3
        assert all(result == [0.1, 0.2, 0.3] for result in results)
        assert mock_openai.generate_embedding.call_count == 3
    
    def test_validate_embedding_valid(self):
        manager = EmbeddingManager(MagicMock(), MagicMock())
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        assert manager.validate_embedding(embedding) is True
    
    def test_validate_embedding_invalid_empty(self):
        manager = EmbeddingManager(MagicMock(), MagicMock())
        assert manager.validate_embedding([]) is False
    
    def test_validate_embedding_invalid_none(self):
        manager = EmbeddingManager(MagicMock(), MagicMock())
        from typing import cast
        assert manager.validate_embedding(cast(list, None)) is False
    
    def test_validate_embedding_invalid_type(self):
        manager = EmbeddingManager(MagicMock(), MagicMock())
        from typing import cast
        assert manager.validate_embedding(cast(list, "not a list")) is False
        assert manager.validate_embedding(cast(list, [0.1, "not a number", 0.3])) is False
    
    def test_get_embedding_dimension(self):
        manager = EmbeddingManager(MagicMock(), MagicMock())
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        dimension = manager.get_embedding_dimension(embedding)
        assert dimension == 5
    
    def test_get_embedding_dimension_invalid(self):
        manager = EmbeddingManager(MagicMock(), MagicMock())
        assert manager.get_embedding_dimension([]) is None
        from typing import cast
        assert manager.get_embedding_dimension(cast(list, "invalid")) is None 