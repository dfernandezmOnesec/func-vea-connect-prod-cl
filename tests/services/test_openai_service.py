"""
Tests for Azure OpenAI service.
"""
import pytest
from unittest.mock import patch, Mock
from services.openai_service import AzureOpenAIService

@pytest.fixture
def mock_settings():
    mock = Mock()
    mock.openai_api_key = "test-openai-key"
    mock.azure_openai_chat_api_version = "2025-01-01-preview"
    mock.azure_openai_endpoint = "https://test-openai.openai.azure.com/"
    mock.azure_openai_chat_deployment = "gpt-35-turbo"
    mock.azure_openai_embeddings_deployment = "text-embedding-ada-002"
    mock.azure_openai_embeddings_api_version = "2023-05-15"
    return mock


class TestAzureOpenAIService:
    """Tests for AzureOpenAIService."""
    
    def test_init(self, mock_settings):
        """Test initialization."""
        with patch('services.openai_service.AzureOpenAI') as mock_client:
            service = AzureOpenAIService(
                client=mock_client.return_value,
                logger_instance=Mock(),
                settings_instance=mock_settings
            )
            assert service.chat_deployment == "gpt-35-turbo"
            assert service.embeddings_deployment == "text-embedding-ada-002"
            # mock_client.assert_called_once_with(...) se elimina porque no se debe llamar si se pasa el cliente
    
    def test_generate_embedding_success(self, mock_settings):
        """Test successful embedding generation."""
        with patch('services.openai_service.AzureOpenAI') as mock_client:
            # Mock embedding response
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
            mock_client.return_value.embeddings.create.return_value = mock_response
            service = AzureOpenAIService(
                client=mock_client.return_value,
                logger_instance=Mock(),
                settings_instance=mock_settings
            )
            result = service.generate_embedding("test text")
            
            assert result == [0.1, 0.2, 0.3]
            mock_client.return_value.embeddings.create.assert_called_once_with(
                input="test text",
                model="text-embedding-ada-002"
            )
    
    def test_generate_embedding_failure(self, mock_settings):
        """Test failed embedding generation."""
        with patch('services.openai_service.AzureOpenAI') as mock_client:
            # Mock exception
            mock_client.return_value.embeddings.create.side_effect = Exception("API error")
            service = AzureOpenAIService(
                client=mock_client.return_value,
                logger_instance=Mock(),
                settings_instance=mock_settings
            )
            result = service.generate_embedding("test text")
            
            assert result is None
    
    def test_generate_text_success(self, mock_settings):
        """Test successful text generation."""
        with patch('services.openai_service.AzureOpenAI') as mock_client:
            # Mock chat completion response
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Generated response"))]
            mock_client.return_value.chat.completions.create.return_value = mock_response
            service = AzureOpenAIService(
                client=mock_client.return_value,
                logger_instance=Mock(),
                settings_instance=mock_settings
            )
            result = service.generate_text("test prompt")
            
            assert result == "Generated response"
            mock_client.return_value.chat.completions.create.assert_called_once()
    
    def test_generate_text_failure(self, mock_settings):
        """Test failed text generation."""
        with patch('services.openai_service.AzureOpenAI') as mock_client:
            # Mock exception
            mock_client.return_value.chat.completions.create.side_effect = Exception("API error")
            service = AzureOpenAIService(
                client=mock_client.return_value,
                logger_instance=Mock(),
                settings_instance=mock_settings
            )
            result = service.generate_text("test prompt")
            
            assert result is None
    
    def test_generate_chat_response_success(self, mock_settings):
        """Test successful chat response generation."""
        with patch('services.openai_service.AzureOpenAI') as mock_client:
            # Mock chat completion response
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Chat response"))]
            mock_client.return_value.chat.completions.create.return_value = mock_response
            service = AzureOpenAIService(
                client=mock_client.return_value,
                logger_instance=Mock(),
                settings_instance=mock_settings
            )
            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ]
            result = service.generate_chat_response(messages)
            
            assert result == "Chat response"
            mock_client.return_value.chat.completions.create.assert_called_once()
    
    def test_generate_chat_response_failure(self, mock_settings):
        """Test failed chat response generation."""
        with patch('services.openai_service.AzureOpenAI') as mock_client:
            # Mock exception
            mock_client.return_value.chat.completions.create.side_effect = Exception("API error")
            service = AzureOpenAIService(
                client=mock_client.return_value,
                logger_instance=Mock(),
                settings_instance=mock_settings
            )
            messages = [{"role": "user", "content": "Hello"}]
            result = service.generate_chat_response(messages)
            
            assert result is None
    
    def test_analyze_sentiment_success(self, mock_settings):
        """Test successful sentiment analysis."""
        with patch('services.openai_service.AzureOpenAI') as mock_client:
            # Mock text generation response
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content='{"sentiment": "positive", "confidence": 0.8}'))]
            mock_client.return_value.chat.completions.create.return_value = mock_response
            service = AzureOpenAIService(
                client=mock_client.return_value,
                logger_instance=Mock(),
                settings_instance=mock_settings
            )
            result = service.analyze_sentiment("I love this!")
            
            assert result["sentiment"] == "positive"
            assert result["confidence"] == 0.8
    
    def test_analyze_sentiment_failure(self, mock_settings):
        """Test failed sentiment analysis."""
        with patch('services.openai_service.AzureOpenAI') as mock_client:
            # Mock exception
            mock_client.return_value.chat.completions.create.side_effect = Exception("API error")
            service = AzureOpenAIService(
                client=mock_client.return_value,
                logger_instance=Mock(),
                settings_instance=mock_settings
            )
            result = service.analyze_sentiment("test text")
            
            assert result is None
    
    def test_extract_keywords_success(self, mock_settings):
        """Test successful keyword extraction."""
        with patch('services.openai_service.AzureOpenAI') as mock_client:
            # Mock text generation response
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="keyword1, keyword2, keyword3"))]
            mock_client.return_value.chat.completions.create.return_value = mock_response
            service = AzureOpenAIService(
                client=mock_client.return_value,
                logger_instance=Mock(),
                settings_instance=mock_settings
            )
            result = service.extract_keywords("test text with keywords")
            
            assert result == ["keyword1", "keyword2", "keyword3"]
    
    def test_extract_keywords_failure(self, mock_settings):
        """Test failed keyword extraction."""
        with patch('services.openai_service.AzureOpenAI') as mock_client:
            # Mock exception
            mock_client.return_value.chat.completions.create.side_effect = Exception("API error")
            service = AzureOpenAIService(
                client=mock_client.return_value,
                logger_instance=Mock(),
                settings_instance=mock_settings
            )
            result = service.extract_keywords("test text")
            
            assert result is None 