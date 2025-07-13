"""
Unit tests for Computer Vision Service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.computer_vision_service import ComputerVisionService


class TestComputerVisionService:
    """Test cases for Computer Vision Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('services.computer_vision_service.ComputerVisionClient') as mock_cv_client:
            with patch('services.computer_vision_service.settings') as mock_settings:
                mock_settings.vision_endpoint = "https://test-vision.cognitiveservices.azure.com/"
                mock_settings.vision_key = "test_key"
                
                self.mock_client = Mock()
                mock_cv_client.return_value = self.mock_client
                
                self.service = ComputerVisionService()
    
    def test_init_success(self):
        """Test successful initialization."""
        assert self.service.client == self.mock_client
    
    def test_analyze_image_success(self):
        """Test successful image analysis."""
        image_url = "https://example.com/image.jpg"
        expected_result = {
            "description": "A cat sitting on a chair",
            "tags": ["cat", "chair", "indoor"],
            "objects": [{"name": "cat", "confidence": 0.95}]
        }
        
        self.mock_client.analyze_image.return_value = Mock(
            description=Mock(captions=[Mock(text="A cat sitting on a chair")]),
            tags=[Mock(name="cat", confidence=0.95), Mock(name="chair", confidence=0.8)],
            objects=[Mock(object_property="cat", confidence=0.95)]
        )
        
        result = self.service.analyze_image(image_url)
        
        assert result is not None
        assert "description" in result
        assert "tags" in result
        self.mock_client.analyze_image.assert_called_once()
    
    def test_analyze_image_failure(self):
        """Test image analysis failure."""
        image_url = "https://example.com/image.jpg"
        
        self.mock_client.analyze_image.side_effect = Exception("Analysis failed")
        
        result = self.service.analyze_image(image_url)
        
        assert result is None
    
    def test_extract_text_success(self):
        """Test successful text extraction."""
        image_url = "https://example.com/document.jpg"
        expected_text = "Hello World\nThis is a test document"
        
        mock_result = Mock()
        mock_result.operation_location = "https://test-vision.cognitiveservices.azure.com/operations/123"
        self.mock_client.read.return_value = mock_result
        
        # Mock the polling result
        mock_polling_result = Mock()
        mock_polling_result.status = "succeeded"
        mock_polling_result.analyze_result = Mock()
        mock_polling_result.analyze_result.read_results = [
            Mock(lines=[Mock(text="Hello World"), Mock(text="This is a test document")])
        ]
        
        with patch.object(self.service, '_poll_read_operation') as mock_poll:
            mock_poll.return_value = mock_polling_result
            
            result = self.service.extract_text(image_url)
            
            assert result == expected_text
            self.mock_client.read.assert_called_once()
    
    def test_extract_text_failure(self):
        """Test text extraction failure."""
        image_url = "https://example.com/document.jpg"
        
        self.mock_client.read.side_effect = Exception("Text extraction failed")
        
        result = self.service.extract_text(image_url)
        
        assert result is None
    
    def test_extract_text_polling_failure(self):
        """Test text extraction with polling failure."""
        image_url = "https://example.com/document.jpg"
        
        mock_result = Mock()
        mock_result.operation_location = "https://test-vision.cognitiveservices.azure.com/operations/123"
        self.mock_client.read.return_value = mock_result
        
        with patch.object(self.service, '_poll_read_operation') as mock_poll:
            mock_poll.return_value = None
            
            result = self.service.extract_text(image_url)
            
            assert result is None
    
    def test_detect_objects_success(self):
        """Test successful object detection."""
        image_url = "https://example.com/image.jpg"
        expected_objects = [
            {"name": "person", "confidence": 0.95, "rectangle": {"x": 100, "y": 100, "w": 200, "h": 300}},
            {"name": "car", "confidence": 0.87, "rectangle": {"x": 300, "y": 200, "w": 150, "h": 100}}
        ]
        
        mock_result = Mock()
        mock_result.objects = [
            Mock(object_property="person", confidence=0.95, rectangle=Mock(x=100, y=100, w=200, h=300)),
            Mock(object_property="car", confidence=0.87, rectangle=Mock(x=300, y=200, w=150, h=100))
        ]
        self.mock_client.detect_objects.return_value = mock_result
        
        result = self.service.detect_objects(image_url)
        
        assert result == expected_objects
        self.mock_client.detect_objects.assert_called_once()
    
    def test_detect_objects_failure(self):
        """Test object detection failure."""
        image_url = "https://example.com/image.jpg"
        
        self.mock_client.detect_objects.side_effect = Exception("Object detection failed")
        
        result = self.service.detect_objects(image_url)
        
        assert result is None
    
    def test_analyze_face_success(self):
        """Test successful face analysis."""
        image_url = "https://example.com/face.jpg"
        expected_result = {
            "age": 25,
            "gender": "Female",
            "emotion": "Happy",
            "glasses": "NoGlasses"
        }
        
        mock_result = Mock()
        mock_result.faces = [
            Mock(
                age=25,
                gender="Female",
                emotion=Mock(anger=0.1, contempt=0.0, disgust=0.0, fear=0.0, happiness=0.9, neutral=0.0, sadness=0.0, surprise=0.0),
                glasses="NoGlasses"
            )
        ]
        self.mock_client.analyze_image.return_value = mock_result
        
        result = self.service.analyze_face(image_url)
        
        assert result == expected_result
        self.mock_client.analyze_image.assert_called_once()
    
    def test_analyze_face_no_faces(self):
        """Test face analysis with no faces detected."""
        image_url = "https://example.com/image.jpg"
        
        mock_result = Mock()
        mock_result.faces = []
        self.mock_client.analyze_image.return_value = mock_result
        
        result = self.service.analyze_face(image_url)
        
        assert result is None
    
    def test_analyze_face_failure(self):
        """Test face analysis failure."""
        image_url = "https://example.com/face.jpg"
        
        self.mock_client.analyze_image.side_effect = Exception("Face analysis failed")
        
        result = self.service.analyze_face(image_url)
        
        assert result is None
    
    def test_generate_thumbnail_success(self):
        """Test successful thumbnail generation."""
        image_url = "https://example.com/image.jpg"
        width = 100
        height = 100
        expected_thumbnail = b"thumbnail_data"
        
        self.mock_client.generate_thumbnail.return_value = expected_thumbnail
        
        result = self.service.generate_thumbnail(image_url, width, height)
        
        assert result == expected_thumbnail
        self.mock_client.generate_thumbnail.assert_called_once_with(width, height, image_url, smart_cropping=True)
    
    def test_generate_thumbnail_failure(self):
        """Test thumbnail generation failure."""
        image_url = "https://example.com/image.jpg"
        width = 100
        height = 100
        
        self.mock_client.generate_thumbnail.side_effect = Exception("Thumbnail generation failed")
        
        result = self.service.generate_thumbnail(image_url, width, height)
        
        assert result is None
    
    def test_analyze_image_from_bytes_success(self):
        """Test successful image analysis from bytes."""
        image_bytes = b"fake_image_data"
        expected_result = {
            "description": "A landscape photo",
            "tags": ["outdoor", "nature", "landscape"]
        }
        
        self.mock_client.analyze_image_in_stream.return_value = Mock(
            description=Mock(captions=[Mock(text="A landscape photo")]),
            tags=[Mock(name="outdoor", confidence=0.9), Mock(name="nature", confidence=0.8)]
        )
        
        result = self.service.analyze_image_from_bytes(image_bytes)
        
        assert result is not None
        assert "description" in result
        self.mock_client.analyze_image_in_stream.assert_called_once()
    
    def test_analyze_image_from_bytes_failure(self):
        """Test image analysis from bytes failure."""
        image_bytes = b"fake_image_data"
        
        self.mock_client.analyze_image_in_stream.side_effect = Exception("Analysis failed")
        
        result = self.service.analyze_image_from_bytes(image_bytes)
        
        assert result is None
    
    def test_extract_text_from_bytes_success(self):
        """Test successful text extraction from bytes."""
        image_bytes = b"fake_document_data"
        expected_text = "Extracted text from document"
        
        mock_result = Mock()
        mock_result.operation_location = "https://test-vision.cognitiveservices.azure.com/operations/123"
        self.mock_client.read_in_stream.return_value = mock_result
        
        mock_polling_result = Mock()
        mock_polling_result.status = "succeeded"
        mock_polling_result.analyze_result = Mock()
        mock_polling_result.analyze_result.read_results = [
            Mock(lines=[Mock(text="Extracted text from document")])
        ]
        
        with patch.object(self.service, '_poll_read_operation') as mock_poll:
            mock_poll.return_value = mock_polling_result
            
            result = self.service.extract_text_from_bytes(image_bytes)
            
            assert result == expected_text
            self.mock_client.read_in_stream.assert_called_once()
    
    def test_extract_text_from_bytes_failure(self):
        """Test text extraction from bytes failure."""
        image_bytes = b"fake_document_data"
        
        self.mock_client.read_in_stream.side_effect = Exception("Text extraction failed")
        
        result = self.service.extract_text_from_bytes(image_bytes)
        
        assert result is None
    
    @patch('time.sleep')
    def test_poll_read_operation_success(self, mock_sleep):
        """Test successful read operation polling."""
        operation_location = "https://test-vision.cognitiveservices.azure.com/operations/123"
        
        mock_result = Mock()
        mock_result.status = "succeeded"
        self.mock_client.get_read_result.return_value = mock_result
        
        result = self.service._poll_read_operation(operation_location)
        
        assert result == mock_result
        self.mock_client.get_read_result.assert_called_once()
    
    @patch('time.sleep')
    def test_poll_read_operation_timeout(self, mock_sleep):
        """Test read operation polling timeout."""
        operation_location = "https://test-vision.cognitiveservices.azure.com/operations/123"
        
        mock_result = Mock()
        mock_result.status = "running"
        self.mock_client.get_read_result.return_value = mock_result
        
        result = self.service._poll_read_operation(operation_location, max_retries=2)
        
        assert result is None
        assert self.mock_client.get_read_result.call_count == 2
    
    @patch('time.sleep')
    def test_poll_read_operation_failed(self, mock_sleep):
        """Test read operation polling with failed status."""
        operation_location = "https://test-vision.cognitiveservices.azure.com/operations/123"
        
        mock_result = Mock()
        mock_result.status = "failed"
        self.mock_client.get_read_result.return_value = mock_result
        
        result = self.service._poll_read_operation(operation_location)
        
        assert result is None
    
    def test_get_dominant_emotion(self):
        """Test dominant emotion detection."""
        emotions = Mock(
            anger=0.1,
            contempt=0.0,
            disgust=0.0,
            fear=0.0,
            happiness=0.9,
            neutral=0.0,
            sadness=0.0,
            surprise=0.0
        )
        
        result = self.service._get_dominant_emotion(emotions)
        
        assert result == "Happy"
    
    def test_get_dominant_emotion_tie(self):
        """Test dominant emotion detection with tie."""
        emotions = Mock(
            anger=0.5,
            contempt=0.0,
            disgust=0.0,
            fear=0.0,
            happiness=0.5,
            neutral=0.0,
            sadness=0.0,
            surprise=0.0
        )
        
        result = self.service._get_dominant_emotion(emotions)
        
        # Should return the first emotion with highest confidence
        assert result in ["Angry", "Happy"] 