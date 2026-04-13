"""Abstract base class for all document parsers."""

from abc import ABC, abstractmethod
from datetime import datetime


class BaseParser(ABC):
    """
    Base class for document parsers.

    All parsers follow the same pattern:
    1. Receive file bytes
    2. Parse/extract structured data
    3. Validate extracted data
    4. Return result with confidence score
    """

    # Subclasses override this to define what fields they extract
    # and where those fields map to in the RJ
    FIELD_MAPPINGS = {}

    def __init__(self, file_bytes, filename=None, **kwargs):
        self.file_bytes = file_bytes
        self.filename = filename
        self.extracted_data = {}
        self.validation_errors = []
        self.validation_warnings = []
        self.confidence = 0.0
        self._parsed = False

    @abstractmethod
    def parse(self):
        """
        Parse the document and populate self.extracted_data.
        Must set self._parsed = True when done.
        Must set self.confidence (0.0 - 1.0).
        """
        pass

    @abstractmethod
    def validate(self):
        """
        Validate extracted data.
        Populate self.validation_errors (critical) and self.validation_warnings (non-critical).
        Returns True if no critical errors.
        """
        pass

    def get_result(self):
        """Parse, validate, and return complete result."""
        if not self._parsed:
            self.parse()

        is_valid = self.validate()

        return {
            'success': is_valid,
            'data': self.extracted_data,
            'field_mappings': self.FIELD_MAPPINGS,
            'confidence': self.confidence,
            'errors': self.validation_errors,
            'warnings': self.validation_warnings,
            'filename': self.filename,
            'parsed_at': datetime.utcnow().isoformat(),
        }

    def get_fillable_data(self):
        """
        Return only the data that maps to RJ cells.
        Format: {cell_reference: value} e.g. {'B6': 1234.56}
        """
        if not self._parsed:
            self.parse()

        fillable = {}
        for field_key, cell_ref in self.FIELD_MAPPINGS.items():
            if field_key in self.extracted_data and self.extracted_data[field_key] is not None:
                fillable[cell_ref] = self.extracted_data[field_key]

        return fillable

    def _safe_float(self, value, default=0.0):
        """Safely convert value to float."""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                # Handle currency formatting: "$1,234.56" -> 1234.56
                cleaned = value.replace('$', '').replace(',', '').replace(' ', '').strip()
                if cleaned == '' or cleaned == '-':
                    return default
                return float(cleaned)
            return float(value)
        except (ValueError, TypeError):
            return default

    def _decode_bytes(self):
        """Decode self.file_bytes as text, falling back across common encodings.

        Galaxy/Lightspeed text dumps are emitted in CP1252 or latin-1; PDFs
        exported to text sometimes land as utf-8. Tries each in order and
        ultimately falls back to utf-8 with replacement characters so the
        parser never raises on a single bad byte.
        """
        raw = self.file_bytes
        if isinstance(raw, str):
            return raw
        for encoding in ('utf-8', 'latin-1', 'cp1252'):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw.decode('utf-8', errors='replace')

    def _extract_pdf_text(self):
        """Extract concatenated text from all pages of a PDF in self.file_bytes.

        Returns '' (not None) and appends a validation error if pdfplumber is
        missing or the PDF can't be opened. Accepts raw bytes or a BytesIO.
        """
        try:
            import pdfplumber
        except ImportError:
            self.validation_errors.append("pdfplumber not installed")
            return ""
        import io
        buf = self.file_bytes
        if isinstance(buf, bytes):
            buf = io.BytesIO(buf)
        try:
            with pdfplumber.open(buf) as pdf:
                return "\n".join((page.extract_text() or "") for page in pdf.pages)
        except Exception as e:
            self.validation_errors.append(f"PDF extraction failed: {e}")
            return ""
