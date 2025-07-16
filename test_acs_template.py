from services.acs_service import acs_service

if __name__ == "__main__":
    to_number = "+525519387611"  # Tu número real
    template_name = "vea_event_info"
    template_language = "es_MX"
    parameters = [
        "Juan Pérez",           # customer_name
        "Retiro Espiritual",    # event_name
        "20 de julio, 2024",    # event_date
        "Parroquia San Juan"    # event_location
    ]

    try:
        message_id = acs_service.send_whatsapp_template_message(
            to_number=to_number,
            template_name=template_name,
            template_language=template_language,
            parameters=parameters
        )
        print(f"Mensaje enviado correctamente. message_id: {message_id}")
    except Exception as e:
        print(f"Error al enviar mensaje: {e}") 