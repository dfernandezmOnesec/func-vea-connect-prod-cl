"""
Tests for ACS service.
"""
from unittest.mock import patch, Mock
from services.acs_service import ACSService


class TestACSService:
    """Tests for ACSService."""
    
    def test_init(self, mock_settings):
        """Test initialization."""
        service = ACSService()
        assert service.phone_number == "+1234567890"
        assert service.endpoint == "https://test-acs.communication.azure.com"
        assert service.api_key == "test-acs-key"
    
    @patch('services.acs_service.httpx.post')
    def test_send_whatsapp_message_success(self, mock_post, mock_settings):
        """Test successful WhatsApp message sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"messageId": "test-message-id"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        service = ACSService()
        result = service.send_whatsapp_message("+1234567890", "Hello")
        
        assert result == "test-message-id"
        mock_post.assert_called_once()
    
    @patch('services.acs_service.httpx.post')
    def test_send_whatsapp_message_failure(self, mock_post, mock_settings):
        """Test failed WhatsApp message sending."""
        # Mock HTTP error
        import httpx
        mock_post.side_effect = httpx.HTTPStatusError("HTTP Error", request=Mock(), response=Mock())
        
        service = ACSService()
        result = service.send_whatsapp_message("+1234567890", "Hello")
        
        assert result is None
    
    def test_validate_phone_number_valid(self, mock_settings):
        """Test valid phone number validation."""
        service = ACSService()
        
        assert service.validate_phone_number("+1234567890") is True
        assert service.validate_phone_number("1234567890") is True
        assert service.validate_phone_number("(123) 456-7890") is True
    
    def test_validate_phone_number_invalid(self, mock_settings):
        """Test invalid phone number validation."""
        service = ACSService()
        
        assert service.validate_phone_number("") is False
        assert service.validate_phone_number("123") is False
        assert service.validate_phone_number("invalid") is False
    
    def test_get_message_status(self, mock_settings):
        """Test getting message status."""
        service = ACSService()
        result = service.get_message_status("test-message-id")
        
        assert result is not None
        assert result["message_id"] == "test-message-id"
        assert result["status"] == "unknown"
        assert "Event Grid" in result["note"] 

def test_get_message_status_found():
    with patch('services.acs_service.redis_service') as mock_redis:
        mock_redis.get.return_value = "delivered"
        service = ACSService()
        result = service.get_message_status("msg123")
        assert result["message_id"] == "msg123"
        assert result["status"] == "delivered"

def test_get_message_status_not_found():
    with patch('services.acs_service.redis_service') as mock_redis:
        mock_redis.get.return_value = None
        service = ACSService()
        result = service.get_message_status("msg123")
        assert result["message_id"] == "msg123"
        assert result["status"] == "unknown"
        assert "note" in result 