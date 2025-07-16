import re
from typing import Dict

class ContactoParser:
    """
    Parser for contact documents. Extracts ministry name, contact name, and contact phone from text.
    """
    @staticmethod
    def parse(text: str) -> Dict:
        return {
            "ministry_name": ContactoParser._extract(r'Ministerio\s*:\s*(.+)', text),
            "contact_name": ContactoParser._extract(r'Contacto\s*:\s*(.+)', text),
            "contact_phone": ContactoParser._extract(r'Contacto.*(\+?\d{10,})', text)
        }

    @staticmethod
    def _extract(pattern: str, text: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else "" 