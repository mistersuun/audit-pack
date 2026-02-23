"""
SD (Suivi des Dépôts) Parser for deposit variance tracking.

Parses daily deposit data from SD Excel files and maps employee names
to SetD personnel columns for automatic variance import.

SD file structure:
- 31 sheets (one per day: '1', '2', ..., '31')
- Each sheet has: DÉPARTEMENT, NOM, CDN/US, MONTANT, MONTANT VÉRIFIÉ, REMBOURSEMENT, VARIANCE
- Variance = MONTANT - MONTANT VÉRIFIÉ
"""

import re
from io import BytesIO
from utils.parsers.base_parser import BaseParser
from utils.sd_reader import SDReader
from utils.rj_mapper import SETD_PERSONNEL_COLUMNS


class SDParser(BaseParser):
    """
    Parse SD (Suivi des Dépôts) Excel file for a specific day.

    Extracts deposit entries, calculates variances, and maps employee names
    to SetD personnel columns for automatic variance export.
    """

    FIELD_MAPPINGS = {}  # Dynamic based on day and employees

    def __init__(self, file_bytes, filename=None, day=None, **kwargs):
        """
        Initialize SD parser.

        Args:
            file_bytes: SD Excel file bytes (BytesIO or bytes)
            filename: Optional filename for logging
            day: Target day (1-31) to parse. If None, will parse current audit day.
            **kwargs: Additional arguments (e.g., current_day from session)
        """
        super().__init__(file_bytes, filename)
        self.day = day
        self.sd_reader = None
        self.day_data = None
        self.entries = []
        self.matched_employees = []
        self.unmatched_names = []
        self.totals = {}
        self.setd_fillable = {}

    def parse(self):
        """
        Parse the SD file for the target day.

        Extracts entries, matches employee names to SetD columns,
        and builds variance fillable dictionary.
        """
        try:
            # Initialize SD reader
            if isinstance(self.file_bytes, bytes):
                file_bytes = BytesIO(self.file_bytes)
            else:
                file_bytes = self.file_bytes

            self.sd_reader = SDReader(file_bytes)

            # Get target day (default to current day if available)
            target_day = self.day
            if target_day is None:
                target_day = 1  # Fallback to day 1

            # Validate day
            if not 1 <= target_day <= 31:
                self.validation_errors.append(f"Invalid day: {target_day}")
                self._parsed = True
                self.confidence = 0.0
                return

            # Read day data
            self.day_data = self.sd_reader.read_day_data(target_day)
            self.entries = self.day_data.get('entries', [])

            # Get totals
            self.totals = self.sd_reader.get_totals_for_day(target_day)

            # Match employees and build fillable data
            self._match_employees()
            self._build_setd_fillable()

            # Calculate confidence based on match success
            self._calculate_confidence()

            # Build matched names detail dict
            matched_names = {}
            for m in self.matched_employees:
                matched_names[m['nom']] = {
                    'col': m['col_letter'],
                    'variance': m['variance'],
                    'match_type': 'fuzzy',
                }

            # Populate extracted data
            self.extracted_data = {
                'day': target_day,
                'date': self.day_data.get('date', ''),
                'total_entries': len(self.entries),
                'entries': self.entries,
                'totals': self.totals,
                'departments': self._group_by_department(),
                'matched_count': len(self.matched_employees),
                'unmatched_count': len(self.unmatched_names),
                'matched_names': matched_names,
                'unmatched_names': self.unmatched_names,
                'setd_fillable': self.setd_fillable,
            }

            self._parsed = True

        except Exception as e:
            self.validation_errors.append(f"Parse error: {str(e)}")
            self._parsed = True
            self.confidence = 0.0

    def validate(self):
        """
        Validate extracted data.

        Returns:
            True if no critical errors, False otherwise.
        """
        if not self._parsed:
            self.parse()

        # Check if parsing succeeded
        if self.validation_errors:
            return False

        # Check if we have entries
        if not self.entries:
            self.validation_warnings.append("No entries found for this day")

        # Warn if no matches
        if not self.matched_employees and self.entries:
            self.validation_warnings.append(
                f"No employee names matched to SetD columns ({len(self.entries)} entries)"
            )

        return len(self.validation_errors) == 0

    def get_setd_fillable(self, day=None):
        """
        Get SetD-ready fillable data for variance import.

        Returns:
            dict: {col_letter: variance_amount} ready for RJ writing
                  Example: {'AY': 125.50, 'CU': -45.75}
        """
        if not self._parsed:
            self.parse()

        return self.setd_fillable

    def _match_employees(self):
        """
        Match SD employee names to SetD personnel columns.

        Uses fuzzy matching strategy:
        1. Exact match (case-insensitive)
        2. Last name match
        3. First name match
        4. Partial substring match
        """
        # Build normalized SetD mapping for faster lookups
        setd_norm = self._build_normalized_setd_mapping()

        for entry in self.entries:
            nom = entry.get('nom', '').strip()
            variance = entry.get('variance', 0)

            if not nom or variance == 0:
                continue

            # Try to match
            col_letter = self._match_name(nom, setd_norm)

            if col_letter:
                self.matched_employees.append({
                    'nom': nom,
                    'variance': variance,
                    'col_letter': col_letter,
                })
            else:
                if nom not in self.unmatched_names:
                    self.unmatched_names.append(nom)

    def _build_normalized_setd_mapping(self):
        """
        Build a normalized version of SETD_PERSONNEL_COLUMNS for fuzzy matching.

        Returns:
            dict: {
                'exact': {normalized_name: (original_name, col_letter)},
                'last_name': {last_name: [(original_name, col_letter), ...]},
                'first_name': {first_name: [(original_name, col_letter), ...]},
                'full_names': [(normalized_name, original_name, col_letter), ...]
            }
        """
        mapping = {
            'exact': {},
            'last_name': {},
            'first_name': {},
            'full_names': [],
        }

        for original_name, col_letter in SETD_PERSONNEL_COLUMNS.items():
            norm_name = self._normalize_name(original_name)

            # Exact normalized match
            mapping['exact'][norm_name] = (original_name, col_letter)

            # Last name index
            parts = original_name.split()
            if parts:
                last_name = self._normalize_name(parts[-1])
                if last_name not in mapping['last_name']:
                    mapping['last_name'][last_name] = []
                mapping['last_name'][last_name].append((original_name, col_letter))

            # First name index
            if len(parts) > 1:
                first_name = self._normalize_name(parts[0])
                if first_name not in mapping['first_name']:
                    mapping['first_name'][first_name] = []
                mapping['first_name'][first_name].append((original_name, col_letter))

            # Full names list for substring matching
            mapping['full_names'].append((norm_name, original_name, col_letter))

        return mapping

    def _match_name(self, sd_name, setd_norm):
        """
        Match a single SD name to SetD column.

        Args:
            sd_name: Name from SD file
            setd_norm: Normalized SetD mapping from _build_normalized_setd_mapping()

        Returns:
            str: Column letter if matched, None otherwise
        """
        norm_sd = self._normalize_name(sd_name)

        # Strategy 1: Exact match
        if norm_sd in setd_norm['exact']:
            return setd_norm['exact'][norm_sd][1]

        # Strategy 2: Last name match (prefer if only one match)
        parts = norm_sd.split()
        if parts:
            last_name = parts[-1]
            if last_name in setd_norm['last_name']:
                candidates = setd_norm['last_name'][last_name]
                if len(candidates) == 1:
                    return candidates[0][1]

        # Strategy 3: First name match (if only one match)
        if len(parts) > 1:
            first_name = parts[0]
            if first_name in setd_norm['first_name']:
                candidates = setd_norm['first_name'][first_name]
                if len(candidates) == 1:
                    return candidates[0][1]

        # Strategy 4: Partial substring match
        norm_sd_lower = norm_sd.lower()
        for full_norm, orig_name, col in setd_norm['full_names']:
            # Check if SD name is contained in SetD name or vice versa
            if norm_sd_lower in full_norm.lower() or full_norm.lower() in norm_sd_lower:
                return col

        return None

    def _normalize_name(self, name):
        """
        Normalize a name for comparison.

        - Lowercase
        - Strip whitespace
        - Remove accents (é→e, ç→c, etc.)
        - Remove special characters
        """
        if not name:
            return ""

        # Lowercase and strip
        name = name.lower().strip()

        # Remove accents using simple mapping
        accent_map = {
            'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a', 'ã': 'a', 'å': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'ô': 'o', 'ö': 'o', 'õ': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ý': 'y', 'ÿ': 'y',
            'ñ': 'n',
            'ç': 'c',
        }

        normalized = ""
        for char in name:
            normalized += accent_map.get(char, char)

        # Remove extra spaces and special characters (keep letters, numbers, spaces, hyphens)
        normalized = re.sub(r'[^a-z0-9\s\-]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def _group_by_department(self):
        """Group entries by department with subtotals."""
        departments = {}
        for entry in self.entries:
            dept = entry.get('departement', 'INCONNU') or 'INCONNU'
            if dept not in departments:
                departments[dept] = {'entries': 0, 'montant': 0, 'variance': 0}
            departments[dept]['entries'] += 1
            departments[dept]['montant'] += entry.get('montant', 0)
            var = entry.get('variance', 0)
            if var is not None:
                departments[dept]['variance'] += var
        return departments

    def _build_setd_fillable(self):
        """
        Build the SetD fillable dictionary from matched employees.

        Format: {col_letter: total_variance_for_column}
        """
        self.setd_fillable = {}

        for match in self.matched_employees:
            col = match['col_letter']
            variance = match['variance']

            # Accumulate variances for each column (in case multiple entries per employee)
            if col not in self.setd_fillable:
                self.setd_fillable[col] = 0
            self.setd_fillable[col] += variance

    def _calculate_confidence(self):
        """
        Calculate confidence score based on match success.

        Score factors:
        - Percentage of entries with non-zero variance that were matched
        - Whether unmatched names exist
        """
        if not self.entries:
            self.confidence = 0.0
            return

        # Count entries with variance
        variance_entries = [e for e in self.entries if e.get('variance', 0) != 0]

        if not variance_entries:
            self.confidence = 0.5  # No variances to match
            return

        # Match rate
        match_rate = len(self.matched_employees) / len(variance_entries)

        # Adjust for unmatched names
        unmatched_penalty = len(self.unmatched_names) * 0.05

        self.confidence = max(0.0, min(1.0, match_rate - unmatched_penalty))


# Utility function for route usage
def get_setd_fillable_from_sd(sd_file_bytes, day):
    """
    Convenience function to get SetD fillable data from SD file.

    Args:
        sd_file_bytes: SD Excel file as bytes or BytesIO
        day: Target day (1-31)

    Returns:
        dict: {col_letter: variance_amount}

    Raises:
        Exception: If parsing fails
    """
    parser = SDParser(sd_file_bytes, day=day)
    result = parser.get_result()

    if not result['success']:
        raise Exception(f"SD parsing failed: {result['errors']}")

    return result['data'].get('setd_fillable', {})
