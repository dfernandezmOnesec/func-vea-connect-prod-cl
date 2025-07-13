"""
Central project configuration using Pydantic v2.
Handles all environment variables and configurations.
"""
import os
from typing import Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Main project configuration.
    - acs_whatsapp_endpoint: Endpoint base para WhatsApp REST API de ACS
    - acs_whatsapp_api_key: API key o token para WhatsApp REST API de ACS
    """
    
    # Azure Communication Services
    acs_connection_string: str = Field(..., description="ACS connection string")
    acs_phone_number: str = Field(..., description="ACS phone number")
    acs_event_grid_topic_endpoint: str = Field(..., description="ACS Event Grid topic endpoint")
    acs_event_grid_topic_key: str = Field(..., description="ACS Event Grid topic key")
    acs_whatsapp_endpoint: str = Field(default="", description="ACS WhatsApp REST API endpoint")
    acs_whatsapp_api_key: str = Field(default="", description="ACS WhatsApp REST API key or token")
    
    # Azure OpenAI Service
    azure_openai_endpoint: str = Field(..., description="Azure OpenAI endpoint")
    azure_openai_chat_deployment: str = Field(..., description="Azure OpenAI chat deployment")
    azure_openai_chat_api_version: str = Field(..., description="Azure OpenAI chat API version")
    azure_openai_embeddings_deployment: str = Field(..., description="Azure OpenAI embeddings deployment")
    azure_openai_embeddings_api_version: str = Field(..., description="Azure OpenAI embeddings API version")
    openai_api_key: str = Field(..., description="OpenAI API key")
    
    # Redis
    redis_connection_string: str = Field(..., description="Redis connection string")
    redis_cache_ttl: int = Field(default=3600, description="Redis cache TTL in seconds")
    
    # Azure Blob Storage
    azure_storage_connection_string: str = Field(..., description="Azure Storage connection string")
    blob_account_name: str = Field(..., description="Blob storage account name")
    blob_container_name: str = Field(..., description="Blob container name")
    
    # Computer Vision
    vision_endpoint: str = Field(..., description="Computer Vision endpoint")
    vision_key: str = Field(..., description="Computer Vision key")
    
    # Queue for async processing
    queue_name: str = Field(..., description="Queue name for document processing")
    
    # General configuration
    environment: str = Field(default="development", description="Environment")
    log_level: str = Field(default="INFO", description="Log level")
    
    # Embedding configuration
    embedding_cache_ttl: int = Field(default=86400, description="Embedding cache TTL in seconds")
    
    # Message processing configuration
    max_message_length: int = Field(default=4096, description="Max message length")
    message_timeout: int = Field(default=30, description="Message timeout in seconds")
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Create configuration from environment variables."""
        return cls(
            acs_connection_string=os.getenv("ACS_CONNECTION_STRING", ""),
            acs_phone_number=os.getenv("ACS_PHONE_NUMBER", ""),
            acs_event_grid_topic_endpoint=os.getenv("ACS_EVENT_GRID_TOPIC_ENDPOINT", ""),
            acs_event_grid_topic_key=os.getenv("ACS_EVENT_GRID_TOPIC_KEY", ""),
            acs_whatsapp_endpoint=os.getenv("ACS_WHATSAPP_ENDPOINT", ""),
            acs_whatsapp_api_key=os.getenv("ACS_WHATSAPP_API_KEY", ""),
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            azure_openai_chat_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", ""),
            azure_openai_chat_api_version=os.getenv("AZURE_OPENAI_CHAT_API_VERSION", ""),
            azure_openai_embeddings_deployment=os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", ""),
            azure_openai_embeddings_api_version=os.getenv("AZURE_OPENAI_EMBEDDINGS_API_VERSION", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            redis_connection_string=os.getenv("REDIS_CONNECTION_STRING", ""),
            redis_cache_ttl=int(os.getenv("REDIS_CACHE_TTL", "3600")),
            azure_storage_connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING", ""),
            blob_account_name=os.getenv("BLOB_ACCOUNT_NAME", ""),
            blob_container_name=os.getenv("BLOB_CONTAINER_NAME", ""),
            vision_endpoint=os.getenv("VISION_ENDPOINT", ""),
            vision_key=os.getenv("VISION_KEY", ""),
            queue_name=os.getenv("QUEUE_NAME", ""),
            environment=os.getenv("ENVIRONMENT", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            embedding_cache_ttl=int(os.getenv("EMBEDDING_CACHE_TTL", "86400")),
            max_message_length=int(os.getenv("MAX_MESSAGE_LENGTH", "4096")),
            message_timeout=int(os.getenv("MESSAGE_TIMEOUT", "30")),
        )


# Global configuration instance
settings = Settings.from_env() 