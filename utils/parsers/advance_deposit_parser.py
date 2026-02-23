"""
Advance Deposit Parser.

Extracts the Advance Deposit Balance from the LightSpeed PMS report.
This is a single value (Deposit on Hand) used in:
1. GEAC/UX sheet Row 44 (B44 = balance, J44 = applied)
2. Jour sheet Column D formula: D = -(New Balance) - Deposit on Hand

In most cases, this value is entered manually in the Import Auto tab's
"Deposit on Hand ($)" field. The parser exists for when the user uploads
the actual Advance Deposit Balance Sheet PDF from LightSpeed.
"""

import re
from utils.parsers.base_parser import BaseParser


class AdvanceDepositParser(BaseParser):
    """
    Parse Advance Deposit Balance Sheet from LightSpeed PMS.

    Target sheet: geac_ux (Row 44)

    Expected data:
    - adv_deposit: Advance Deposit Balance (B44)
    - adv_deposit_applied: Amount Applied Today (J44)
    - deposit_on_hand: Net deposit on hand (for Jour Column D)
    """

    FIELD_MAPPINGS = {
        'adv_deposit': 'B44',
        'adv_deposit_applied': 'J44',
    }

    def parse(self):
        """
        Parse Advance Deposit Balance Sheet PDF.

        The PDF typically contains a summary with:
        - "Balance Forward" or "Previous Balance"
        - "Deposits Received"
        - "Deposits Applied"
        - "Ending Balance" / "Deposit on Hand"
        """
        try:
            text = self._extract_pdf_text()

            if not text:
                self.validation_warnings.append(
                    "Impossible d'extraire le texte du PDF. "
                    "Entrez le montant manuellement dans le champ 'Deposit on Hand'."
                )
                self.confidence = 0.0
                self._parsed = True
                return

            self._extract_amounts(text)
            self.confidence = self._calculate_confidence()

        except Exception as e:
            self.validation_warnings.append(
                f"Erreur lecture PDF: {str(e)}. "
                "Entrez le montant manuellement."
            )
            self.confidence = 0.0

        self._parsed = True

    def _extract_pdf_text(self):
        """Extract text from PDF bytes using pdfplumber."""
        try:
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(self.file_bytes)) as pdf:
                text = ''
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
                return text
        except ImportError:
            self.validation_warnings.append(
                "Module pdfplumber non disponible. "
                "Entrez le montant manuellement."
            )
            return ''
        except Exception:
            return ''

    def _extract_amounts(self, text):
        """Extract deposit amounts from PDF text."""
        # Pattern: dollar amounts possibly with commas
        money_pattern = r'[\$]?\s*([\d,]+\.?\d*)'

        # Try to find "Ending Balance" or "Deposit on Hand" or "Balance"
        patterns = [
            (r'(?:ending\s+balance|deposit\s+on\s+hand|solde\s+final)[:\s]*' + money_pattern, 'adv_deposit'),
            (r'(?:deposits?\s+applied|d[eé]p[oô]ts?\s+appliqu[eé]s?)[:\s]*' + money_pattern, 'adv_deposit_applied'),
            (r'(?:balance\s+forward|previous\s+balance|solde\s+pr[eé]c[eé]dent)[:\s]*' + money_pattern, 'balance_forward'),
            (r'(?:deposits?\s+received|d[eé]p[oô]ts?\s+re[cç]us?)[:\s]*' + money_pattern, 'deposits_received'),
        ]

        text_lower = text.lower()
        for pattern, field in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    self.extracted_data[field] = value
                except (ValueError, IndexError):
                    pass

        # Compute deposit_on_hand if we have the main balance
        if 'adv_deposit' in self.extracted_data:
            self.extracted_data['deposit_on_hand'] = self.extracted_data['adv_deposit']

    def _calculate_confidence(self):
        """Calculate confidence based on what we found."""
        if 'adv_deposit' in self.extracted_data:
            return 0.85
        if 'balance_forward' in self.extracted_data:
            return 0.5
        if self.extracted_data:
            return 0.3
        return 0.0

    def validate(self):
        """Validate extracted data."""
        if not self.extracted_data:
            self.validation_warnings.append(
                "Aucune donnée extraite. Entrez le montant dans 'Deposit on Hand' manuellement."
            )
            return True  # Not an error — manual input is the expected fallback

        deposit = self.extracted_data.get('adv_deposit', 0)
        if deposit and deposit < 0:
            self.validation_warnings.append(
                f"Deposit on Hand négatif ({deposit}) — vérifiez la valeur"
            )

        return True
