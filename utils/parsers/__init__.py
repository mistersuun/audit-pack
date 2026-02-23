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
    }

    ACCEPTED_EXTENSIONS = {
        'daily_revenue': ['.pdf'],
        'advance_deposit': ['.pdf'],
        'freedompay': ['.xls', '.xlsx'],
        'hp_excel': ['.xls', '.xlsx', '.xlsm'],
        'ar_summary': ['.pdf'],
        'sales_journal': ['.rtf', '.txt'],
        'sd_deposit': ['.xls', '.xlsx'],
    }

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
        }
