import re
from typing import Dict

class EventoParser:
    """
    Parser for event documents. Extracts event name, date, and location from text.
    """
    @staticmethod
    def parse(text: str) -> Dict:
        return {
            "event_name": EventoParser._extract(r'Evento\s*:\s*(.+)', text),
            "event_date": EventoParser._extract(r'Fecha\s*:\s*(.+)', text),
            "event_location": EventoParser._extract(r'Lugar\s*:\s*(.+)', text)
        }

    @staticmethod
    def _extract(pattern: str, text: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else "" 