"""
Document parsing framework for RJ auto-fill.
Parsers extract structured data from PDFs and Excel files,
which is then used to pre-fill RJ input sheets.
"""

from utils.parsers.base_parser import BaseParser
from utils.parsers.daily_revenue_parser import DailyRevenueParser
from utils.parsers.advance_deposit_parser import AdvanceDepositParser
from utils.parsers.freedompay_parser import FreedomPayParser
from utils.parsers.hp_excel_parser import HPExcelParser
from utils.parsers.ar_summary_parser import ARSummaryParser
from utils.parsers.sales_journal_parser import SalesJournalParser
from utils.parsers.sd_parser import SDParser
from utils.parsers.market_segment_parser import MarketSegmentParser
from utils.parsers.cashier_summary_parser import CashierSummaryParser
from utils.parsers.transaction_summary_parser import TransactionSummaryParser
from utils.parsers.recap_text_parser import RecapTextParser
from utils.parsers.house_totals_parser import HouseTotalsParser
from utils.parsers.debourse_parser import DebourseParser


class ParserFactory:
    """Factory to instantiate the correct parser by document type."""

    PARSERS = {
        'daily_revenue': DailyRevenueParser,
        'advance_deposit': AdvanceDepositParser,
        'freedompay': FreedomPayParser,
        'hp_excel': HPExcelParser,
        'ar_summary': ARSummaryParser,
        'sales_journal': SalesJournalParser,
        'sd_deposit': SDParser,
        'market_segment': MarketSegmentParser,
        'cashier_summary': CashierSummaryParser,
        'transaction_summary': TransactionSummaryParser,
        'recap_text': RecapTextParser,
        'house_totals': HouseTotalsParser,
        'debourse': DebourseParser,
    }

    ACCEPTED_EXTENSIONS = {
        'daily_revenue': ['.pdf'],
        'advance_deposit': ['.pdf'],
        'freedompay': ['.xls', '.xlsx'],
        'hp_excel': ['.xls', '.xlsx', '.xlsm'],
        'ar_summary': ['.pdf'],
        'sales_journal': ['.rtf', '.txt'],
        'sd_deposit': ['.xls', '.xlsx'],
        'market_segment': ['.pdf'],
        'cashier_summary': ['.pdf', '.txt'],
        'transaction_summary': ['.xlsx'],
        'recap_text': ['.txt'],
        'house_totals': ['.txt'],
        'debourse': ['.pdf', '.dat'],  # .dat is a PDF with wrong extension
    }

    # Auto-detection rules: map filename patterns to parser types
    FILENAME_PATTERNS = [
        # Order matters — more specific patterns first.
        # house_totals and 90.2/debourse BEFORE generic 'house' to catch them.
        ('house_totals', 'house_totals'),
        ('house_90_2', 'debourse'),
        ('90_2', 'debourse'),
        ('90.2', 'debourse'),
        ('debourse', 'debourse'),
        ('daily_rev', 'daily_revenue'),
        ('dlyrev', 'daily_revenue'),
        ('advance_deposit', 'advance_deposit'),
        ('adv_dep', 'advance_deposit'),
        ('deposit_balance', 'advance_deposit'),
        ('market_segment', 'market_segment'),
        ('mktsegprd', 'market_segment'),
        ('transactionsummary', 'transaction_summary'),
        ('transaction_summary', 'transaction_summary'),
        ('freedompay', 'freedompay'),
        ('fusebox', 'transaction_summary'),
        ('cashier_cashout', 'cashier_summary'),
        ('cashier_details', None),  # informational only, no parser yet
        ('4_28_cashier', None),  # F&B cashier details, no parser yet
        ('daily_cashout', 'cashier_summary'),
        ('cshsum', 'cashier_summary'),
        ('cshout', 'cashier_summary'),
        ('sales_journal', 'sales_journal'),
        # AR Summary — multiple naming conventions used by hotels
        ('ar_summary', 'ar_summary'),
        ('arsummary', 'ar_summary'),
        ('ar summary', 'ar_summary'),
        ('arsum', 'ar_summary'),
        ('receivable', 'ar_summary'),
        ('recevable', 'ar_summary'),
        ('recap', 'recap_text'),
        ('guest_ledger', None),  # informational only
        ('guestledger', None),
        ('chambres_pannes', None),  # informational only
        ('quasimodo', None),  # reconciliation sheet — handled via /api/rj/quasimodo
        ('quasi', None),
        ('hp', 'hp_excel'),
        ('pod0', None),  # POD payroll — informational
        ('dbr', None),  # DBRS master — informational
        ('rj ', None),  # RJ workbook — handled separately
        ('sd.', 'sd_deposit'),
        ('sd ', 'sd_deposit'),
    ]

    @classmethod
    def detect_type(cls, filename):
        """Auto-detect parser type from filename.

        Returns:
            doc_type string, or None if not parseable.
        """
        if not filename:
            return None
        fn_lower = filename.lower()
        for pattern, doc_type in cls.FILENAME_PATTERNS:
            if pattern in fn_lower:
                return doc_type
        return None

    @classmethod
    def create(cls, doc_type, file_bytes, filename=None, **kwargs):
        parser_class = cls.PARSERS.get(doc_type)
        if not parser_class:
            raise ValueError(f"Type de document inconnu: {doc_type}")
        # Pass extra kwargs (e.g., day=23 for HPExcelParser)
        return parser_class(file_bytes, filename=filename, **kwargs)

    @classmethod
    def get_supported_types(cls):
        return list(cls.PARSERS.keys())

    @classmethod
    def get_type_info(cls):
        return {
            'daily_revenue': {
                'label_fr': 'Revenu Journalier (PDF)',
                'description_fr': 'Rapport Daily Revenue de LightSpeed — pages 5-6',
                'target_sheet': 'Recap',
                'extensions': ['.pdf'],
            },
            'advance_deposit': {
                'label_fr': 'Dépôt en avance (PDF)',
                'description_fr': 'Rapport Advance Deposit Balance de LightSpeed',
                'target_sheet': 'geac_ux',
                'extensions': ['.pdf'],
            },
            'freedompay': {
                'label_fr': 'FreedomPay (Excel)',
                'description_fr': 'Export de réconciliation bancaire FreedomPay/Fusebox',
                'target_sheet': 'geac_ux',
                'extensions': ['.xls', '.xlsx'],
            },
            'hp_excel': {
                'label_fr': 'HP Admin (Excel)',
                'description_fr': 'Fichier HP-ADMIN promotions/administration',
                'target_sheet': 'jour',
                'extensions': ['.xls', '.xlsx', '.xlsm'],
            },
            'ar_summary': {
                'label_fr': 'AR Summary (PDF)',
                'description_fr': 'Rapport AR Summary du système GEAC/UX PMS',
                'target_sheet': 'geac_ux',
                'extensions': ['.pdf'],
            },
            'sales_journal': {
                'label_fr': 'Sales Journal (RTF/TXT)',
                'description_fr': 'Rapport Sales Journal de Positouch/LightSpeed POS',
                'target_sheet': 'Jour',
                'extensions': ['.rtf', '.txt'],
            },
            'sd_deposit': {
                'label_fr': 'Suivi des Dépôts (SD Excel)',
                'description_fr': 'Fichier SD avec variances journalières des dépôts',
                'target_sheet': 'SetD',
                'extensions': ['.xls', '.xlsx'],
            },
            'market_segment': {
                'label_fr': 'Market Segment (PDF)',
                'description_fr': 'Rapport Market Segment Production (mktsegprd) — DBRS segments',
                'target_sheet': 'DBRS',
                'extensions': ['.pdf'],
            },
            'cashier_summary': {
                'label_fr': 'Cashier Summary (PDF)',
                'description_fr': 'Rapport Daily Cashout/Cashier Cashout — GEAC cashout par carte',
                'target_sheet': 'GEAC',
                'extensions': ['.pdf'],
            },
            'transaction_summary': {
                'label_fr': 'Transactions Cartes (Excel)',
                'description_fr': 'FreedomPay TransactionSummarybyCardType — Transelect réception',
                'target_sheet': 'Transelect',
                'extensions': ['.xlsx'],
            },
            'recap_text': {
                'label_fr': 'Recap Serveurs (TXT)',
                'description_fr': 'Rapport Recap par serveur — Transelect restaurant + cash',
                'target_sheet': 'Recap',
                'extensions': ['.txt'],
            },
            'house_totals': {
                'label_fr': 'House Totals (TXT)',
                'description_fr': 'Sales Journal Report for Entire house — PAYMENT TOTALS (Comptant Positouch + Remb Gratuité)',
                'target_sheet': 'Recap',
                'extensions': ['.txt'],
            },
            'debourse': {
                'label_fr': 'Débourse 90.2 (PDF)',
                'description_fr': 'Cashier Detail Dept 90 Sub 90.2 — Remboursement Serveur + Due Back Réception',
                'target_sheet': 'Recap',
                'extensions': ['.pdf', '.dat'],
            },
        }
