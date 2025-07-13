"""
Computer Vision service for text extraction from images.
"""
import logging
from typing import Optional
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from config.settings import settings

logger = logging.getLogger(__name__)


class ComputerVisionService:
    """Service for Azure Computer Vision operations."""
    
    def __init__(self):
        """Initialize Computer Vision client."""
        try:
            self.client = ComputerVisionClient(
                settings.vision_endpoint,
                CognitiveServicesCredentials(settings.vision_key)
            )
            logger.info("Computer Vision client initialized")
        except Exception as e:
            logger.error(f"Error initializing Computer Vision: {e}")
            raise
    
    def extract_text_from_image_file(self, file_path: str) -> str:
        """
        Extract text from image file using OCR.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Extracted text content
        """
        try:
            with open(file_path, 'rb') as image_file:
                # Use OCR API for text extraction
                result = self.client.recognize_printed_text_in_stream(image_file)
                
                text_content = ""
                # Handle the result safely
                if result and hasattr(result, 'regions') and result.regions:  # type: ignore
                    for region in result.regions:  # type: ignore
                        if hasattr(region, 'lines') and region.lines:
                            for line in region.lines:
                                if hasattr(line, 'words') and line.words:
                                    for word in line.words:
                                        if hasattr(word, 'text'):
                                            text_content += word.text + " "
                                text_content += "\n"
                
                logger.info(f"Text extracted from image: {len(text_content)} characters")
                return text_content.strip()
                
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
    
    def extract_text_from_image_url(self, image_url: str) -> str:
        """
        Extract text from image URL using OCR.
        
        Args:
            image_url: URL of the image
            
        Returns:
            Extracted text content
        """
        try:
            # Use Read API for better text extraction
            read_response = self.client.read(image_url, raw=True)
            
            if not read_response or not hasattr(read_response, 'headers'):
                logger.error("Invalid response from Computer Vision API")
                return ""
            
            # Get the operation location (URL with an ID at the end)
            read_operation_location = read_response.headers["Operation-Location"]
            operation_id = read_operation_location.split("/")[-1]  # type: ignore
            
            # Wait for the operation to complete
            while True:
                read_result = self.client.get_read_result(operation_id)
                if not read_result or not hasattr(read_result, 'status'):
                    logger.error("Invalid read result from Computer Vision API")
                    return ""
                    
                if read_result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:  # type: ignore
                    break
            
            # Extract text from the result
            text_content = ""
            if read_result.status == OperationStatusCodes.succeeded:  # type: ignore
                if hasattr(read_result, 'analyze_result') and read_result.analyze_result:  # type: ignore
                    for text_result in read_result.analyze_result.read_results:  # type: ignore
                        if hasattr(text_result, 'lines'):
                            for line in text_result.lines:
                                text_content += line.text + "\n"
            
            logger.info(f"Text extracted from image URL: {len(text_content)} characters")
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from image URL: {e}")
            raise
    
    def extract_text_from_image_bytes(self, image_bytes: bytes) -> str:
        """
        Extract text from image bytes using OCR.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Extracted text content
        """
        try:
            from io import BytesIO
            
            # Create a file-like object from bytes
            image_stream = BytesIO(image_bytes)
            
            # Use OCR API for text extraction
            result = self.client.recognize_printed_text_in_stream(image_stream)
            
            text_content = ""
            # Handle the result safely
            if result and hasattr(result, 'regions') and result.regions:  # type: ignore
                for region in result.regions:  # type: ignore
                    if hasattr(region, 'lines') and region.lines:
                        for line in region.lines:
                            if hasattr(line, 'words') and line.words:
                                for word in line.words:
                                    if hasattr(word, 'text'):
                                        text_content += word.text + " "
                            text_content += "\n"
            
            logger.info(f"Text extracted from image bytes: {len(text_content)} characters")
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from image bytes: {e}")
            return ""

    def analyze_image(self, file_path: str) -> Optional[dict]:
        """
        Analyze image for tags, descriptions, and other features.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Analysis results or None if error
        """
        try:
            with open(file_path, 'rb') as image_file:
                # Analyze image
                analysis = self.client.analyze_image_in_stream(
                    image_file,
                    visual_features=['tags', 'description', 'faces', 'objects'],
                    language='en'
                )
                
                if not analysis:
                    logger.error("No analysis result received")
                    return None
                
                result = {
                    'tags': [tag.name for tag in analysis.tags] if hasattr(analysis, 'tags') and analysis.tags else [],  # type: ignore
                    'description': analysis.description.captions[0].text if (hasattr(analysis, 'description') and analysis.description and analysis.description.captions) else "",  # type: ignore
                    'faces_count': len(analysis.faces) if hasattr(analysis, 'faces') and analysis.faces else 0,  # type: ignore
                    'objects': [obj.object_property for obj in analysis.objects] if hasattr(analysis, 'objects') and analysis.objects else []  # type: ignore
                }
                
                logger.info(f"Image analyzed: {len(result['tags'])} tags found")
                return result
                
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None


# Global service instance
computer_vision_service = ComputerVisionService() 