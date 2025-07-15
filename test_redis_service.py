"""
Unit tests for Redis Service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from services.redis_service import RedisService


class TestRedisService:
    """Test cases for Redis Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('services.redis_service.settings') as mock_settings:
            mock_settings.redis_connection_string = "redis://localhost:6379"
            mock_settings.redis_cache_ttl = 3600
            mock_settings.embedding_cache_ttl = 86400

            self.mock_redis_client = Mock()
            self.service = RedisService(redis_client=self.mock_redis_client)
    
    def test_init_success(self):
        """Test successful initialization."""
        assert self.service.client == self.mock_redis_client
        assert self.service.default_ttl == 3600
        assert self.service.embedding_ttl == 86400
    
    def test_set_success(self):
        """Test successful set operation."""
        key = "test_key"
        value = "test_value"
        ttl = 1800
        
        self.mock_redis_client.setex.return_value = True
        
        result = self.service.set(key, value, ttl)
        
        assert result is True
        self.mock_redis_client.setex.assert_called_once_with(key, ttl, value)
    
    def test_set_with_default_ttl(self):
        """Test set operation with default TTL."""
        key = "test_key"
        value = "test_value"
        
        self.mock_redis_client.setex.return_value = True
        
        result = self.service.set(key, value)
        
        assert result is True
        self.mock_redis_client.setex.assert_called_once_with(key, 3600, value)
    
    def test_set_failure(self):
        """Test set operation failure."""
        key = "test_key"
        value = "test_value"
        
        self.mock_redis_client.setex.side_effect = Exception("Redis error")
        
        result = self.service.set(key, value)
        
        assert result is False
    
    def test_get_success(self):
        """Test successful get operation."""
        key = "test_key"
        expected_value = "test_value"
        
        self.mock_redis_client.get.return_value = expected_value.encode('utf-8')
        
        result = self.service.get(key)
        
        assert result == expected_value
        self.mock_redis_client.get.assert_called_once_with(key)
    
    def test_get_nonexistent_key(self):
        """Test get operation with nonexistent key."""
        key = "nonexistent_key"
        
        self.mock_redis_client.get.return_value = None
        
        result = self.service.get(key)
        
        assert result is None
    
    def test_get_failure(self):
        """Test get operation failure."""
        key = "test_key"
        
        self.mock_redis_client.get.side_effect = Exception("Redis error")
        
        result = self.service.get(key)
        
        assert result is None
    
    def test_delete_success(self):
        """Test successful delete operation."""
        key = "test_key"
        
        self.mock_redis_client.delete.return_value = 1
        
        result = self.service.delete(key)
        
        assert result is True
        self.mock_redis_client.delete.assert_called_once_with(key)
    
    def test_delete_nonexistent_key(self):
        """Test delete operation with nonexistent key."""
        key = "nonexistent_key"
        
        self.mock_redis_client.delete.return_value = 0
        
        result = self.service.delete(key)
        
        assert result is False
    
    def test_delete_failure(self):
        """Test delete operation failure."""
        key = "test_key"
        
        self.mock_redis_client.delete.side_effect = Exception("Redis error")
        
        result = self.service.delete(key)
        
        assert result is False
    
    def test_exists_true(self):
        """Test exists operation when key exists."""
        key = "test_key"
        
        self.mock_redis_client.exists.return_value = 1
        
        result = self.service.exists(key)
        
        assert result is True
        self.mock_redis_client.exists.assert_called_once_with(key)
    
    def test_exists_false(self):
        """Test exists operation when key doesn't exist."""
        key = "test_key"
        
        self.mock_redis_client.exists.return_value = 0
        
        result = self.service.exists(key)
        
        assert result is False
    
    def test_exists_failure(self):
        """Test exists operation failure."""
        key = "test_key"
        
        self.mock_redis_client.exists.side_effect = Exception("Redis error")
        
        result = self.service.exists(key)
        
        assert result is False
    
    def test_set_json_success(self):
        """Test successful JSON set operation."""
        key = "test_key"
        data = {"name": "test", "value": 123}
        ttl = 1800
        
        with patch.object(self.service, 'set') as mock_set:
            mock_set.return_value = True
            
            result = self.service.set_json(key, data, ttl)
            
            assert result is True
            mock_set.assert_called_once()
            call_args = mock_set.call_args
            assert call_args[0][0] == key
            assert call_args[0][2] == ttl
            # Verify JSON serialization
            assert json.loads(call_args[0][1]) == data
    
    def test_set_json_failure(self):
        """Test JSON set operation failure."""
        key = "test_key"
        data = {"name": "test"}
        
        with patch.object(self.service, 'set') as mock_set:
            mock_set.return_value = False
            
            result = self.service.set_json(key, data)
            
            assert result is False
    
    def test_get_json_success(self):
        """Test successful JSON get operation."""
        key = "test_key"
        expected_data = {"name": "test", "value": 123}
        
        with patch.object(self.service, 'get') as mock_get:
            mock_get.return_value = json.dumps(expected_data)
            
            result = self.service.get_json(key)
            
            assert result == expected_data
    
    def test_get_json_nonexistent_key(self):
        """Test JSON get operation with nonexistent key."""
        key = "nonexistent_key"
        
        with patch.object(self.service, 'get') as mock_get:
            mock_get.return_value = None
            
            result = self.service.get_json(key)
            
            assert result is None
    
    def test_get_json_invalid_json(self):
        """Test JSON get operation with invalid JSON."""
        key = "test_key"
        
        with patch.object(self.service, 'get') as mock_get:
            mock_get.return_value = "invalid json"
            
            result = self.service.get_json(key)
            
            assert result is None
    
    def test_set_embedding_success(self):
        """Test successful embedding set operation."""
        key = "embedding_key"
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        with patch.object(self.service, 'set_json') as mock_set_json:
            mock_set_json.return_value = True
            
            result = self.service.set_embedding(key, embedding)
            
            assert result is True
            mock_set_json.assert_called_once_with(key, embedding, 86400)
    
    def test_set_embedding_failure(self):
        """Test embedding set operation failure."""
        key = "embedding_key"
        embedding = [0.1, 0.2, 0.3]
        
        with patch.object(self.service, 'set_json') as mock_set_json:
            mock_set_json.return_value = False
            
            result = self.service.set_embedding(key, embedding)
            
            assert result is False
    
    def test_get_embedding_success(self):
        """Test successful embedding get operation."""
        key = "embedding_key"
        expected_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        with patch.object(self.service, 'get_json') as mock_get_json:
            mock_get_json.return_value = expected_embedding
            
            result = self.service.get_embedding(key)
            
            assert result == expected_embedding
    
    def test_get_embedding_nonexistent(self):
        """Test embedding get operation with nonexistent key."""
        key = "embedding_key"
        
        with patch.object(self.service, 'get_json') as mock_get_json:
            mock_get_json.return_value = None
            
            result = self.service.get_embedding(key)
            
            assert result is None
    
    def test_set_conversation_context_success(self):
        """Test successful conversation context set operation."""
        user_id = "user_123"
        context = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]
        
        with patch.object(self.service, 'set_json') as mock_set_json:
            mock_set_json.return_value = True
            
            result = self.service.set_conversation_context(user_id, context)
            
            assert result is True
            mock_set_json.assert_called_once_with(f"conversation:{user_id}", context)
    
    def test_set_conversation_context_failure(self):
        """Test conversation context set operation failure."""
        user_id = "user_123"
        context = [{"role": "user", "content": "Hello"}]
        
        with patch.object(self.service, 'set_json') as mock_set_json:
            mock_set_json.return_value = False
            
            result = self.service.set_conversation_context(user_id, context)
            
            assert result is False
    
    def test_get_conversation_context_success(self):
        """Test successful conversation context get operation."""
        user_id = "user_123"
        expected_context = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]
        
        with patch.object(self.service, 'get_json') as mock_get_json:
            mock_get_json.return_value = expected_context
            
            result = self.service.get_conversation_context(user_id)
            
            assert result == expected_context
    
    def test_get_conversation_context_nonexistent(self):
        """Test conversation context get operation with nonexistent key."""
        user_id = "user_123"
        
        with patch.object(self.service, 'get_json') as mock_get_json:
            mock_get_json.return_value = None
            
            result = self.service.get_conversation_context(user_id)
            
            assert result == []
    
    def test_clear_conversation_context_success(self):
        """Test successful conversation context clear operation."""
        user_id = "user_123"
        
        with patch.object(self.service, 'delete') as mock_delete:
            mock_delete.return_value = True
            
            result = self.service.clear_conversation_context(user_id)
            
            assert result is True
            mock_delete.assert_called_once_with(f"conversation:{user_id}")
    
    def test_clear_conversation_context_failure(self):
        """Test conversation context clear operation failure."""
        user_id = "user_123"
        
        with patch.object(self.service, 'delete') as mock_delete:
            mock_delete.return_value = False
            
            result = self.service.clear_conversation_context(user_id)
            
            assert result is False
    
    def test_ping_success(self):
        """Test successful ping operation."""
        self.mock_redis_client.ping.return_value = True
        
        result = self.service.ping()
        
        assert result is True
        self.mock_redis_client.ping.assert_called_once()
    
    def test_ping_failure(self):
        """Test ping operation failure."""
        self.mock_redis_client.ping.side_effect = Exception("Redis connection failed")
        
        result = self.service.ping()
        
        assert result is False
    
    def test_get_info_success(self):
        """Test successful info retrieval."""
        expected_info = {
            "redis_version": "6.2.0",
            "connected_clients": 10,
            "used_memory": "1048576"
        }
        
        self.mock_redis_client.info.return_value = expected_info
        
        result = self.service.get_info()
        
        assert result == expected_info
        self.mock_redis_client.info.assert_called_once()
    
    def test_get_info_failure(self):
        """Test info retrieval failure."""
        self.mock_redis_client.info.side_effect = Exception("Redis error")
        
        result = self.service.get_info()
        
        assert result is None
    
    def test_flush_all_success(self):
        """Test successful flush all operation."""
        self.mock_redis_client.flushall.return_value = True
        
        result = self.service.flush_all()
        
        assert result is True
        self.mock_redis_client.flushall.assert_called_once()
    
    def test_flush_all_failure(self):
        """Test flush all operation failure."""
        self.mock_redis_client.flushall.side_effect = Exception("Redis error")
        
        result = self.service.flush_all()
        
        assert result is False 