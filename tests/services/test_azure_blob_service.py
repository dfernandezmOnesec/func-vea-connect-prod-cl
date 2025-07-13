"""
Unit tests for Azure Blob Service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from services.azure_blob_service import AzureBlobService


class TestAzureBlobService:
    """Test cases for Azure Blob Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('services.azure_blob_service.BlobServiceClient') as mock_blob_service:
            with patch('services.azure_blob_service.settings') as mock_settings:
                mock_settings.azure_storage_connection_string = "test_connection_string"
                mock_settings.blob_container_name = "test_container"
                
                self.mock_container_client = Mock()
                self.mock_blob_service_client = Mock()
                self.mock_blob_service_client.get_container_client.return_value = self.mock_container_client
                mock_blob_service.from_connection_string.return_value = self.mock_blob_service_client
                
                self.service = AzureBlobService()
    
    def test_init_success(self):
        """Test successful initialization."""
        assert self.service.container_name == "test_container"
        assert self.service.container_client == self.mock_container_client
    
    @patch('services.azure_blob_service.BlobServiceClient')
    def test_init_container_creation(self, mock_blob_service):
        """Test initialization with container creation."""
        with patch('services.azure_blob_service.settings') as mock_settings:
            mock_settings.azure_storage_connection_string = "test_connection_string"
            mock_settings.blob_container_name = "test_container"
            
            mock_container_client = Mock()
            mock_blob_service_client = Mock()
            mock_blob_service_client.get_container_client.return_value = mock_container_client
            mock_blob_service.from_connection_string.return_value = mock_blob_service_client
            
            # Simulate container doesn't exist
            mock_container_client.get_container_properties.side_effect = Exception("Container not found")
            
            service = AzureBlobService()
            
            mock_blob_service_client.create_container.assert_called_once_with("test_container")
    
    def test_upload_text_success(self):
        """Test successful text upload."""
        blob_name = "test.txt"
        text_content = "Hello, World!"
        metadata = {"key": "value"}
        
        mock_blob_client = Mock()
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.upload_text(blob_name, text_content, metadata)
        
        assert result is True
        mock_blob_client.upload_blob.assert_called_once_with(text_content, overwrite=True, metadata=metadata)
    
    def test_upload_text_failure(self):
        """Test text upload failure."""
        blob_name = "test.txt"
        text_content = "Hello, World!"
        
        mock_blob_client = Mock()
        mock_blob_client.upload_blob.side_effect = Exception("Upload failed")
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.upload_text(blob_name, text_content)
        
        assert result is False
    
    def test_upload_json_success(self):
        """Test successful JSON upload."""
        blob_name = "test.json"
        data = {"name": "test", "value": 123}
        metadata = {"type": "json"}
        
        with patch.object(self.service, 'upload_text') as mock_upload_text:
            mock_upload_text.return_value = True
            
            result = self.service.upload_json(blob_name, data, metadata)
            
            assert result is True
            mock_upload_text.assert_called_once()
            call_args = mock_upload_text.call_args
            assert call_args[0][0] == blob_name
            assert call_args[0][2] == metadata
    
    def test_upload_json_failure(self):
        """Test JSON upload failure."""
        blob_name = "test.json"
        data = {"name": "test"}
        
        with patch.object(self.service, 'upload_text') as mock_upload_text:
            mock_upload_text.return_value = False
            
            result = self.service.upload_json(blob_name, data)
            
            assert result is False
    
    def test_download_text_success(self):
        """Test successful text download."""
        blob_name = "test.txt"
        expected_text = "Hello, World!"
        
        mock_blob_client = Mock()
        mock_download_stream = Mock()
        mock_download_stream.readall.return_value = expected_text.encode('utf-8')
        mock_blob_client.download_blob.return_value = mock_download_stream
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.download_text(blob_name)
        
        assert result == expected_text
    
    def test_download_text_failure(self):
        """Test text download failure."""
        blob_name = "test.txt"
        
        mock_blob_client = Mock()
        mock_blob_client.download_blob.side_effect = Exception("Download failed")
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.download_text(blob_name)
        
        assert result is None
    
    def test_download_json_success(self):
        """Test successful JSON download."""
        blob_name = "test.json"
        expected_data = {"name": "test", "value": 123}
        
        with patch.object(self.service, 'download_text') as mock_download_text:
            mock_download_text.return_value = '{"name": "test", "value": 123}'
            
            result = self.service.download_json(blob_name)
            
            assert result == expected_data
    
    def test_download_json_failure(self):
        """Test JSON download failure."""
        blob_name = "test.json"
        
        with patch.object(self.service, 'download_text') as mock_download_text:
            mock_download_text.return_value = None
            
            result = self.service.download_json(blob_name)
            
            assert result is None
    
    def test_delete_blob_success(self):
        """Test successful blob deletion."""
        blob_name = "test.txt"
        
        mock_blob_client = Mock()
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.delete_blob(blob_name)
        
        assert result is True
        mock_blob_client.delete_blob.assert_called_once()
    
    def test_delete_blob_failure(self):
        """Test blob deletion failure."""
        blob_name = "test.txt"
        
        mock_blob_client = Mock()
        mock_blob_client.delete_blob.side_effect = Exception("Delete failed")
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.delete_blob(blob_name)
        
        assert result is False
    
    def test_list_blobs_success(self):
        """Test successful blob listing."""
        expected_blobs = ["file1.txt", "file2.json", "folder/file3.txt"]
        
        mock_blob_list = []
        for blob_name in expected_blobs:
            mock_blob = Mock()
            mock_blob.name = blob_name
            mock_blob_list.append(mock_blob)
        
        self.mock_container_client.list_blobs.return_value = mock_blob_list
        
        result = self.service.list_blobs()
        
        assert result == expected_blobs
    
    def test_list_blobs_with_filter(self):
        """Test blob listing with name filter."""
        expected_blobs = ["folder/file1.txt", "folder/file2.json"]
        
        mock_blob_list = []
        for blob_name in expected_blobs:
            mock_blob = Mock()
            mock_blob.name = blob_name
            mock_blob_list.append(mock_blob)
        
        self.mock_container_client.list_blobs.return_value = mock_blob_list
        
        result = self.service.list_blobs(name_starts_with="folder/")
        
        assert result == expected_blobs
        self.mock_container_client.list_blobs.assert_called_once_with(name_starts_with="folder/")
    
    def test_list_blobs_failure(self):
        """Test blob listing failure."""
        self.mock_container_client.list_blobs.side_effect = Exception("List failed")
        
        result = self.service.list_blobs()
        
        assert result == []
    
    def test_blob_exists_true(self):
        """Test blob exists check when blob exists."""
        blob_name = "test.txt"
        
        mock_blob_client = Mock()
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.blob_exists(blob_name)
        
        assert result is True
        mock_blob_client.get_blob_properties.assert_called_once()
    
    def test_blob_exists_false(self):
        """Test blob exists check when blob doesn't exist."""
        blob_name = "test.txt"
        
        mock_blob_client = Mock()
        mock_blob_client.get_blob_properties.side_effect = Exception("Blob not found")
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.blob_exists(blob_name)
        
        assert result is False
    
    def test_get_blob_metadata_success(self):
        """Test successful metadata retrieval."""
        blob_name = "test.txt"
        expected_metadata = {"key1": "value1", "key2": "value2"}
        
        mock_blob_client = Mock()
        mock_properties = Mock()
        mock_properties.metadata = expected_metadata
        mock_blob_client.get_blob_properties.return_value = mock_properties
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.get_blob_metadata(blob_name)
        
        assert result == expected_metadata
    
    def test_get_blob_metadata_failure(self):
        """Test metadata retrieval failure."""
        blob_name = "test.txt"
        
        mock_blob_client = Mock()
        mock_blob_client.get_blob_properties.side_effect = Exception("Metadata retrieval failed")
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.get_blob_metadata(blob_name)
        
        assert result is None
    
    def test_save_conversation_success(self):
        """Test successful conversation saving."""
        conversation_id = "conv_123"
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        with patch.object(self.service, 'upload_json') as mock_upload_json:
            mock_upload_json.return_value = True
            
            result = self.service.save_conversation(conversation_id, messages)
            
            assert result is True
            mock_upload_json.assert_called_once()
            call_args = mock_upload_json.call_args
            assert "conversations/conv_123.json" in call_args[0][0]
            assert call_args[0][1]["conversation_id"] == conversation_id
            assert call_args[0][1]["messages"] == messages
    
    def test_save_conversation_failure(self):
        """Test conversation saving failure."""
        conversation_id = "conv_123"
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch.object(self.service, 'upload_json') as mock_upload_json:
            mock_upload_json.return_value = False
            
            result = self.service.save_conversation(conversation_id, messages)
            
            assert result is False
    
    def test_load_conversation_success(self):
        """Test successful conversation loading."""
        conversation_id = "conv_123"
        expected_data = {
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        with patch.object(self.service, 'download_json') as mock_download_json:
            mock_download_json.return_value = expected_data
            
            result = self.service.load_conversation(conversation_id)
            
            assert result == expected_data
            mock_download_json.assert_called_once_with("conversations/conv_123.json")
    
    def test_load_conversation_failure(self):
        """Test conversation loading failure."""
        conversation_id = "conv_123"
        
        with patch.object(self.service, 'download_json') as mock_download_json:
            mock_download_json.return_value = None
            
            result = self.service.load_conversation(conversation_id)
            
            assert result is None
    
    def test_download_file_success(self):
        """Test successful file download."""
        blob_name = "test.txt"
        local_file_path = "/tmp/test.txt"
        
        mock_blob_client = Mock()
        mock_download_stream = Mock()
        mock_download_stream.readall.return_value = b"Hello, World!"
        mock_blob_client.download_blob.return_value = mock_download_stream
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = self.service.download_file(blob_name, local_file_path)
            
            assert result is True
            mock_file.write.assert_called_once_with(b"Hello, World!")
    
    def test_download_file_failure(self):
        """Test file download failure."""
        blob_name = "test.txt"
        local_file_path = "/tmp/test.txt"
        
        mock_blob_client = Mock()
        mock_blob_client.download_blob.side_effect = Exception("Download failed")
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.download_file(blob_name, local_file_path)
        
        assert result is False
    
    def test_update_blob_metadata_success(self):
        """Test successful metadata update."""
        blob_name = "test.txt"
        metadata = {"key1": "value1", "key2": "value2"}
        
        mock_blob_client = Mock()
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.update_blob_metadata(blob_name, metadata)
        
        assert result is True
        mock_blob_client.set_blob_metadata.assert_called_once_with(metadata)
    
    def test_update_blob_metadata_failure(self):
        """Test metadata update failure."""
        blob_name = "test.txt"
        metadata = {"key1": "value1"}
        
        mock_blob_client = Mock()
        mock_blob_client.set_blob_metadata.side_effect = Exception("Update failed")
        self.mock_container_client.get_blob_client.return_value = mock_blob_client
        
        result = self.service.update_blob_metadata(blob_name, metadata)
        
        assert result is False 