"""
Configuración específica para pruebas que evita la inicialización de servicios reales.
"""
import os
import sys
from unittest.mock import Mock, patch

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar variables de entorno para pruebas
os.environ["ENVIRONMENT"] = "test"
os.environ["AZURE_STORAGE_CONNECTION_STRING"] = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net"
os.environ["BLOB_ACCOUNT_NAME"] = "test"
os.environ["BLOB_CONTAINER_NAME"] = "test-container"
os.environ["ACS_CONNECTION_STRING"] = "endpoint=https://test.communication.azure.com;accesskey=test"
os.environ["ACS_PHONE_NUMBER"] = "+1234567890"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com/"
os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"] = "test-deployment"
os.environ["AZURE_OPENAI_CHAT_API_VERSION"] = "2023-05-15"
os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"] = "test-embeddings"
os.environ["AZURE_OPENAI_EMBEDDINGS_API_VERSION"] = "2023-05-15"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["REDIS_CONNECTION_STRING"] = "redis://localhost:6379"
os.environ["VISION_ENDPOINT"] = "https://test.cognitiveservices.azure.com/"
os.environ["VISION_KEY"] = "test-vision-key"
os.environ["QUEUE_NAME"] = "test-queue"

# Mock de servicios antes de importar los módulos principales
def setup_test_environment():
    """Configurar el entorno de prueba con mocks."""
    
    # Mock de Azure Blob Service
    with patch('azure.storage.blob.BlobServiceClient') as mock_blob_client:
        mock_blob_service = Mock()
        mock_container_client = Mock()
        mock_blob_client.from_connection_string.return_value = mock_blob_service
        mock_blob_service.get_container_client.return_value = mock_container_client
        
        # Mock de métodos del container client
        mock_container_client.get_blob_client.return_value = Mock()
        mock_container_client.list_blobs.return_value = []
        mock_container_client.get_container_properties.return_value = Mock()
        
    # Mock de Azure OpenAI Service
    with patch('openai.AzureOpenAI') as mock_openai_client:
        mock_openai = Mock()
        mock_openai_client.return_value = mock_openai
        
        # Mock de métodos de OpenAI
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock()]
        mock_chat_completion.choices[0].message.content = "Test response"
        mock_openai.chat.completions.create.return_value = mock_chat_completion
        
        mock_embedding = Mock()
        mock_embedding.data = [Mock()]
        mock_embedding.data[0].embedding = [0.1, 0.2, 0.3]
        mock_openai.embeddings.create.return_value = mock_embedding
    
    # Mock de Redis
    with patch('redis.Redis') as mock_redis_client:
        mock_redis = Mock()
        mock_redis_client.from_url.return_value = mock_redis
        
    # El patch para azure.communication.sms.CommunicationServiceClient se elimina porque no existe el módulo
    # with patch('azure.communication.sms.CommunicationServiceClient') as mock_acs_client:
    #     mock_acs = Mock()
    #     mock_acs_client.from_connection_string.return_value = mock_acs

# Configurar el entorno antes de importar cualquier módulo
setup_test_environment() 