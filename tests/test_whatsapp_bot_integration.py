"""
Integration tests for WhatsApp Bot Function - Complete Flow Testing.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

# Import the main function and helper functions
from whatsapp_bot_function import main, _extract_message_details, _generate_ai_response


class TestWhatsAppBotIntegration:
    """Integration tests for WhatsApp Bot Function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_user_number = "+521234567890"
        self.test_conversation_id = f"whatsapp_{self.test_user_number}"
        
        # Mock documents data for testing
        self.complete_donativo = {
            "id": "donativo_001",
            "tipo": "donativo",
            "nombre_donante": "Juan Pérez",
            "monto": "1000.00",
            "fecha": "2024-01-15",
            "concepto": "Donación para eventos",
            "metodo_pago": "Transferencia bancaria",
            "estado": "Confirmado"
        }
        
        self.incomplete_donativo = {
            "id": "donativo_002",
            "tipo": "donativo",
            "nombre_donante": "María García",
            "monto": "",  # Campo vacío
            "fecha": "2024-01-16",
            "concepto": "Donación general",
            "metodo_pago": "",
            "estado": "Pendiente"
        }
        
        self.complete_evento = {
            "id": "evento_001",
            "tipo": "evento",
            "nombre": "Gala de Beneficencia 2024",
            "fecha": "2024-02-15",
            "hora": "19:00",
            "lugar": "Centro de Convenciones",
            "descripcion": "Evento anual de recaudación de fondos",
            "organizador": "Comité de Eventos VEA",
            "capacidad": "500 personas"
        }
        
        self.complete_contacto = {
            "id": "contacto_001",
            "tipo": "contacto",
            "nombre": "Carlos López",
            "email": "carlos.lopez@email.com",
            "telefono": "+525512345678",
            "organizacion": "Empresa ABC",
            "cargo": "Director de Marketing",
            "interes": "Patrocinio de eventos"
        }
    
    def create_mock_event(self, message: str) -> Mock:
        """Create a mock Event Grid event with the given message."""
        mock_event = Mock()
        mock_event.event_type = "Microsoft.Communication.AdvancedMessageReceived"
        mock_event.get_json.return_value = {
            "data": {
                "from": self.test_user_number,
                "message": message,
                "receivedTimestamp": datetime.utcnow().isoformat()
            }
        }
        return mock_event
    
    @patch('whatsapp_bot_function.azure_blob_service')
    @patch('whatsapp_bot_function.acs_service')
    @patch('whatsapp_bot_function.openai_service')
    def test_bot_response_to_donativo_keyword(self, mock_openai, mock_acs, mock_blob):
        """Test bot response when user asks about 'donativo'."""
        # Arrange
        mock_event = self.create_mock_event("donativo")
        
        # Mock OpenAI to return a template response
        mock_openai.generate_chat_response_with_context.return_value = (
            "Aquí tienes la información del donativo:\n"
            "Donante: Juan Pérez\n"
            "Monto: $1,000.00\n"
            "Fecha: 15/01/2024\n"
            "Concepto: Donación para eventos"
        )
        
        # Mock ACS service
        mock_acs.send_whatsapp_text_message.return_value = "msg_12345"
        
        # Mock blob service
        mock_blob.load_conversation.return_value = {"messages": []}
        mock_blob.save_conversation.return_value = True
        
        # Act
        main(mock_event)
        
        # Assert
        mock_openai.generate_chat_response_with_context.assert_called_once()
        mock_acs.send_whatsapp_text_message.assert_called_once()
        
        # Verify the response contains donativo information
        call_args = mock_openai.generate_chat_response_with_context.call_args
        assert "donativo" in call_args[1]["message"].lower()
    
    @patch('whatsapp_bot_function.azure_blob_service')
    @patch('whatsapp_bot_function.acs_service')
    @patch('whatsapp_bot_function.openai_service')
    def test_bot_response_to_donativo_keyword_with_incomplete_data(self, mock_openai, mock_acs, mock_blob):
        """Test bot response when user asks about 'donativo' with incomplete data."""
        # Arrange
        mock_event = self.create_mock_event("donativo")
        
        # Mock OpenAI to return fallback response
        mock_openai.generate_chat_response_with_context.return_value = (
            "No encontré la información solicitada para tu consulta."
        )
        
        # Mock ACS service
        mock_acs.send_whatsapp_text_message.return_value = "msg_12345"
        
        # Mock blob service
        mock_blob.load_conversation.return_value = {"messages": []}
        mock_blob.save_conversation.return_value = True
        
        # Act
        main(mock_event)
        
        # Assert
        mock_openai.generate_chat_response_with_context.assert_called_once()
        mock_acs.send_whatsapp_text_message.assert_called_once()
        
        # Verify the response is the fallback message
        response = mock_openai.generate_chat_response_with_context.return_value
        assert "No encontré la información" in response
    
    @patch('whatsapp_bot_function.azure_blob_service')
    @patch('whatsapp_bot_function.acs_service')
    @patch('whatsapp_bot_function.openai_service')
    def test_bot_response_to_evento_keyword(self, mock_openai, mock_acs, mock_blob):
        """Test bot response when user asks about 'evento'."""
        # Arrange
        mock_event = self.create_mock_event("evento")
        
        # Mock OpenAI to return a template response
        mock_openai.generate_chat_response_with_context.return_value = (
            "Aquí tienes la información del evento:\n"
            "Nombre: Gala de Beneficencia 2024\n"
            "Fecha: 15/02/2024\n"
            "Hora: 19:00\n"
            "Lugar: Centro de Convenciones"
        )
        
        # Mock ACS service
        mock_acs.send_whatsapp_text_message.return_value = "msg_12345"
        
        # Mock blob service
        mock_blob.load_conversation.return_value = {"messages": []}
        mock_blob.save_conversation.return_value = True
        
        # Act
        main(mock_event)
        
        # Assert
        mock_openai.generate_chat_response_with_context.assert_called_once()
        mock_acs.send_whatsapp_text_message.assert_called_once()
    
    @patch('whatsapp_bot_function.azure_blob_service')
    @patch('whatsapp_bot_function.acs_service')
    @patch('whatsapp_bot_function.openai_service')
    def test_bot_response_to_contacto_keyword(self, mock_openai, mock_acs, mock_blob):
        """Test bot response when user asks about 'contacto'."""
        # Arrange
        mock_event = self.create_mock_event("contacto")
        
        # Mock OpenAI to return a template response
        mock_openai.generate_chat_response_with_context.return_value = (
            "Aquí tienes la información de contacto:\n"
            "Nombre: Carlos López\n"
            "Email: carlos.lopez@email.com\n"
            "Teléfono: +52 55 1234 5678\n"
            "Organización: Empresa ABC"
        )
        
        # Mock ACS service
        mock_acs.send_whatsapp_text_message.return_value = "msg_12345"
        
        # Mock blob service
        mock_blob.load_conversation.return_value = {"messages": []}
        mock_blob.save_conversation.return_value = True
        
        # Act
        main(mock_event)
        
        # Assert
        mock_openai.generate_chat_response_with_context.assert_called_once()
        mock_acs.send_whatsapp_text_message.assert_called_once()
    
    @patch('whatsapp_bot_function.azure_blob_service')
    @patch('whatsapp_bot_function.acs_service')
    @patch('whatsapp_bot_function.openai_service')
    def test_bot_response_to_generic_message(self, mock_openai, mock_acs, mock_blob):
        """Test bot response to generic message like 'Hola'."""
        # Arrange
        mock_event = self.create_mock_event("Hola")
        
        # Mock OpenAI to return welcome message
        mock_openai.generate_chat_response_with_context.return_value = (
            "¡Hola! Soy el asistente virtual de VEA Connect. "
            "Puedo ayudarte con información sobre donativos, eventos y contactos. "
            "¿En qué puedo asistirte hoy?"
        )
        
        # Mock ACS service
        mock_acs.send_whatsapp_text_message.return_value = "msg_12345"
        
        # Mock blob service
        mock_blob.load_conversation.return_value = {"messages": []}
        mock_blob.save_conversation.return_value = True
        
        # Act
        main(mock_event)
        
        # Assert
        mock_openai.generate_chat_response_with_context.assert_called_once()
        mock_acs.send_whatsapp_text_message.assert_called_once()
        
        # Verify the response is a welcome message
        response = mock_openai.generate_chat_response_with_context.return_value
        assert "VEA Connect" in response
        assert "asistente virtual" in response
    
    @patch('whatsapp_bot_function.azure_blob_service')
    @patch('whatsapp_bot_function.acs_service')
    @patch('whatsapp_bot_function.openai_service')
    def test_bot_response_to_unknown_keyword(self, mock_openai, mock_acs, mock_blob):
        """Test bot response to unknown keyword."""
        # Arrange
        mock_event = self.create_mock_event("xyz123")
        
        # Mock OpenAI to return fallback message
        mock_openai.generate_chat_response_with_context.return_value = (
            "No encontré la información solicitada para tu consulta. "
            "Puedo ayudarte con información sobre donativos, eventos y contactos."
        )
        
        # Mock ACS service
        mock_acs.send_whatsapp_text_message.return_value = "msg_12345"
        
        # Mock blob service
        mock_blob.load_conversation.return_value = {"messages": []}
        mock_blob.save_conversation.return_value = True
        
        # Act
        main(mock_event)
        
        # Assert
        mock_openai.generate_chat_response_with_context.assert_called_once()
        mock_acs.send_whatsapp_text_message.assert_called_once()
    
    @patch('whatsapp_bot_function.azure_blob_service')
    @patch('whatsapp_bot_function.acs_service')
    @patch('whatsapp_bot_function.openai_service')
    def test_conversation_context_persistence(self, mock_openai, mock_acs, mock_blob):
        """Test that conversation context is properly saved and loaded."""
        # Arrange
        mock_event = self.create_mock_event("Hola")
        
        # Mock existing conversation context
        existing_context = {
            "messages": [
                {"role": "user", "content": "Hola", "timestamp": "2024-01-01T10:00:00Z"},
                {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?", "timestamp": "2024-01-01T10:00:01Z"}
            ]
        }
        
        mock_openai.generate_chat_response_with_context.return_value = "Respuesta del bot"
        mock_acs.send_whatsapp_text_message.return_value = "msg_12345"
        mock_blob.load_conversation.return_value = existing_context
        mock_blob.save_conversation.return_value = True
        
        # Act
        main(mock_event)
        
        # Assert
        assert mock_blob.load_conversation.call_count >= 1
        first_call = mock_blob.load_conversation.call_args_list[0]
        assert first_call == ((self.test_conversation_id,), {})
        mock_blob.save_conversation.assert_called()
        
        # Verify conversation context is passed to OpenAI
        call_args = mock_openai.generate_chat_response_with_context.call_args
        assert call_args[1]["conversation_context"] == existing_context["messages"]
    
    @patch('whatsapp_bot_function.azure_blob_service')
    @patch('whatsapp_bot_function.acs_service')
    @patch('whatsapp_bot_function.openai_service')
    def test_error_handling_openai_failure(self, mock_openai, mock_acs, mock_blob):
        """Test error handling when OpenAI service fails."""
        # Arrange
        mock_event = self.create_mock_event("Hola")
        
        mock_openai.generate_chat_response_with_context.return_value = None  # Simulate failure
        mock_blob.load_conversation.return_value = {"messages": []}
        
        # Act & Assert
        main(mock_event)  # Should handle gracefully without raising exception
        
        # Verify that ACS service was not called due to OpenAI failure
        mock_acs.send_whatsapp_text_message.assert_not_called()
    
    @patch('whatsapp_bot_function.azure_blob_service')
    @patch('whatsapp_bot_function.acs_service')
    @patch('whatsapp_bot_function.openai_service')
    def test_error_handling_acs_failure(self, mock_openai, mock_acs, mock_blob):
        """Test error handling when ACS service fails."""
        # Arrange
        mock_event = self.create_mock_event("Hola")
        
        mock_openai.generate_chat_response_with_context.return_value = "Respuesta del bot"
        mock_acs.send_whatsapp_text_message.return_value = None  # Simulate failure
        mock_blob.load_conversation.return_value = {"messages": []}
        
        # Act & Assert
        main(mock_event)  # Should handle gracefully without raising exception
        
        # Verify that ACS service was called but failed
        mock_acs.send_whatsapp_text_message.assert_called_once()
    
    def test_extract_message_details_valid_event(self):
        """Test message details extraction from valid event."""
        # Arrange
        event_data = {
            "data": {
                "from": self.test_user_number,
                "message": "Test message",
                "receivedTimestamp": "2024-01-01T12:00:00Z"
            }
        }
        
        # Act
        result = _extract_message_details(event_data)
        
        # Assert
        assert result is not None
        assert result["from_number"] == self.test_user_number
        assert result["message"] == "Test message"
        assert result["timestamp"] == "2024-01-01T12:00:00Z"
    
    def test_extract_message_details_invalid_event(self):
        """Test message details extraction from invalid event."""
        # Arrange
        event_data = {
            "data": {
                "from": self.test_user_number
                # Missing message field
            }
        }
        
        # Act
        result = _extract_message_details(event_data)
        
        # Assert
        assert result is None
    
    @patch('whatsapp_bot_function.openai_service')
    def test_generate_ai_response_with_context(self, mock_openai):
        """Test AI response generation with conversation context."""
        # Arrange
        conversation_context = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?"}
        ]
        
        mock_openai.generate_chat_response_with_context.return_value = "Respuesta del bot"
        
        # Act
        result = _generate_ai_response(self.test_user_number, "¿Cómo estás?", conversation_context)
        
        # Assert
        assert result == "Respuesta del bot"
        mock_openai.generate_chat_response_with_context.assert_called_once_with(
            user_number=self.test_user_number,
            message="¿Cómo estás?",
            conversation_context=conversation_context
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 