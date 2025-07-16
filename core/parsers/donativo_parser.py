import re
from typing import Dict

class DonativoParser:
    """
    Parser for donation documents. Extracts bank, account, beneficiary, CLABE, contact name, and contact phone from text.
    """
    @staticmethod
    def parse(text: str) -> Dict:
        return {
            "bank_name": DonativoParser._extract(r'Banco\s*:\s*(.+)', text),
            "account_number": DonativoParser._extract(r'Cuenta\s*:\s*(\d+)', text),
            "beneficiary_name": DonativoParser._extract(r'Beneficiario\s*:\s*(.+)', text),
            "clabe_number": DonativoParser._extract(r'CLABE\s*:\s*(\d+)', text),
            "contact_name": DonativoParser._extract(r'Contacto\s*:\s*(.+)', text),
            "contact_phone": DonativoParser._extract(r'Contacto.*(\+?\d{10,})', text)
        }

    @staticmethod
    def _extract(pattern: str, text: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else "" 