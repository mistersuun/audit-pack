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
