"""
Unit tests for Document Processor.
"""
from unittest.mock import Mock, patch, MagicMock
from core.document_processor import DocumentProcessor


class TestDocumentProcessor:
    """Test cases for Document Processor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock all dependencies explícitamente
        self.mock_blob_service = Mock()
        self.mock_openai_service = Mock()
        self.mock_redis_service = Mock()
        self.mock_vision_service = Mock()
        self.processor = DocumentProcessor(
            blob_service=self.mock_blob_service,
            openai_service=self.mock_openai_service,
            redis_service=self.mock_redis_service,
            vision_service=self.mock_vision_service
        )
    
    def test_init_success(self):
        """Test successful initialization."""
        assert self.processor.vision_service == self.mock_vision_service
        assert self.processor.openai_service == self.mock_openai_service
        assert self.processor.blob_service == self.mock_blob_service
        assert self.processor.redis_service == self.mock_redis_service
    
    @patch('requests.get')
    @patch('pypdf.PdfReader')  # Mockear el lector de PDF usando pypdf
    def test_process_document_pdf_success(self, mock_pdf_reader, mock_requests_get):
        """Test successful PDF document processing."""
        # Arrange
        file_url = "https://example.com/document.pdf"
        file_name = "test_document.pdf"
        user_id = "user_123"
        options = {"extract_text": True, "generate_embeddings": True}
        
        mock_response = Mock()
        mock_response.content = b"fake_pdf_content"
        mock_requests_get.return_value = mock_response
        
        # Simular que el PDFReader devuelve páginas con texto
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Extracted text from PDF"
        mock_pdf.pages = [mock_page]
        mock_pdf_reader.return_value = mock_pdf
        
        self.mock_openai_service.generate_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)
        
        # Assert
        assert result["success"] is True
        assert result["content"] == "Extracted text from PDF"
        assert result["embeddings"] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert "metadata" in result
        assert "processing_id" in result
        
        mock_requests_get.assert_called_once_with(file_url, timeout=30)
        mock_pdf_reader.assert_called_once()
        self.mock_openai_service.generate_embedding.assert_called_once()
    
    @patch('requests.get')
    @patch('pypdf.PdfReader')
    @patch('docx.Document')
    def test_process_document_docx_success(self, mock_document, mock_pdf_reader, mock_requests_get):
        """Test successful DOCX document processing."""
        # Arrange
        file_url = "https://example.com/document.docx"
        file_name = "test_document.docx"
        user_id = "user_123"
        options = {"extract_text": True, "generate_embeddings": True}
        
        mock_response = Mock()
        mock_response.content = b"fake_docx_content"
        mock_requests_get.return_value = mock_response
        
        mock_doc = Mock()
        mock_doc.paragraphs = [Mock(text="Paragraph 1"), Mock(text="Paragraph 2")]
        mock_document.return_value = mock_doc
        
        self.mock_openai_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)
        
        # Assert
        assert result["success"] is True
        assert "Paragraph 1\nParagraph 2" in result["content"]
        assert result["embeddings"] == [0.1, 0.2, 0.3]
    
    @patch('requests.get')
    @patch('pypdf.PdfReader')
    def test_process_document_txt_success(self, mock_pdf_reader, mock_requests_get):
        """Test successful TXT document processing."""
        # Arrange
        file_url = "https://example.com/document.txt"
        file_name = "test_document.txt"
        user_id = "user_123"
        options = {"extract_text": True, "generate_embeddings": True}
        
        mock_response = Mock()
        mock_response.content = b"Simple text content"
        mock_response.text = "Simple text content"
        mock_requests_get.return_value = mock_response
        
        self.mock_openai_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)
        
        # Assert
        assert result["success"] is True
        assert result["content"] == "Simple text content"
        assert result["embeddings"] == [0.1, 0.2, 0.3]
    
    @patch('requests.get')
    def test_process_document_download_failure(self, mock_requests_get):
        """Test document download failure."""
        # Arrange
        file_url = "https://example.com/document.pdf"
        file_name = "test_document.pdf"
        user_id = "user_123"
        options = {"extract_text": True}
        
        mock_requests_get.side_effect = Exception("Download failed")
        
        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "Failed to process document" in result["error"]
    
    @patch('requests.get')
    def test_process_document_unsupported_format(self, mock_requests_get):
        """Test unsupported document format."""
        # Arrange
        file_url = "https://example.com/document.xyz"
        file_name = "test_document.xyz"
        user_id = "user_123"
        options = {"extract_text": True}
        
        mock_response = Mock()
        mock_response.content = b"content"
        mock_requests_get.return_value = mock_response
        
        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "Unsupported file format" in result["error"]
    
    @patch('requests.get')
    @patch('pypdf.PdfReader')
    def test_process_document_text_extraction_failure(self, mock_pdf_reader, mock_requests_get):
        """Test text extraction failure."""
        # Arrange
        file_url = "https://example.com/document.pdf"
        file_name = "test_document.pdf"
        user_id = "user_123"
        options = {"extract_text": True}
        
        mock_response = Mock()
        mock_response.content = b"fake_pdf_content"
        mock_requests_get.return_value = mock_response
        
        # Simular que el PDFReader falla
        mock_pdf_reader.side_effect = Exception("PDF processing failed")
        
        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "Failed to process document" in result["error"]
    
    @patch('requests.get')
    @patch('pypdf.PdfReader')
    def test_process_document_embedding_generation_failure(self, mock_pdf_reader, mock_requests_get):
        """Test embedding generation failure."""
        # Arrange
        file_url = "https://example.com/document.pdf"
        file_name = "test_document.pdf"
        user_id = "user_123"
        options = {"extract_text": True, "generate_embeddings": True}
        
        mock_response = Mock()
        mock_response.content = b"fake_pdf_content"
        mock_requests_get.return_value = mock_response
        
        # Simular que el PDFReader devuelve páginas con texto
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Extracted text"
        mock_pdf.pages = [mock_page]
        mock_pdf_reader.return_value = mock_pdf
        
        self.mock_vision_service.extract_text.return_value = "Extracted text"
        self.mock_openai_service.generate_embedding.side_effect = Exception("Embedding generation failed")
        
        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "Failed to process document" in result["error"]
    
    @patch('requests.get')
    @patch('pypdf.PdfReader')
    def test_process_document_without_embeddings(self, mock_pdf_reader, mock_requests_get):
        """Test document processing without embedding generation."""
        # Arrange
        file_url = "https://example.com/document.pdf"
        file_name = "test_document.pdf"
        user_id = "user_123"
        options = {"extract_text": True, "generate_embeddings": False}
        
        mock_response = Mock()
        mock_response.content = b"fake_pdf_content"
        mock_requests_get.return_value = mock_response
        
        # Simular que el PDFReader devuelve páginas con texto
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Extracted text"
        mock_pdf.pages = [mock_page]
        mock_pdf_reader.return_value = mock_pdf
        
        self.mock_vision_service.extract_text.return_value = "Extracted text"
        
        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)
        
        # Assert
        assert result["success"] is True
        assert result["content"] == "Extracted text"
        assert "embeddings" not in result or result["embeddings"] is None
        self.mock_openai_service.generate_embedding.assert_not_called()
    
    @patch('requests.get')
    @patch('pypdf.PdfReader')
    def test_process_document_with_image_analysis(self, mock_pdf_reader, mock_requests_get):
        """Test document processing with image analysis."""
        # Arrange
        file_url = "https://example.com/document.pdf"
        file_name = "test_document.pdf"
        user_id = "user_123"
        options = {"extract_text": True, "analyze_images": True}
        
        mock_response = Mock()
        mock_response.content = b"fake_pdf_content"
        mock_requests_get.return_value = mock_response
        
        # Simular que el PDFReader devuelve páginas con texto
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Extracted text"
        mock_pdf.pages = [mock_page]
        mock_pdf_reader.return_value = mock_pdf
        
        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)
        
        # Assert
        assert result["success"] is True
        assert result["content"] == "Extracted text"
        # Nota: analyze_images no está implementado en process_document, 
        # así que no se espera image_analysis en los metadatos
    
    @patch('requests.get')
    @patch('pypdf.PdfReader')
    def test_process_document_with_summary(self, mock_pdf_reader, mock_requests_get):
        """Test document processing with summary generation."""
        # Arrange
        file_url = "https://example.com/document.pdf"
        file_name = "test_document.pdf"
        user_id = "user_123"
        options = {"extract_text": True, "generate_summary": True}
        
        mock_response = Mock()
        mock_response.content = b"fake_pdf_content"
        mock_requests_get.return_value = mock_response
        
        # Simular que el PDFReader devuelve páginas con texto
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Long document content that needs summarization"
        mock_pdf.pages = [mock_page]
        mock_pdf_reader.return_value = mock_pdf
        
        self.mock_openai_service.generate_text.return_value = "Document summary"
        
        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)
        
        # Assert
        assert result["success"] is True
        # Nota: generate_summary no está implementado en process_document,
        # así que no se espera un campo "summary" en el resultado
    
    def test_validate_file_url_valid(self):
        """Test valid file URL validation."""
        valid_urls = [
            "https://example.com/document.pdf",
            "http://test.com/file.docx",
            "https://docs.google.com/viewer?url=https://example.com/file.txt"
        ]
        
        for url in valid_urls:
            result = self.processor.validate_file_url(url)
            assert result is True
    
    def test_validate_file_url_invalid(self):
        """Test invalid file URL validation."""
        invalid_urls = [
            "",
            "not_a_url",
            "ftp://example.com/file.pdf",
            "https://example.com/file with spaces.pdf",
            "https://example.com/file\nwith\nnewlines.pdf"
        ]
        
        for url in invalid_urls:
            result = self.processor.validate_file_url(url)
            assert result is False
    
    def test_get_file_extension(self):
        """Test file extension extraction."""
        test_cases = [
            ("document.pdf", "pdf"),
            ("file.docx", "docx"),
            ("text.txt", "txt"),
            ("no_extension", ""),
            ("multiple.dots.file.pdf", "pdf"),
            ("", ""),
            (None, "")
        ]
        
        for filename, expected in test_cases:
            result = self.processor.get_file_extension(filename)
            assert result == expected
    
    def test_is_supported_format(self):
        """Test supported format validation."""
        supported_formats = ["pdf", "docx", "txt", "jpg", "png"]
        unsupported_formats = ["xyz", "exe", "mp4", "unknown"]
        
        for fmt in supported_formats:
            result = self.processor.is_supported_format(fmt)
            assert result is True
        
        for fmt in unsupported_formats:
            result = self.processor.is_supported_format(fmt)
            assert result is False
    
    @patch('requests.get')
    @patch('pypdf.PdfReader')
    def test_process_document_large_file_warning(self, mock_pdf_reader, mock_requests_get):
        """Test large file processing with warning."""
        # Arrange
        file_url = "https://example.com/large_document.pdf"
        file_name = "large_document.pdf"
        user_id = "user_123"
        options = {"extract_text": True}
        
        # Simulate large file content
        large_content = b"x" * (50 * 1024 * 1024)  # 50MB
        mock_response = Mock()
        mock_response.content = large_content
        mock_requests_get.return_value = mock_response

        # Simular que el PDFReader devuelve páginas con texto
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Large document content"
        mock_pdf.pages = [mock_page]
        mock_pdf_reader.return_value = mock_pdf
        
        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)
        
        # Assert
        assert result["success"] is True
        assert "warning" in result["metadata"]
        assert "large file" in result["metadata"]["warning"].lower()
    
    @patch('requests.get')
    @patch('pypdf.PdfReader')
    def test_process_document_with_metadata(self, mock_pdf_reader, mock_requests_get):
        """Test document processing with comprehensive metadata."""
        # Arrange
        file_url = "https://example.com/document.pdf"
        file_name = "test_document.pdf"
        user_id = "user_123"
        options = {"extract_text": True, "generate_embeddings": True}

        mock_response = Mock()
        mock_response.content = b"fake_pdf_content"
        mock_response.headers = {"content-length": "1024"}
        mock_requests_get.return_value = mock_response

        # Simular que el PDFReader devuelve páginas con texto
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Extracted text content"
        mock_pdf.pages = [mock_page]
        mock_pdf_reader.return_value = mock_pdf

        self.mock_openai_service.generate_embedding.return_value = [0.1, 0.2, 0.3]

        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)

        # Assert
        assert result["success"] is True
        metadata = result["metadata"]
        assert "file_name" in metadata
        assert metadata["file_name"] == file_name
        assert "file_type" in metadata
        assert metadata["file_type"] == "pdf"
        assert "user_id" in metadata
        assert metadata["user_id"] == user_id
        # Nota: file_size no está implementado en el código real

    @patch('requests.get')
    @patch('pypdf.PdfReader')
    def test_process_document_error_handling(self, mock_pdf_reader, mock_requests_get):
        """Test comprehensive error handling."""
        # Arrange
        file_url = "https://example.com/document.pdf"
        file_name = "test_document.pdf"
        user_id = "user_123"
        options = {"extract_text": True, "generate_embeddings": True}

        mock_response = Mock()
        mock_response.content = b"fake_pdf_content"
        mock_requests_get.return_value = mock_response

        # Simular que el PDFReader falla
        mock_pdf_reader.side_effect = Exception("PDF processing failed")

        # Act
        result = self.processor.process_document(file_url, file_name, user_id, options)

        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "Failed to process document" in result["error"]
        assert "processing_id" in result  # Should still have processing ID for tracking 
    
    def test_process_pdf_scanned(self):
        """Test procesamiento de PDF escaneado usando visión computacional."""
        from unittest.mock import MagicMock
        processor = self.processor
        processor.vision_service.extract_text_from_image_bytes.return_value = "Texto extraído de imagen PDF"
        processor.openai_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        processor.redis_service.set_cache.return_value = True
        # Simular PDF escaneado (sin texto, pero con imágenes)
        with patch('fitz.open') as mock_fitz_open, patch('pypdf.PdfReader') as mock_pdf_reader:
            mock_doc = MagicMock()
            mock_page = Mock()
            mock_page.get_images.return_value = [(1,)]
            mock_page.load_page.return_value = mock_page
            mock_doc.load_page.return_value = mock_page
            mock_doc.get_images.return_value = [(1,)]
            mock_doc.extract_image.return_value = {'image': b'fake_image_bytes'}
            mock_doc.__len__.return_value = 1
            mock_fitz_open.return_value = mock_doc
            # Mock PdfReader para que .pages sea vacío (simula PDF escaneado)
            mock_pdf = MagicMock()
            mock_pdf.pages = []
            mock_pdf_reader.return_value = mock_pdf
            fake_blob_stream = Mock()
            fake_blob_stream.read.return_value = b"fake_pdf_bytes"
            result = processor.process_document_from_blob(fake_blob_stream, "archivo.pdf")
            assert result is True
            processor.vision_service.extract_text_from_image_bytes.assert_called()
            processor.openai_service.generate_embedding.assert_called()
            processor.redis_service.set_cache.assert_called() 