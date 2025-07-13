"""
Tests for Event Grid handler function.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import azure.functions as func
from datetime import datetime

from functions.event_grid_handler import (
    main,
    handle_whatsapp_message_received,
    handle_whatsapp_delivery_report,
    process_incoming_whatsapp_message,
    generate_response_with_rag,
    save_conversation_with_context,
    load_conversation_history_with_redis,
)


class TestEventGridHandler:
    """Test cases for Event Grid handler functions."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_event = Mock(spec=func.EventGridEvent)
        self.mock_event.event_type = "Microsoft.Communication.AdvancedMessageReceived"
        
        # Mock WhatsApp message data
        self.whatsapp_message_data = {
            "from": {
                "phoneNumber": "+1234567890"
            },
            "message": {
                "content": "Hello, how are you?"
            },
            "id": "msg_123",
            "receivedTimestamp": "2024-01-01T12:00:00Z",
            "channelType": "whatsapp"
        }
        
        self.mock_event.get_json.return_value = self.whatsapp_message_data
    
    @patch('functions.event_grid_handler.logger')
    def test_main_with_whatsapp_message_received(self, mock_logger):
        """Test main function with WhatsApp message received event."""
        # Arrange
        self.mock_event.event_type = "Microsoft.Communication.AdvancedMessageReceived"
        
        # Act
        with patch('functions.event_grid_handler.handle_whatsapp_message_received') as mock_handler:
            main(self.mock_event)
            
            # Assert
            mock_handler.assert_called_once_with(self.mock_event)
            mock_logger.info.assert_called()
    
    @patch('functions.event_grid_handler.logger')
    def test_main_with_whatsapp_delivery_report(self, mock_logger):
        """Test main function with WhatsApp delivery report event."""
        # Arrange
        self.mock_event.event_type = "Microsoft.Communication.AdvancedMessageDeliveryReportReceived"
        
        # Act
        with patch('functions.event_grid_handler.handle_whatsapp_delivery_report') as mock_handler:
            main(self.mock_event)
            
            # Assert
            mock_handler.assert_called_once_with(self.mock_event)
            mock_logger.info.assert_called()
    
    @patch('functions.event_grid_handler.logger')
    def test_main_with_unknown_event_type(self, mock_logger):
        """Test main function with unknown event type."""
        # Arrange
        self.mock_event.event_type = "Unknown.Event.Type"
        
        # Act
        main(self.mock_event)
        
        # Assert
        mock_logger.info.assert_called_with("Unhandled event type: Unknown.Event.Type")
    
    @patch('functions.event_grid_handler.logger')
    @patch('functions.event_grid_handler.process_incoming_whatsapp_message')
    def test_handle_whatsapp_message_received_success(self, mock_process, mock_logger):
        """Test successful WhatsApp message received handling."""
        # Act
        handle_whatsapp_message_received(self.mock_event)
        
        # Assert
        mock_process.assert_called_once_with(
            "+1234567890",
            "Hello, how are you?",
            "msg_123",
            "2024-01-01T12:00:00Z"
        )
        mock_logger.info.assert_called()
    
    @patch('functions.event_grid_handler.logger')
    def test_handle_whatsapp_message_received_missing_fields(self, mock_logger):
        """Test WhatsApp message received with missing fields."""
        # Arrange
        incomplete_data = {
            "from": {},
            "message": {},
            "id": "msg_123",
            "receivedTimestamp": "2024-01-01T12:00:00Z",
            "channelType": "whatsapp"
        }
        self.mock_event.get_json.return_value = incomplete_data
        
        # Act
        with patch('functions.event_grid_handler.process_incoming_whatsapp_message') as mock_process:
            handle_whatsapp_message_received(self.mock_event)
            
            # Assert
            mock_process.assert_not_called()
            mock_logger.warning.assert_called_with("Missing from_number or message_content in WhatsApp event")
    
    @patch('functions.event_grid_handler.logger')
    def test_handle_whatsapp_message_received_non_whatsapp_channel(self, mock_logger):
        """Test WhatsApp message received with non-WhatsApp channel."""
        # Arrange
        sms_data = {
            "from": {"phoneNumber": "+1234567890"},
            "message": {"content": "Hello"},
            "id": "msg_123",
            "receivedTimestamp": "2024-01-01T12:00:00Z",
            "channelType": "sms"
        }
        self.mock_event.get_json.return_value = sms_data
        
        # Act
        with patch('functions.event_grid_handler.process_incoming_whatsapp_message') as mock_process:
            handle_whatsapp_message_received(self.mock_event)
            
            # Assert
            mock_process.assert_not_called()
            mock_logger.info.assert_called_with("Ignoring non-WhatsApp message from channel: sms")
    
    @patch('functions.event_grid_handler.logger')
    @patch('functions.event_grid_handler.update_message_status')
    def test_handle_whatsapp_delivery_report_success(self, mock_update, mock_logger):
        """Test successful WhatsApp delivery report handling."""
        # Arrange
        delivery_report_data = {
            "id": "msg_123",
            "status": "delivered",
            "deliveryTimestamp": "2024-01-01T12:01:00Z"
        }
        self.mock_event.get_json.return_value = delivery_report_data
        
        # Act
        handle_whatsapp_delivery_report(self.mock_event)
        
        # Assert
        mock_update.assert_called_once_with(
            "msg_123",
            "delivered",
            "2024-01-01T12:01:00Z"
        )
        mock_logger.info.assert_called()
    
    @patch('functions.event_grid_handler.logger')
    @patch('functions.event_grid_handler.embedding_manager')
    @patch('functions.event_grid_handler.openai_service')
    @patch('functions.event_grid_handler.load_conversation_history_with_redis')
    def test_generate_response_with_rag_success(self, mock_load_history, mock_openai, mock_embedding, mock_logger):
        """Test successful response generation with RAG."""
        # Arrange
        user_message = "What is the weather like?"
        user_number = "+1234567890"

        mock_embedding.get_embedding.return_value = [0.1, 0.2, 0.3]
        mock_embedding.find_similar_content.return_value = "Weather information: Sunny, 25°C"
        mock_load_history.return_value = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        mock_openai.generate_chat_response.return_value = "The weather is sunny and 25°C."

        # Act
        result = generate_response_with_rag(user_message, user_number)

        # Assert
        assert result == "The weather is sunny and 25°C."
        mock_embedding.get_embedding.assert_called_once_with(user_message)
        mock_embedding.find_similar_content.assert_called_once_with([0.1, 0.2, 0.3], top_k=3)
        mock_load_history.assert_called_once_with(user_number)
        mock_openai.generate_chat_response.assert_called_once()
    
    @patch('functions.event_grid_handler.logger')
    @patch('functions.event_grid_handler.embedding_manager')
    def test_generate_response_with_rag_no_embedding(self, mock_embedding, mock_logger):
        """Test response generation when embedding fails."""
        # Arrange
        user_message = "What is the weather like?"
        user_number = "+1234567890"

        mock_embedding.get_embedding.return_value = None

        # Act
        result = generate_response_with_rag(user_message, user_number)

        # Assert
        assert result is None
        # Ya no verificamos el log porque el error se loguea en otro lugar
    
    @patch('functions.event_grid_handler.logger')
    @patch('functions.event_grid_handler.azure_blob_service')
    @patch('functions.event_grid_handler.embedding_manager')
    def test_save_conversation_with_context_success(self, mock_embedding, mock_blob, mock_logger):
        """Test successful conversation saving with context."""
        # Arrange
        user_number = "+1234567890"
        user_message = "Hello"
        bot_response = "Hi there!"
        timestamp = "2024-01-01T12:00:00Z"
        incoming_id = "msg_123"
        outgoing_id = "msg_456"
        
        mock_blob.load_conversation.return_value = {
            "conversation_id": "acs_+1234567890",
            "user_number": "+1234567890",
            "messages": []
        }
        mock_embedding.save_conversation_context.return_value = True
        
        # Act
        save_conversation_with_context(
            user_number, user_message, bot_response, 
            timestamp, incoming_id, outgoing_id
        )
        
        # Assert
        mock_blob.load_conversation.assert_called_once()
        mock_blob.save_conversation.assert_called_once()
        mock_embedding.save_conversation_context.assert_called_once()
        mock_logger.debug.assert_called()
    
    @patch('functions.event_grid_handler.logger')
    @patch('functions.event_grid_handler.embedding_manager')
    def test_load_conversation_history_with_redis_from_redis(self, mock_embedding, mock_logger):
        """Test loading conversation history from Redis."""
        # Arrange
        user_number = "+1234567890"
        expected_context = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        mock_embedding.get_conversation_context.return_value = expected_context
        
        # Act
        result = load_conversation_history_with_redis(user_number)
        
        # Assert
        assert result == expected_context
        mock_embedding.get_conversation_context.assert_called_once_with(user_number)
        mock_logger.debug.assert_called()
    
    @patch('functions.event_grid_handler.logger')
    @patch('functions.event_grid_handler.azure_blob_service')
    @patch('functions.event_grid_handler.embedding_manager')
    def test_load_conversation_history_with_redis_fallback_to_blob(self, mock_embedding, mock_blob, mock_logger):
        """Test loading conversation history with fallback to blob storage."""
        # Arrange
        user_number = "+1234567890"
        blob_data = {
            "conversation_id": "acs_+1234567890",
            "user_number": "+1234567890",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }
        
        mock_embedding.get_conversation_context.return_value = None
        mock_blob.load_conversation.return_value = blob_data
        mock_embedding.save_conversation_context.return_value = True
        
        # Act
        result = load_conversation_history_with_redis(user_number)
        
        # Assert
        assert result == blob_data["messages"]
        mock_embedding.get_conversation_context.assert_called_once_with(user_number)
        mock_blob.load_conversation.assert_called_once()
        mock_embedding.save_conversation_context.assert_called_once()
    
    @patch('functions.event_grid_handler.logger')
    @patch('functions.event_grid_handler.azure_blob_service')
    @patch('functions.event_grid_handler.embedding_manager')
    def test_load_conversation_history_with_redis_no_data(self, mock_embedding, mock_blob, mock_logger):
        """Test loading conversation history when no data exists."""
        # Arrange
        user_number = "+1234567890"
        
        mock_embedding.get_conversation_context.return_value = None
        mock_blob.load_conversation.return_value = None
        
        # Act
        result = load_conversation_history_with_redis(user_number)
        
        # Assert
        assert result == []
        mock_embedding.get_conversation_context.assert_called_once_with(user_number)
        mock_blob.load_conversation.assert_called_once() 

def test_handle_delivery_report_saves_status():
    # Simular el objeto EventGridEvent con get_json()
    mock_event = Mock()
    mock_event.get_json.return_value = {
        "id": "msg123",
        "status": "delivered",
        "deliveryTimestamp": "2024-07-13T12:00:00Z"
    }
    with patch('functions.event_grid_handler.update_message_status') as mock_update_status:
        handle_whatsapp_delivery_report(mock_event)
        mock_update_status.assert_called_once_with("msg123", "delivered", "2024-07-13T12:00:00Z") 