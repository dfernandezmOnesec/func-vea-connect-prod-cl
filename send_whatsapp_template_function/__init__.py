"""
HTTP trigger function to send WhatsApp template messages using ACS Advanced SDK.
"""
import logging
import json
import azure.functions as func
from datetime import datetime
from services.acs_service import acs_service

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP endpoint to send WhatsApp template messages.
    Expects JSON body with 'to_number', 'template_name', 'template_language', 'parameters'.
    """
    try:
        if req.method != "POST":
            return func.HttpResponse(
                json.dumps({"success": False, "message": "Method not allowed. Use POST."}),
                status_code=405,
                mimetype='application/json'
            )
        try:
            body = req.get_json()
        except Exception:
            return func.HttpResponse(
                json.dumps({"success": False, "message": "Invalid or empty JSON body."}),
                status_code=400,
                mimetype='application/json'
            )
        to_number = body.get("to_number")
        template_name = body.get("template_name")
        template_language = body.get("template_language", "es_MX")
        parameters = body.get("parameters", [])
        if not to_number or not template_name:
            return func.HttpResponse(
                json.dumps({"success": False, "message": "Missing required parameters: to_number, template_name"}),
                status_code=400,
                mimetype='application/json'
            )
        try:
            message_id = acs_service.send_whatsapp_template_message(
                to_number=to_number,
                template_name=template_name,
                template_language=template_language,
                parameters=parameters
            )
            return func.HttpResponse(
                json.dumps({
                    "success": True,
                    "message": "WhatsApp template message sent successfully.",
                    "to_number": to_number,
                    "template_name": template_name,
                    "message_id": message_id,
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=200,
                mimetype='application/json'
            )
        except Exception as e:
            logger.error(f"Error sending WhatsApp template message: {e}")
            return func.HttpResponse(
                json.dumps({"success": False, "message": "Failed to send WhatsApp template message.", "error": str(e)}),
                status_code=500,
                mimetype='application/json'
            )
    except Exception as e:
        logger.error(f"Internal error: {e}")
        return func.HttpResponse(
            json.dumps({"success": False, "message": "Internal server error.", "error": str(e)}),
            status_code=500,
            mimetype='application/json'
        ) 