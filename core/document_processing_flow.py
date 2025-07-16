import re
import json
from typing import Dict, Any, Optional
from services.azure_blob_service import azure_blob_service
from services.redis_service import redis_service
from services.openai_service import openai_service
from services.computer_vision_service import computer_vision_service
from core.embedding_manager import embedding_manager
from core.parsers.donativo_parser import DonativoParser
from core.parsers.evento_parser import EventoParser
from core.parsers.contacto_parser import ContactoParser
# from db.crud import insert_document_pg, delete_document_pg, get_document_pg  # Uncomment and adapt to your real DB layer


def extract_text_from_blob(blob_name: str) -> str:
    """
    Extract text from a blob in Azure Storage. Uses Computer Vision for images, reads text for .txt/.json, etc.
    """
    file_extension = blob_name.split('.')[-1].lower()
    if file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff']:
        # Download as bytes and extract text from image
        file_bytes = azure_blob_service.download_text(blob_name)  # This may need to be download_file or similar for binary
        if isinstance(file_bytes, str):
            file_bytes = file_bytes.encode('utf-8')
        text = computer_vision_service.extract_text_from_bytes(file_bytes)
        return text or ""
    elif file_extension == 'json':
        json_text = azure_blob_service.download_text(blob_name)
        json_data = json.loads(json_text) if json_text else {}
        return json.dumps(json_data, ensure_ascii=False)
    elif file_extension in ['txt', 'md', 'csv']:
        text = azure_blob_service.download_text(blob_name)
        return text or ""
    else:
        raise ValueError("Unsupported file format for text extraction")


def process_and_embed_document(blob_name: str, category: str) -> Dict[str, Any]:
    """
    Process a document from Azure Storage, extract text, parse metadata, generate embeddings, and store in Redis and PostgreSQL.
    """
    text = extract_text_from_blob(blob_name)
    if category == "donativo":
        metadata = DonativoParser.parse(text)
    elif category == "evento":
        metadata = EventoParser.parse(text)
    elif category == "contacto":
        metadata = ContactoParser.parse(text)
    else:
        metadata = {}
    embedding = openai_service.generate_embedding(text)
    doc_id = generate_doc_id(blob_name)
    document_data = {
        "doc_id": doc_id,
        "category": category,
        "metadata": metadata,
        "embeddings": embedding
    }
    redis_service.set_cache(f"doc:{doc_id}", document_data)
    # TODO: Insert or update in PostgreSQL here (e.g., insert_document_pg(document_data))
    return document_data


def create_document(document_data: dict, file_blob: bytes, category: str):
    """
    Create a document: upload to Storage, insert in DB, process and embed, store in Redis.
    """
    azure_blob_service.upload_text(document_data["file_name"], file_blob.decode('utf-8'))  # Adjust if binary
    # TODO: Insert in PostgreSQL here (e.g., insert_document_pg(document_data))
    process_and_embed_document(document_data["file_name"], category)


def delete_document(doc_id: str, file_name: str):
    """
    Delete a document from Storage, Redis, and DB.
    """
    azure_blob_service.delete_blob(file_name)
    redis_service.delete_cache(f"doc:{doc_id}")
    # TODO: Delete from PostgreSQL here (e.g., delete_document_pg(doc_id))


def find_similar_and_extract_fields(user_message: str, category: str) -> Optional[Dict[str, Any]]:
    """
    Find the most similar document by embedding and extract structured metadata for the given category.
    """
    user_embedding = openai_service.generate_embedding(user_message)
    # TODO: Implement a real vector search in Redis or use embedding_manager if available
    # For now, simulate by listing all doc keys and picking the first matching category
    # In production, replace with a real similarity search
    for key in redis_service.client.scan_iter("doc:*"):
        doc = redis_service.get_cache(key)
        if doc and doc.get("category") == category:
            return doc.get("metadata")
    return None


def validate_template_params(params: dict) -> bool:
    """
    Returns True if all values in the params dict are non-empty (not '', None, or only whitespace).
    """
    return all(str(v).strip() for v in params.values())


def send_fallback_message(custom_message: str = None):
    """
    Send a VEA-style fallback/help message to the user.
    """
    response_text = custom_message or (
        "¡Hola hermano(a)! ¿En qué puedo ayudarte? Actualmente puedo ofrecerte información sobre nuestros próximos eventos, "
        "cómo donar, o bien el contacto de alguno de nuestros líderes de ministerio. ¡Bendiciones!"
    )
    print(f"[BOT] Fallback message: {response_text}")
    # Here you would call acs_service.send_whatsapp_text_message(from_number, response_text)


def handle_donation_request(user_message: str, customer_name: str):
    """
    Handle WhatsApp donation intent: find relevant document and send template with real data.
    """
    metadata = find_similar_and_extract_fields(user_message, "donativo")
    if metadata and validate_template_params({"customer_name": customer_name, **metadata}):
        send_template_donation({"customer_name": customer_name, **metadata})
    else:
        send_fallback_message("No encontré la información solicitada para tu consulta.")


def handle_event_request(user_message: str, customer_name: str):
    """
    Handle WhatsApp event intent: find relevant document and send template with real data.
    """
    metadata = find_similar_and_extract_fields(user_message, "evento")
    if metadata and validate_template_params({"customer_name": customer_name, **metadata}):
        send_template_event({"customer_name": customer_name, **metadata})
    else:
        send_fallback_message("No encontré la información solicitada para tu consulta.")


def handle_contact_request(user_message: str, customer_name: str):
    """
    Handle WhatsApp contact intent: find relevant document and send template with real data.
    """
    metadata = find_similar_and_extract_fields(user_message, "contacto")
    if metadata and validate_template_params({"customer_name": customer_name, **metadata}):
        send_template_contact({"customer_name": customer_name, **metadata})
    else:
        send_fallback_message("No encontré la información solicitada para tu consulta.")


def generate_doc_id(blob_name: str) -> str:
    """
    Generate a unique document ID from the blob name.
    """
    import hashlib
    base = blob_name.rsplit('.', 1)[0]
    return f"{base}_{hashlib.md5(blob_name.encode()).hexdigest()[:8]}" 


def send_template_donation(payload: dict):
    """
    Simulate sending a WhatsApp donation template message with the given payload.
    """
    print(f"[BOT] Sending donation template with data: {json.dumps(payload, ensure_ascii=False)}")
    # Here you would call acs_service.send_whatsapp_template_message(...)

def send_template_event(payload: dict):
    """
    Simulate sending a WhatsApp event template message with the given payload.
    """
    print(f"[BOT] Sending event template with data: {json.dumps(payload, ensure_ascii=False)}")
    # Here you would call acs_service.send_whatsapp_template_message(...)

def send_template_contact(payload: dict):
    """
    Simulate sending a WhatsApp contact template message with the given payload.
    """
    print(f"[BOT] Sending contact template with data: {json.dumps(payload, ensure_ascii=False)}")
    # Here you would call acs_service.send_whatsapp_template_message(...) 