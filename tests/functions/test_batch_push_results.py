"""
Unit tests for Batch Push Results Function.
"""
from unittest.mock import Mock, patch
import json
import azure.functions as func
from batch_push_results import main
import pytest


class TestBatchPushResultsFunction:
    """Test cases for Batch Push Results Function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_queue_message = Mock(spec=func.QueueMessage)
    
    @patch('batch_push_results.DocumentProcessor')
    def test_main_successful_processing(self, mock_document_processor_class):
        """Test successful document processing."""
        # Arrange
        queue_data = {
            "blob_name": "test_document.pdf",
            "blob_url": "https://example.com/document.pdf",
            "file_size": 1024,
            "content_type": "application/pdf"
        }
        self.mock_queue_message.get_body.return_value = json.dumps(queue_data).encode('utf-8')
        
        mock_processor_instance = Mock()
        mock_processor_instance.process_document_from_queue.return_value = True
        mock_document_processor_class.return_value = mock_processor_instance
        
        # Act
        main(self.mock_queue_message)
        
        # Assert
        mock_processor_instance.process_document_from_queue.assert_called_once_with(
            blob_name="test_document.pdf",
            blob_url="https://example.com/document.pdf",
            file_size=1024,
            content_type="application/pdf"
        )
    
    @patch('batch_push_results.DocumentProcessor')
    def test_main_processing_failure(self, mock_document_processor_class):
        """Test document processing failure."""
        # Arrange
        queue_data = {
            "blob_name": "test_document.pdf",
            "blob_url": "https://example.com/document.pdf",
            "file_size": 1024,
            "content_type": "application/pdf"
        }
        self.mock_queue_message.get_body.return_value = json.dumps(queue_data).encode('utf-8')
        
        mock_processor_instance = Mock()
        mock_processor_instance.process_document_from_queue.return_value = False
        mock_document_processor_class.return_value = mock_processor_instance
        
        # Act
        main(self.mock_queue_message)
        
        # Assert
        mock_processor_instance.process_document_from_queue.assert_called_once()
    
    def test_main_missing_blob_name(self):
        """Test missing blob_name in queue message."""
        # Arrange
        queue_data = {
            "blob_url": "https://example.com/document.pdf",
            "file_size": 1024
        }
        self.mock_queue_message.get_body.return_value = json.dumps(queue_data).encode('utf-8')
        
        # Act
        main(self.mock_queue_message)
        
        # Assert - should log error but not raise exception
    
    def test_main_invalid_json(self):
        """Test invalid JSON in queue message."""
        # Arrange
        self.mock_queue_message.get_body.return_value = b"invalid json"

        # Act & Assert
        with patch('batch_push_results.logger') as mock_logger:
            with pytest.raises(json.JSONDecodeError):
                main(self.mock_queue_message)
            
            # Verify that error was logged
            mock_logger.error.assert_called_with("Failed to parse queue message JSON: Expecting value: line 1 column 1 (char 0)")
    
    @patch('batch_push_results.DocumentProcessor')
    def test_main_processor_exception(self, mock_document_processor_class):
        """Test processor exception handling."""
        # Arrange
        queue_data = {
            "blob_name": "test_document.pdf",
            "blob_url": "https://example.com/document.pdf"
        }
        self.mock_queue_message.get_body.return_value = json.dumps(queue_data).encode('utf-8')

        mock_processor_instance = Mock()
        mock_processor_instance.process_document_from_queue.side_effect = Exception("Processing error")

        mock_document_processor_class.return_value = mock_processor_instance

        # Act & Assert
        with patch('batch_push_results.logger') as mock_logger:
            with pytest.raises(Exception):
                main(self.mock_queue_message)
            # Se puede verificar que el logger registró el error si se desea
            # mock_logger.error.assert_called() 