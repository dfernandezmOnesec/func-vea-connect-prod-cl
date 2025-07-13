"""
Unit tests for WhatsApp Bot Function.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from functions.whatsapp_bot_function import (
    main,
    _extract_message_details,
    _load_conversation_context,
    _generate_ai_response,
    _send_whatsapp_response,
    _save_conversation
)


class TestWhatsAppBotFunction:
    """Test cases for WhatsApp Bot Function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_event = Mock()
        self.mock_event.event_type = "Microsoft.Communication.SMSReceived"
        self.mock_event.get_json.return_value = {
            "data": {
                "from": "+1234567890",
                "message": "Hello, how are you?",
                "receivedTimestamp": "2024-01-01T12:00:00Z"
            }
        }
    
    @patch('functions.whatsapp_bot_function._extract_message_details')
    @patch('functions.whatsapp_bot_function._load_conversation_context')
    @patch('functions.whatsapp_bot_function._generate_ai_response')
    @patch('functions.whatsapp_bot_function._send_whatsapp_response')
    @patch('functions.whatsapp_bot_function._save_conversation')
    def test_main_successful_processing(self, mock_save, mock_send, mock_generate, mock_load, mock_extract):
        """Test successful message processing."""
        # Arrange
        mock_extract.return_value = {
            "from_number": "+1234567890",
            "message": "Hello, how are you?",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        mock_load.return_value = []
        mock_generate.return_value = "I'm doing well, thank you for asking!"
        mock_send.return_value = "msg_12345"
        
        # Act
        main(self.mock_event)
        
        # Assert
        mock_extract.assert_called_once()
        mock_load.assert_called_once_with("whatsapp_+1234567890")
        mock_generate.assert_called_once()
        mock_send.assert_called_once()
        mock_save.assert_called_once()
    
    def test_main_skip_non_sms_event(self):
        """Test that non-SMS events are skipped."""
        # Arrange
        self.mock_event.event_type = "Microsoft.Communication.SMSSent"
        
        # Act & Assert
        main(self.mock_event)  # Should not raise any exceptions
    
    @patch('functions.whatsapp_bot_function._extract_message_details')
    def test_main_extract_failure(self, mock_extract):
        """Test handling of message extraction failure."""
        # Arrange
        mock_extract.return_value = None
        
        # Act & Assert
        main(self.mock_event)  # Should handle gracefully
    
    def test_extract_message_details_success(self):
        """Test successful message details extraction."""
        # Arrange
        event_data = {
            "data": {
                "from": "+1234567890",
                "message": "Test message",
                "receivedTimestamp": "2024-01-01T12:00:00Z"
            }
        }
        
        # Act
        result = _extract_message_details(event_data)
        
        # Assert
        assert result is not None
        assert result["from_number"] == "+1234567890"
        assert result["message"] == "Test message"
        assert result["timestamp"] == "2024-01-01T12:00:00Z"
    
    def test_extract_message_details_missing_fields(self):
        """Test message details extraction with missing fields."""
        # Arrange
        event_data = {
            "data": {
                "from": "+1234567890"
                # Missing message field
            }
        }
        
        # Act
        result = _extract_message_details(event_data)
        
        # Assert
        assert result is None
    
    def test_extract_message_details_empty_data(self):
        """Test message details extraction with empty data."""
        # Arrange
        event_data = {}
        
        # Act
        result = _extract_message_details(event_data)
        
        # Assert
        assert result is None
    
    @patch('functions.whatsapp_bot_function.azure_blob_service')
    def test_load_conversation_context_existing(self, mock_blob_service):
        """Test loading existing conversation context."""
        # Arrange
        mock_blob_service.load_conversation.return_value = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }
        
        # Act
        result = _load_conversation_context("test_conversation")
        
        # Assert
        assert result is not None
        assert len(result) == 2
        mock_blob_service.load_conversation.assert_called_once_with("test_conversation")
    
    @patch('functions.whatsapp_bot_function.azure_blob_service')
    def test_load_conversation_context_not_found(self, mock_blob_service):
        """Test loading conversation context when not found."""
        # Arrange
        mock_blob_service.load_conversation.return_value = None
        
        # Act
        result = _load_conversation_context("test_conversation")
        
        # Assert
        assert result == []
    
    @patch('functions.whatsapp_bot_function.openai_service')
    def test_generate_ai_response_success(self, mock_openai_service):
        """Test successful AI response generation."""
        # Arrange
        mock_openai_service.generate_chat_response_with_context.return_value = "AI response"
        
        # Act
        result = _generate_ai_response("+1234567890", "Hello", [])
        
        # Assert
        assert result == "AI response"
        mock_openai_service.generate_chat_response_with_context.assert_called_once()
    
    @patch('functions.whatsapp_bot_function.openai_service')
    def test_generate_ai_response_failure(self, mock_openai_service):
        """Test AI response generation failure."""
        # Arrange
        mock_openai_service.generate_chat_response_with_context.return_value = None
        
        # Act
        result = _generate_ai_response("+1234567890", "Hello", [])
        
        # Assert
        assert result is None
    
    @patch('functions.whatsapp_bot_function.acs_service')
    def test_send_whatsapp_response_success(self, mock_acs_service):
        """Test successful WhatsApp message sending."""
        # Arrange
        mock_acs_service.send_whatsapp_message.return_value = "msg_12345"
        
        # Act
        result = _send_whatsapp_response("+1234567890", "Test message")
        
        # Assert
        assert result == "msg_12345"
        mock_acs_service.send_whatsapp_message.assert_called_once_with("+1234567890", "Test message")
    
    @patch('functions.whatsapp_bot_function.acs_service')
    def test_send_whatsapp_response_failure(self, mock_acs_service):
        """Test WhatsApp message sending failure."""
        # Arrange
        mock_acs_service.send_whatsapp_message.return_value = None
        
        # Act
        result = _send_whatsapp_response("+1234567890", "Test message")
        
        # Assert
        assert result is None
    
    @patch('functions.whatsapp_bot_function.azure_blob_service')
    def test_save_conversation_success(self, mock_blob_service):
        """Test successful conversation saving."""
        # Arrange
        mock_blob_service.load_conversation.return_value = {
            "messages": [{"role": "user", "content": "Previous message"}]
        }
        mock_blob_service.save_conversation.return_value = True
        
        # Act
        _save_conversation("test_conversation", "+1234567890", "User message", "AI response", "2024-01-01T12:00:00Z")
        
        # Assert
        mock_blob_service.save_conversation.assert_called_once()
        saved_messages = mock_blob_service.save_conversation.call_args[0][1]
        assert len(saved_messages) == 3  # Previous + user + AI
        assert saved_messages[-2]["role"] == "user"
        assert saved_messages[-1]["role"] == "assistant"
    
    @patch('functions.whatsapp_bot_function.azure_blob_service')
    def test_save_conversation_new_conversation(self, mock_blob_service):
        """Test saving conversation for new conversation."""
        # Arrange
        mock_blob_service.load_conversation.return_value = None
        mock_blob_service.save_conversation.return_value = True
        
        # Act
        _save_conversation("new_conversation", "+1234567890", "User message", "AI response", "2024-01-01T12:00:00Z")
        
        # Assert
        mock_blob_service.save_conversation.assert_called_once()
        saved_messages = mock_blob_service.save_conversation.call_args[0][1]
        assert len(saved_messages) == 2  # User + AI
        assert saved_messages[0]["role"] == "user"
        assert saved_messages[1]["role"] == "assistant"


if __name__ == "__main__":
    pytest.main([__file__]) 