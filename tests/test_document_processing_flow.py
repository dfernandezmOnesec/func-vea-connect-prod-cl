import pytest
import json
from core.document_processing_flow import (
    create_document, process_and_embed_document, find_similar_and_extract_fields, delete_document, generate_doc_id
)

class DummyBlobService:
    """Mock Azure Blob Service for testing."""
    def __init__(self):
        self.storage = {}
    def upload_text(self, blob_name, text, metadata=None):
        self.storage[blob_name] = text
        return True
    def download_text(self, blob_name):
        return self.storage.get(blob_name, None)
    def delete_blob(self, blob_name):
        if blob_name in self.storage:
            del self.storage[blob_name]
            return True
        return False

class DummyRedisService:
    """Mock Redis Service for testing."""
    def __init__(self):
        self.cache = {}
        self.client = self
    def set_cache(self, key, value, ttl=None):
        self.cache[key] = value
        return True
    def get_cache(self, key):
        return self.cache.get(key, None)
    def delete_cache(self, key):
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    def scan_iter(self, pattern):
        # Only supports 'doc:*' pattern
        for key in self.cache:
            if key.startswith('doc:'):
                yield key

@pytest.fixture(autouse=True)
def patch_services(monkeypatch):
    # Patch services in the correct module namespace
    import core.document_processing_flow as docflow
    dummy_blob = DummyBlobService()
    dummy_redis = DummyRedisService()
    monkeypatch.setattr(docflow, 'azure_blob_service', dummy_blob)
    monkeypatch.setattr(docflow, 'redis_service', dummy_redis)
    yield


def test_end_to_end_document_flow():
    """
    End-to-end test: create, search, and delete a document using the processing flow.
    """
    # 1. Create document
    file_name = "donativo_test.txt"
    file_blob = "Banco: Banamex\nCuenta: 987654321\nBeneficiario: Iglesia VEA\nCLABE: 123456789012345678\nContacto: Juan Perez\nContacto: +521234567890".encode('utf-8')
    document_data = {"file_name": file_name}
    category = "donativo"
    create_document(document_data, file_blob, category)
    doc_id = generate_doc_id(file_name)
    # 2. Search for the document
    user_message = "Quiero hacer un donativo a Banamex"
    metadata = find_similar_and_extract_fields(user_message, category)
    assert metadata is not None, "Metadata should be found for the created document"
    assert metadata["bank_name"] == "Banamex"
    assert metadata["beneficiary_name"] == "Iglesia VEA"
    # 3. Delete the document
    delete_document(doc_id, file_name)
    # 4. Verify deletion
    import core.document_processing_flow as docflow
    assert docflow.redis_service.get_cache(f"doc:{doc_id}") is None, "Document should be deleted from Redis"
    assert docflow.azure_blob_service.download_text(file_name) is None, "Document should be deleted from Storage" 