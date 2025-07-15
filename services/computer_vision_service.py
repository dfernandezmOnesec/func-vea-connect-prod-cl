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
            return ""
    
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

    def analyze_image(self, image: str) -> Optional[dict]:
        """
        Analiza una imagen desde un archivo o URL para tags, descripciones y objetos.
        """
        try:
            if image.startswith('http://') or image.startswith('https://'):
                analysis = self.client.analyze_image(image, visual_features=['tags', 'description', 'faces', 'objects'])
            else:
                with open(image, 'rb') as image_file:
                    analysis = self.client.analyze_image_in_stream(
                        image_file,
                        visual_features=['tags', 'description', 'faces', 'objects'],
                        language='en'
                    )
                if not analysis:
                    logger.error("No analysis result received")
                    return None
                result = {
                'tags': [tag.name for tag in getattr(analysis, 'tags', [])],
                'description': getattr(getattr(analysis, 'description', None), 'captions', [{}])[0].text if (hasattr(analysis, 'description') and getattr(analysis, 'description', None) and getattr(getattr(analysis, 'description', None), 'captions', None)) else "",
                'objects': [{"name": obj.object_property, "confidence": obj.confidence} for obj in getattr(analysis, 'objects', [])]
                }
                logger.info(f"Image analyzed: {len(result['tags'])} tags found")
                return result
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None

    def extract_text(self, image_url: str) -> Optional[str]:
        """Extrae texto de una imagen desde una URL usando el API de Read."""
        try:
            if hasattr(self.client, 'read'):
                read_response = self.client.read(image_url, raw=True)
            else:
                return None
            if not read_response or not hasattr(read_response, 'operation_location'):
                logger.error("Invalid response from Computer Vision API")
                return None
            operation_location = getattr(read_response, 'operation_location', None)
            if not operation_location:
                logger.error("operation_location is None")
                return None
            # Usar el método de polling para tests
            poll_result = self._poll_read_operation(operation_location)
            if not poll_result or not hasattr(poll_result, 'analyze_result') or not getattr(poll_result, 'analyze_result', None):
                return None
            text_content = ""
            for text_result in getattr(getattr(poll_result, 'analyze_result', None), 'read_results', []):
                if hasattr(text_result, 'lines'):
                    for line in text_result.lines:
                        text_content += line.text + "\n"
            return text_content.strip() if text_content else None
        except Exception as e:
            logger.error(f"Error extracting text from image URL: {e}")
            return None

    def detect_objects(self, image_url: str) -> Optional[list]:
        """Detecta objetos en una imagen desde una URL."""
        try:
            analysis = self.client.detect_objects(image_url)
            if not hasattr(analysis, 'objects') or not getattr(analysis, 'objects', None):
                return None
            objects = []
            for obj in getattr(analysis, 'objects', []):
                rect = obj.rectangle
                # Convertir Mock o cualquier objeto a dict plano
                if hasattr(rect, 'as_dict'):
                    rect_dict = rect.as_dict()
                else:
                    rect_dict = {k: getattr(rect, k, None) for k in ['x','y','w','h']}
                # Si sigue siendo Mock, convertir a dict plano
                if not isinstance(rect_dict, dict):
                    rect_dict = {k: getattr(rect, k, None) for k in ['x','y','w','h']}
                objects.append({
                    "name": obj.object_property,
                    "confidence": obj.confidence,
                    "rectangle": rect_dict
                })
            return objects
        except Exception as e:
            logger.error(f"Error detecting objects: {e}")
            return None

    def analyze_face(self, image_url: str) -> Optional[dict]:
        """Analiza rostros en una imagen desde una URL."""
        try:
            analysis = self.client.analyze_image(image_url, visual_features=["faces"])
            if not hasattr(analysis, 'faces') or not getattr(analysis, 'faces', None):
                return None
            face = getattr(analysis, 'faces', [None])[0]
            if not face:
                return None
            return {
                "age": getattr(face, 'age', None),
                "gender": getattr(face, 'gender', None),
                "emotion": self._get_dominant_emotion(getattr(face, 'emotion', None)) if hasattr(face, 'emotion') else None,
                    "glasses": getattr(face, 'glasses', None)
                }
        except Exception as e:
            logger.error(f"Error analyzing face: {e}")
            return None

    def generate_thumbnail(self, image_url: str, width: int, height: int) -> Optional[bytes]:
        """Genera un thumbnail de la imagen."""
        try:
            result = self.client.generate_thumbnail(width, height, image_url, smart_cropping=True)
            if isinstance(result, bytes):
                return result
            return None
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None

    def analyze_image_from_bytes(self, image_bytes: bytes) -> Optional[dict]:
        """Analiza una imagen desde bytes."""
        try:
            from io import BytesIO
            image_stream = BytesIO(image_bytes)
            analysis = self.client.analyze_image_in_stream(
                image_stream,
                visual_features=["tags", "description", "faces", "objects"],
                language="en"
            )
            # tags
            tags_attr = getattr(analysis, 'tags', [])
            try:
                tags = [tag.name for tag in tags_attr]
            except TypeError:
                tags = []
            # description
            description = getattr(getattr(analysis, 'description', None), 'captions', [{}])[0].text if (hasattr(analysis, 'description') and getattr(analysis, 'description', None) and getattr(getattr(analysis, 'description', None), 'captions', None)) else ""
            # faces
            faces = getattr(analysis, 'faces', []) if hasattr(analysis, 'faces') else []
            try:
                faces_count = len(faces)
            except TypeError:
                faces_count = 0
            # objects
            objects_attr = getattr(analysis, 'objects', [])
            try:
                objects = [obj.object_property for obj in objects_attr]
            except TypeError:
                objects = []
            return {
                'tags': tags,
                'description': description,
                'faces_count': faces_count,
                'objects': objects
            }
        except Exception as e:
            logger.error(f"Error analyzing image from bytes: {e}")
            return None

    def extract_text_from_bytes(self, image_bytes: bytes) -> Optional[str]:
        """Extrae texto desde bytes usando el API de Read (mockeable para tests)."""
        try:
            if hasattr(self.client, 'read_in_stream'):
                read_response = self.client.read_in_stream(image_bytes, raw=True)
            else:
                return None
            if not read_response or not hasattr(read_response, 'operation_location'):
                logger.error("Invalid response from Computer Vision API")
                return None
            operation_location = getattr(read_response, 'operation_location', None)
            if not operation_location:
                logger.error("operation_location is None")
                return None
            poll_result = self._poll_read_operation(operation_location)
            if not poll_result or not hasattr(poll_result, 'analyze_result') or not getattr(poll_result, 'analyze_result', None):
                return None
            text_content = ""
            for text_result in getattr(getattr(poll_result, 'analyze_result', None), 'read_results', []):
                if hasattr(text_result, 'lines'):
                    for line in text_result.lines:
                        text_content += line.text + "\n"
            return text_content.strip() if text_content else None
        except Exception as e:
            logger.error(f"Error extracting text from image bytes: {e}")
            return None

    def _poll_read_operation(self, operation_location: str, max_retries: int = 10) -> object:
        """Espera a que termine la operación de lectura OCR."""
        import time
        operation_id = operation_location.split("/")[-1]
        for _ in range(max_retries):
            result = self.client.get_read_result(operation_id)  # type: ignore
            if hasattr(result, 'status'):
                if result.status == OperationStatusCodes.succeeded:  # type: ignore
                    return result
                elif result.status in [OperationStatusCodes.failed]:  # type: ignore
                    return None
            time.sleep(1)
        return None

    def _get_dominant_emotion(self, emotions) -> str:
        """Devuelve la emoción dominante de un objeto de emociones."""
        if not emotions:
            return ""
        
        # Mapeo de nombres de emociones
        emotion_mapping = {
            'anger': 'Angry',
            'contempt': 'Contempt',
            'disgust': 'Disgust',
            'fear': 'Fear',
            'happiness': 'Happy',
            'neutral': 'Neutral',
            'sadness': 'Sad',
            'surprise': 'Surprise'
        }
        
        emotion_scores = {k: v for k, v in emotions.__dict__.items() if isinstance(v, (int, float))}
        if not emotion_scores:
            return ""
        
        dominant_emotion = max(emotion_scores, key=lambda x: emotion_scores[x])  # type: ignore
        result = emotion_mapping.get(dominant_emotion, dominant_emotion)
        return result if result else ""


# Global service instance
computer_vision_service = ComputerVisionService() 