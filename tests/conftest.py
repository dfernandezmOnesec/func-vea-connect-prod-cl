"""
Configuración de pytest para el proyecto.
"""
import pytest
from unittest.mock import Mock, patch

# Importar configuración de prueba
from . import test_config


@pytest.fixture(autouse=True)
def mock_azure_services():
    """Mock de servicios de Azure para pruebas."""
    with patch('services.azure_blob_service.BlobServiceClient') as mock_blob_client, \
         patch('services.openai_service.AzureOpenAI') as mock_openai_client:
        
        # Mock para Azure Blob Service
        mock_blob_service = Mock()
        mock_container_client = Mock()
        mock_blob_client.from_connection_string.return_value = mock_blob_service
        mock_blob_service.get_container_client.return_value = mock_container_client
        
        # Mock para Azure OpenAI Service
        mock_openai = Mock()
        mock_openai_client.return_value = mock_openai
        
        yield {
            'blob_service': mock_blob_service,
            'container_client': mock_container_client,
            'openai_client': mock_openai
        }


@pytest.fixture
def mock_redis():
    """Mock de Redis para pruebas."""
    with patch('services.redis_service.redis.Redis') as mock_redis_client:
        mock_redis = Mock()
        mock_redis_client.from_url.return_value = mock_redis
        yield mock_redis


@pytest.fixture
def mock_acs_service():
    """Mock de Azure Communication Services para pruebas."""
    with patch('services.acs_service.CommunicationServiceClient') as mock_acs_client:
        mock_acs = Mock()
        mock_acs_client.from_connection_string.return_value = mock_acs
        yield mock_acs


@pytest.fixture
def sample_sms_event():
    """Sample SMS event for tests."""
    return {
        "eventType": "Microsoft.Communication.SMSReceived",
        "eventTime": "2023-01-01T00:00:00Z",
        "data": {
            "from": "+1234567890",
            "message": "Hello, how are you?",
            "messageId": "test-message-id",
            "receivedTimestamp": "2023-01-01T00:00:00Z"
        }
    }


@pytest.fixture
def sample_delivery_report_event():
    """Sample delivery report event for tests."""
    return {
        "eventType": "Microsoft.Communication.SMSDeliveryReportReceived",
        "eventTime": "2023-01-01T00:00:00Z",
        "data": {
            "messageId": "test-message-id",
            "deliveryStatus": "delivered",
            "deliveryTimestamp": "2023-01-01T00:00:00Z"
        }
    } 