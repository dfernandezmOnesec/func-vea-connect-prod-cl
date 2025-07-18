"""
Azure OpenAI Service for embeddings and text generation.
"""
import logging
from typing import List, Optional, Dict, Any, Sequence, cast
from openai import AzureOpenAI
from config.settings import settings
from openai.types.chat import ChatCompletionMessageParam

logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """Service for Azure OpenAI."""
    
    def __init__(
        self,
        client=None,
        logger_instance=None,
        settings_instance=None
    ):
        self.settings = settings_instance or settings
        self.logger = logger_instance or logger
        if client is not None:
            self.client = client
        else:
            self.client = AzureOpenAI(
                api_key=self.settings.openai_api_key,
                api_version=self.settings.azure_openai_chat_api_version,
                azure_endpoint=self.settings.azure_openai_endpoint
            )
        self.chat_deployment = self.settings.azure_openai_chat_deployment
        self.embeddings_deployment = self.settings.azure_openai_embeddings_deployment
        self.embeddings_api_version = self.settings.azure_openai_embeddings_api_version
        self.logger.info(f"Azure OpenAI client initialized with chat deployment: {self.chat_deployment}")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using Azure OpenAI.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector or None if error
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embeddings_deployment
            )
            
            embedding = response.data[0].embedding
            self.logger.debug(f"Embedding generated for text of {len(text)} characters")
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_text(self, prompt: str, max_tokens: Optional[int] = None) -> Optional[str]:
        """
        Generate text using Azure OpenAI.
        
        Args:
            prompt: Prompt to generate text from
            max_tokens: Maximum number of tokens (uses default if None)
            
        Returns:
            Generated text or None if error
        """
        try:
            if max_tokens is None:
                max_tokens = 1000
            
            response = self.client.chat.completions.create(
                model=self.chat_deployment,
                messages=[
                    {"role": "system", "content": "You are a helpful and friendly assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            generated_text = response.choices[0].message.content
            if generated_text is not None:
                self.logger.debug(f"Text generated: {len(generated_text)} characters")
            else:
                self.logger.debug("Text generated: None")
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Error generating text: {e}")
            return None
    
    def generate_chat_response(self, messages: Sequence[Dict[str, str]], max_tokens: Optional[int] = None) -> Optional[str]:
        """
        Generate response for a conversation.
        
        Args:
            messages: List of messages in format [{"role": "user", "content": "..."}]
            max_tokens: Maximum number of tokens
            
        Returns:
            Generated response or None if error
        """
        try:
            if max_tokens is None:
                max_tokens = 1000
            # Convert messages to correct type
            chat_messages = [
                {"role": m["role"], "content": m["content"]} for m in messages
            ]
            response = self.client.chat.completions.create(
                model=self.chat_deployment,
                messages=cast(List[ChatCompletionMessageParam], chat_messages),
                max_tokens=max_tokens,
                temperature=0.7
            )
            generated_text = response.choices[0].message.content
            if generated_text is not None:
                self.logger.debug(f"Chat response generated: {len(generated_text)} characters")
            else:
                self.logger.debug("Chat response generated: None")
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Error generating chat response: {e}")
            return None
    
    def analyze_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis or None if error
        """
        try:
            prompt = f"""
            Analyze the sentiment of the following text and respond in JSON format:
            {{
                "sentiment": "positive|negative|neutral",
                "confidence": 0.0-1.0,
                "emotions": ["emotion1", "emotion2"],
                "summary": "brief summary"
            }}
            
            Text: {text}
            """
            
            response = self.generate_text(prompt)
            if response:
                import json
                return json.loads(response)
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return None
    
    def extract_keywords(self, text: str) -> Optional[List[str]]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of keywords or None if error
        """
        try:
            prompt = f"""
            Extract the most important keywords from the following text.
            Respond only with a comma-separated list:
            
            Text: {text}
            """
            
            response = self.generate_text(prompt)
            if response:
                keywords = [kw.strip() for kw in response.split(',')]
                return keywords
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return None
    
    def generate_chat_response_with_context(self, user_number: str, message: str, conversation_context: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
        """
        Generate chat response with conversation context.
        
        Args:
            user_number: User's phone number
            message: Current message from user
            conversation_context: Previous conversation messages
            
        Returns:
            Generated response or None if error
        """
        try:
            # Build conversation history
            messages = []
            
            # Add system message
            system_message = {
                "role": "system",
                "content": "You are a helpful WhatsApp assistant. Be friendly, concise, and helpful. Respond in the same language as the user's message."
            }
            messages.append(system_message)
            
            # Add conversation context if available
            if conversation_context:
                for msg in conversation_context[-10:]:  # Limit to last 10 messages
                    if msg.get("role") in ["user", "assistant"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Generate response
            response = self.generate_chat_response(messages, max_tokens=500)
            
            if response:
                self.logger.info(f"Generated response for user {user_number}: {len(response)} characters")
            else:
                self.logger.warning(f"Failed to generate response for user {user_number}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating chat response with context for user {user_number}: {e}")
            return None


# Global service instance
openai_service = AzureOpenAIService() 