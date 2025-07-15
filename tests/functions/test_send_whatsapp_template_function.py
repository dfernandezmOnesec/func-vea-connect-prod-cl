import json
import pytest
from unittest.mock import Mock, patch
import azure.functions as func
from send_whatsapp_template_function import main

class TestSendWhatsappTemplateFunction:
    def setup_method(self):
        self.mock_request = Mock(spec=func.HttpRequest)
        self.mock_request.method = "POST"

    def test_send_template_success(self):
        self.mock_request.get_json.return_value = {
            "to_number": "+521234567890",
            "template_name": "vea_info_donativos",
            "template_language": "es_MX",
            "parameters": ["Juan"]
        }
        with patch('send_whatsapp_template_function.acs_service') as mock_acs_service:
            mock_acs_service.send_whatsapp_template_message.return_value = "msg-456"
            response = main(self.mock_request)
            assert response.status_code == 200
            data = json.loads(response.get_body().decode())
            assert data["success"] is True
            assert data["to_number"] == "+521234567890"
            assert data["template_name"] == "vea_info_donativos"
            assert data["message_id"] == "msg-456"

    def test_missing_parameters(self):
        self.mock_request.get_json.return_value = {"to_number": "+521234567890"}
        response = main(self.mock_request)
        assert response.status_code == 400
        data = json.loads(response.get_body().decode())
        assert data["success"] is False
        assert "Missing required parameters" in data["message"]

    def test_invalid_method(self):
        self.mock_request.method = "GET"
        response = main(self.mock_request)
        assert response.status_code == 405
        data = json.loads(response.get_body().decode())
        assert data["success"] is False
        assert "Method not allowed" in data["message"]

    def test_internal_error(self):
        self.mock_request.get_json.side_effect = Exception("fail json")
        response = main(self.mock_request)
        assert response.status_code == 400 or response.status_code == 500
        data = json.loads(response.get_body().decode())
        assert data["success"] is False 