"""
Tests for delete_document_function.
"""
import json
import pytest
from unittest.mock import Mock, patch
import azure.functions as func

from delete_document_function import main, delete_document_completely, get_document_info


class TestDeleteDocumentFunction:
    """Test cases for delete document function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_request = Mock(spec=func.HttpRequest)
        self.mock_request.method = "DELETE"
    
    def test_delete_document_success(self):
        """Test successful document deletion."""
        # Mock request data
        request_data = {
            "document_id": "test_doc_123",
            "blob_name": "documents/test_document.pdf"
        }
        self.mock_request.get_json.return_value = request_data
        
        # Mock services
        with patch('delete_document_function.azure_blob_service') as mock_blob_service, \
             patch('delete_document_function.redis_service') as mock_redis_service, \
             patch('delete_document_function.embedding_manager') as mock_embedding_manager:
            
            # Configure mocks
            mock_blob_service.delete_blob.return_value = True
            mock_redis_service.delete.return_value = True
            mock_embedding_manager.delete_document_embeddings.return_value = True
            
            # Call function
            response = main(self.mock_request)
            
            # Assertions
            assert response.status_code == 200
            response_data = json.loads(response.get_body().decode())
            assert response_data["success"] is True
            assert response_data["document_id"] == "test_doc_123"
            assert response_data["blob_name"] == "documents/test_document.pdf"
            
            # Verify service calls
            mock_blob_service.delete_blob.assert_called_once_with("documents/test_document.pdf")
            mock_embedding_manager.delete_document_embeddings.assert_called_once_with("test_doc_123")
    
    def test_delete_document_missing_parameters(self):
        """Test deletion with missing parameters."""
        # Mock empty request data
        self.mock_request.get_json.return_value = {}
        
        # Call function
        response = main(self.mock_request)
        
        # Assertions
        assert response.status_code == 400
        response_data = json.loads(response.get_body().decode())
        assert "Missing required parameters" in response_data["message"]
    
    def test_delete_document_invalid_method(self):
        """Test deletion with invalid HTTP method."""
        # Mock GET method
        self.mock_request.method = "GET"
        
        # Call function
        response = main(self.mock_request)
        
        # Assertions
        assert response.status_code == 405
        assert "Method not allowed" in response.get_body().decode()
    
    def test_delete_document_storage_failure(self):
        """Test deletion when storage deletion fails."""
        # Mock request data
        request_data = {
            "document_id": "test_doc_123",
            "blob_name": "documents/test_document.pdf"
        }
        self.mock_request.get_json.return_value = request_data
        
        # Mock services with storage failure
        with patch('delete_document_function.azure_blob_service') as mock_blob_service, \
             patch('delete_document_function.redis_service') as mock_redis_service, \
             patch('delete_document_function.embedding_manager') as mock_embedding_manager:
            
            # Configure mocks
            mock_blob_service.delete_blob.return_value = False
            mock_redis_service.delete.return_value = True
            mock_embedding_manager.delete_document_embeddings.return_value = True
            
            # Call function
            response = main(self.mock_request)
            
            # Assertions
            assert response.status_code == 500
            response_data = json.loads(response.get_body().decode())
            assert response_data["success"] is False
            assert "Failed to delete document completely" in response_data["message"]
    
    def test_delete_document_completely_success(self):
        """Test delete_document_completely function success."""
        with patch('delete_document_function.azure_blob_service') as mock_blob_service, \
             patch('delete_document_function.redis_service') as mock_redis_service, \
             patch('delete_document_function.embedding_manager') as mock_embedding_manager:
            
            # Configure mocks
            mock_blob_service.delete_blob.return_value = True
            mock_redis_service.delete.return_value = True
            mock_embedding_manager.delete_document_embeddings.return_value = True
            
            # Call function
            result = delete_document_completely("test_doc_123", "test_blob.pdf")
            
            # Assertions
            assert result["success"] is True
            assert result["details"]["storage_deleted"] is True
            assert result["details"]["redis_deleted"] is True
            assert result["details"]["embeddings_deleted"] is True
    
    def test_delete_document_completely_partial_failure(self):
        """Test delete_document_completely with partial failures."""
        with patch('delete_document_function.azure_blob_service') as mock_blob_service, \
             patch('delete_document_function.redis_service') as mock_redis_service, \
             patch('delete_document_function.embedding_manager') as mock_embedding_manager:
            
            # Configure mocks with mixed results
            mock_blob_service.delete_blob.return_value = True
            mock_redis_service.delete.return_value = False
            mock_embedding_manager.delete_document_embeddings.return_value = True
            
            # Call function
            result = delete_document_completely("test_doc_123", "test_blob.pdf")
            
            # Assertions
            assert result["success"] is False
            assert result["details"]["storage_deleted"] is True
            assert result["details"]["redis_deleted"] is False
            assert result["details"]["embeddings_deleted"] is True
            assert len(result["details"]["errors"]) > 0
    
    def test_get_document_info_success(self):
        """Test get_document_info function success."""
        with patch('delete_document_function.redis_service') as mock_redis_service:
            # Mock Redis response
            mock_metadata = {
                "blob_name": "documents/test_doc.pdf",
                "document_id": "test_doc_123",
                "chunks_count": 5
            }
            mock_redis_service.get_json.return_value = mock_metadata
            
            # Call function
            result = get_document_info("test_doc_123")
            
            # Assertions
            assert result is not None
            assert result["document_id"] == "test_doc_123"
            assert result["blob_name"] == "documents/test_doc.pdf"
            assert result["metadata"] == mock_metadata
    
    def test_get_document_info_not_found(self):
        """Test get_document_info when document not found."""
        with patch('delete_document_function.redis_service') as mock_redis_service:
            # Mock Redis response
            mock_redis_service.get_json.return_value = None
            
            # Call function
            result = get_document_info("nonexistent_doc")
            
            # Assertions
            assert result is not None
            assert result["document_id"] == "nonexistent_doc"
            assert result["blob_name"] is None
            assert result["metadata"] is None 