"""
Unit tests for Send Message Function.
"""
from unittest.mock import Mock, patch
import json
import azure.functions as func
from functions.send_message_function import main


class TestSendMessageFunction:
    """Test cases for Send Message Function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_request = Mock(spec=func.HttpRequest)
        self.mock_request.method = "POST"
    
    @patch('functions.send_message_function.acs_service')
    @patch('functions.send_message_function.settings')
    def test_main_successful_send(self, mock_settings, mock_acs_service):
        """Test successful message sending."""
        # Arrange
        request_body = {
            "to_number": "+1234567890",
            "message": "Hello, this is a test message"
        }
        self.mock_request.get_json.return_value = request_body
        
        mock_acs_service.send_whatsapp_message.return_value = "msg_12345"
        mock_acs_service.validate_phone_number.return_value = True
        mock_settings.max_message_length = 4096
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 200
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert response_body["success"] is True
        assert response_body["message_id"] == "msg_12345"
        mock_acs_service.send_whatsapp_message.assert_called_once_with("+1234567890", "Hello, this is a test message")
    
    @patch('functions.send_message_function.acs_service')
    @patch('functions.send_message_function.settings')
    def test_main_send_failure(self, mock_settings, mock_acs_service):
        """Test message sending failure."""
        # Arrange
        request_body = {
            "to_number": "+1234567890",
            "message": "Hello, this is a test message"
        }
        self.mock_request.get_json.return_value = request_body
        
        mock_acs_service.send_whatsapp_message.return_value = None
        mock_acs_service.validate_phone_number.return_value = True
        mock_settings.max_message_length = 4096
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 500
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert response_body["success"] is False
        assert "error" in response_body
    
    def test_main_invalid_method(self):
        """Test invalid HTTP method."""
        # Arrange
        self.mock_request.method = "GET"
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 405
        assert "Method not allowed" in response.get_body().decode('utf-8')
    
    def test_main_invalid_json(self):
        """Test invalid JSON in request body."""
        # Arrange
        self.mock_request.get_json.side_effect = ValueError("Invalid JSON")
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 500  # This will trigger the exception handler
    
    def test_main_missing_to_field(self):
        """Test missing 'to_number' field in request."""
        # Arrange
        request_body = {
            "message": "Hello, this is a test message"
        }
        self.mock_request.get_json.return_value = request_body
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 400
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert "Missing required parameters" in response_body
    
    def test_main_missing_message_field(self):
        """Test missing 'message' field in request."""
        # Arrange
        request_body = {
            "to_number": "+1234567890"
        }
        self.mock_request.get_json.return_value = request_body
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 400
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert "Missing required parameters" in response_body
    
    @patch('functions.send_message_function.acs_service')
    @patch('functions.send_message_function.settings')
    def test_main_invalid_phone_number(self, mock_settings, mock_acs_service):
        """Test invalid phone number format."""
        # Arrange
        request_body = {
            "to_number": "invalid_number",
            "message": "Hello, this is a test message"
        }
        self.mock_request.get_json.return_value = request_body
        
        mock_acs_service.validate_phone_number.return_value = False
        mock_settings.max_message_length = 4096
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 400
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert response_body["success"] is False
        assert "Invalid phone number format" in response_body["message"]
    
    @patch('functions.send_message_function.acs_service')
    @patch('functions.send_message_function.settings')
    def test_main_service_exception(self, mock_settings, mock_acs_service):
        """Test service exception handling."""
        # Arrange
        request_body = {
            "to_number": "+1234567890",
            "message": "Hello, this is a test message"
        }
        self.mock_request.get_json.return_value = request_body
        
        mock_acs_service.validate_phone_number.side_effect = Exception("Service error")
        mock_settings.max_message_length = 4096
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 500
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert response_body["success"] is False
    
    @patch('functions.send_message_function.acs_service')
    @patch('functions.send_message_function.settings')
    def test_main_bulk_message_success(self, mock_settings, mock_acs_service):
        """Test successful bulk message sending."""
        # Arrange
        request_body = {
            "messages": [
                {"to": "+1234567890", "message": "Message 1"},
                {"to": "+0987654321", "message": "Message 2"}
            ]
        }
        self.mock_request.get_json.return_value = request_body
        
        mock_acs_service.send_bulk_messages.return_value = {
            "successful": [
                {"to_number": "+1234567890", "message_id": "msg_1"},
                {"to_number": "+0987654321", "message_id": "msg_2"}
            ],
            "failed": [],
            "total": 2
        }
        mock_settings.max_message_length = 4096
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 200
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert response_body["success"] is True
        assert len(response_body["results"]["successful"]) == 2
        assert len(response_body["results"]["failed"]) == 0
        mock_acs_service.send_bulk_messages.assert_called_once()
    
    @patch('functions.send_message_function.acs_service')
    @patch('functions.send_message_function.settings')
    def test_main_bulk_message_partial_failure(self, mock_settings, mock_acs_service):
        """Test bulk message sending with partial failures."""
        # Arrange
        request_body = {
            "messages": [
                {"to": "+1234567890", "message": "Message 1"},
                {"to": "invalid", "message": "Message 2"}
            ]
        }
        self.mock_request.get_json.return_value = request_body
        
        mock_acs_service.send_bulk_messages.return_value = {
            "successful": [
                {"to_number": "+1234567890", "message_id": "msg_1"}
            ],
            "failed": [
                {"to_number": "invalid", "error": "Invalid phone number"}
            ],
            "total": 2
        }
        mock_settings.max_message_length = 4096
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 207  # Multi-status
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert response_body["success"] is True
        assert len(response_body["results"]["successful"]) == 1
        assert len(response_body["results"]["failed"]) == 1
    
    @patch('functions.send_message_function.acs_service')
    @patch('functions.send_message_function.settings')
    def test_main_bulk_message_all_failed(self, mock_settings, mock_acs_service):
        """Test bulk message sending with all failures."""
        # Arrange
        request_body = {
            "messages": [
                {"to": "invalid1", "message": "Message 1"},
                {"to": "invalid2", "message": "Message 2"}
            ]
        }
        self.mock_request.get_json.return_value = request_body
        
        mock_acs_service.send_bulk_messages.return_value = {
            "successful": [],
            "failed": [
                {"to_number": "invalid1", "error": "Invalid phone number"},
                {"to_number": "invalid2", "error": "Invalid phone number"}
            ],
            "total": 2
        }
        mock_settings.max_message_length = 4096
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 500
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert response_body["success"] is False
        assert len(response_body["results"]["successful"]) == 0
        assert len(response_body["results"]["failed"]) == 2
    
    def test_main_missing_messages_field_bulk(self):
        """Test missing 'messages' field in bulk request."""
        # Arrange
        request_body = {
            "to": "+1234567890",
            "message": "Hello"
        }
        self.mock_request.get_json.return_value = request_body
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 400
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert response_body["error"] == "Missing required field: message"
    
    def test_main_empty_messages_array(self):
        """Test empty messages array in bulk request."""
        # Arrange
        request_body = {
            "messages": []
        }
        self.mock_request.get_json.return_value = request_body
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 400
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert response_body["error"] == "Messages array cannot be empty"
    
    @patch('functions.send_message_function.acs_service')
    @patch('functions.send_message_function.settings')
    def test_main_bulk_message_validation_errors(self, mock_settings, mock_acs_service):
        """Test bulk message validation errors."""
        # Arrange
        request_body = {
            "messages": [
                {"to": "+1234567890", "message": "A" * 5000},  # Too long
                {"to": "invalid", "message": ""}  # Empty message
            ]
        }
        self.mock_request.get_json.return_value = request_body
        
        mock_settings.max_message_length = 4096
        
        # Act
        response = main(self.mock_request)
        
        # Assert
        assert response.status_code == 400
        response_body = json.loads(response.get_body().decode('utf-8'))
        assert "validation_errors" in response_body
        assert len(response_body["validation_errors"]) == 2 