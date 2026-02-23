"""Tests for Import Excel → NAS and Export NAS → Excel workflows."""

import io
import json
import os
import xlrd
import olefile
import pytest
from tests.conftest import RJ_07_PATH, DAILY_REV_PDF, SALES_JOURNAL_RTF, AR_SUMMARY_PDF


class TestImportExcel:
    """Test POST /api/rj/native/import/excel endpoint."""

    def test_import_creates_next_day_session(self, client, fresh_db):
        with open(RJ_07_PATH, 'rb') as f:
            resp = client.post('/api/rj/native/import/excel',
                               data={'rj_file': (f, 'Rj 07-02-2026.xls')},
                               content_type='multipart/form-data')
        d = resp.get_json()
        assert d['success'] is True
        assert d['new_date'] == '2026-02-08'
        assert d['imported_from'] == '2026-02-07'

    def test_import_populates_fields(self, client, fresh_db):
        with open(RJ_07_PATH, 'rb') as f:
            resp = client.post('/api/rj/native/import/excel',
                               data={'rj_file': (f, 'Rj 07-02-2026.xls')},
                               content_type='multipart/form-data')
        d = resp.get_json()
        summary = d['summary']
        assert summary['total_fields'] > 50
        assert 'recap' in summary['sections']
        assert 'transelect' in summary['sections']
        assert 'geac' in summary['sections']
        assert 'dueback' in summary['sections']
        assert 'jour' in summary['sections']

    def test_import_dueback_no_carry(self, client, fresh_db):
        """Emery, Nikoleta, Thaneekan, Manolo, Cindy should have previous=0."""
        with open(RJ_07_PATH, 'rb') as f:
            resp = client.post('/api/rj/native/import/excel',
                               data={'rj_file': (f, 'Rj 07-02-2026.xls')},
                               content_type='multipart/form-data')
        d = resp.get_json()
        session_data = d['session']
        dueback = session_data.get('dueback_entries', [])
        if isinstance(dueback, str):
            dueback = json.loads(dueback)

        blocked_names = ['emery', 'nikoleta', 'thaneekan', 'manolo', 'cindy']
        for entry in dueback:
            name = entry.get('name', '').lower()
            if any(b in name for b in blocked_names):
                assert entry.get('previous', 0) == 0, \
                    f"{entry['name']} should have previous=0 (no-carry rule)"

    def test_import_no_file_returns_400(self, client, fresh_db):
        resp = client.post('/api/rj/native/import/excel',
                           data={},
                           content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_import_returns_session_data(self, client, fresh_db):
        with open(RJ_07_PATH, 'rb') as f:
            resp = client.post('/api/rj/native/import/excel',
                               data={'rj_file': (f, 'Rj 07-02-2026.xls')},
                               content_type='multipart/form-data')
        d = resp.get_json()
        assert 'session' in d
        assert d['session']['status'] in ('draft', 'in_progress')


class TestExportExcel:
    """Test GET /api/rj/native/export/rj-filled/<date> endpoint."""

    def test_export_returns_xls(self, client, fresh_db):
        # First import to create a session and store the file
        with open(RJ_07_PATH, 'rb') as f:
            client.post('/api/rj/native/import/excel',
                        data={'rj_file': (f, 'Rj 07-02-2026.xls')},
                        content_type='multipart/form-data')

        resp = client.get('/api/rj/native/export/rj-filled/2026-02-08')
        assert resp.status_code == 200
        assert resp.content_type == 'application/vnd.ms-excel'
        assert len(resp.data) > 100000

    def test_export_preserves_vba(self, client, fresh_db):
        with open(RJ_07_PATH, 'rb') as f:
            client.post('/api/rj/native/import/excel',
                        data={'rj_file': (f, 'Rj 07-02-2026.xls')},
                        content_type='multipart/form-data')

        resp = client.get('/api/rj/native/export/rj-filled/2026-02-08')
        of = olefile.OleFileIO(io.BytesIO(resp.data))
        vba_count = len([e for e in of.listdir()
                         if '_VBA_PROJECT_CUR' in '/'.join(e)])
        of.close()
        assert vba_count >= 100  # Should have ~116 VBA streams

    def test_export_updates_controle_date(self, client, fresh_db):
        with open(RJ_07_PATH, 'rb') as f:
            client.post('/api/rj/native/import/excel',
                        data={'rj_file': (f, 'Rj 07-02-2026.xls')},
                        content_type='multipart/form-data')

        resp = client.get('/api/rj/native/export/rj-filled/2026-02-08')
        rb = xlrd.open_workbook(file_contents=resp.data, formatting_info=True)
        ctrl = rb.sheet_by_name('controle')
        assert ctrl.cell_value(2, 1) == 8   # day
        assert ctrl.cell_value(3, 1) == 2   # month
        assert ctrl.cell_value(4, 1) == 2026  # year

    def test_export_invalid_date_returns_400(self, client, fresh_db):
        resp = client.get('/api/rj/native/export/rj-filled/not-a-date')
        assert resp.status_code == 400

    def test_export_missing_session_returns_404(self, client, fresh_db):
        resp = client.get('/api/rj/native/export/rj-filled/2099-01-01')
        assert resp.status_code == 404


class TestParseAndFill:
    """Test POST /api/rj/native/parse-and-fill endpoint."""

    def _setup_session(self, client):
        with open(RJ_07_PATH, 'rb') as f:
            client.post('/api/rj/native/import/excel',
                        data={'rj_file': (f, 'Rj 07-02-2026.xls')},
                        content_type='multipart/form-data')

    def test_parse_daily_revenue(self, client, fresh_db):
        if not os.path.exists(DAILY_REV_PDF):
            pytest.skip("Daily Revenue PDF not available")
        self._setup_session(client)

        with open(DAILY_REV_PDF, 'rb') as f:
            resp = client.post('/api/rj/native/parse-and-fill',
                               data={'file': (f, 'Daily_Rev.pdf'),
                                     'doc_type': 'daily_revenue',
                                     'date': '2026-02-08'},
                               content_type='multipart/form-data')
        d = resp.get_json()
        assert d['success'] is True
        assert d['fields_filled'] > 10
        assert 'jour' in d['sections_updated']

    def test_parse_sales_journal(self, client, fresh_db):
        if not os.path.exists(SALES_JOURNAL_RTF):
            pytest.skip("Sales Journal RTF not available")
        self._setup_session(client)

        with open(SALES_JOURNAL_RTF, 'rb') as f:
            resp = client.post('/api/rj/native/parse-and-fill',
                               data={'file': (f, 'Sales_Journal.rtf'),
                                     'doc_type': 'sales_journal',
                                     'date': '2026-02-08'},
                               content_type='multipart/form-data')
        d = resp.get_json()
        assert d['success'] is True
        assert d['fields_filled'] > 5

    def test_parse_ar_summary(self, client, fresh_db):
        if not os.path.exists(AR_SUMMARY_PDF):
            pytest.skip("AR Summary PDF not available")
        self._setup_session(client)

        with open(AR_SUMMARY_PDF, 'rb') as f:
            resp = client.post('/api/rj/native/parse-and-fill',
                               data={'file': (f, 'AR_Summary.pdf'),
                                     'doc_type': 'ar_summary',
                                     'date': '2026-02-08'},
                               content_type='multipart/form-data')
        d = resp.get_json()
        assert d['success'] is True
        assert d['fields_filled'] > 0

    def test_parse_missing_doc_type_returns_400(self, client, fresh_db):
        self._setup_session(client)
        with open(DAILY_REV_PDF, 'rb') as f:
            resp = client.post('/api/rj/native/parse-and-fill',
                               data={'file': (f, 'test.pdf'),
                                     'date': '2026-02-08'},
                               content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_parse_missing_session_returns_404(self, client, fresh_db):
        if not os.path.exists(DAILY_REV_PDF):
            pytest.skip("Daily Revenue PDF not available")
        with open(DAILY_REV_PDF, 'rb') as f:
            resp = client.post('/api/rj/native/parse-and-fill',
                               data={'file': (f, 'test.pdf'),
                                     'doc_type': 'daily_revenue',
                                     'date': '2099-12-31'},
                               content_type='multipart/form-data')
        assert resp.status_code == 404


class TestFullRoundTrip:
    """Test complete Import → Parse → Export cycle."""

    def test_import_parse_export_reimport(self, client, fresh_db):
        """Full workflow: import RJ 07 → parse reports → export → verify."""
        if not os.path.exists(DAILY_REV_PDF):
            pytest.skip("Test files not available")

        # 1. Import
        with open(RJ_07_PATH, 'rb') as f:
            resp = client.post('/api/rj/native/import/excel',
                               data={'rj_file': (f, 'Rj 07-02-2026.xls')},
                               content_type='multipart/form-data')
        assert resp.get_json()['success']

        # 2. Parse a report
        with open(DAILY_REV_PDF, 'rb') as f:
            resp = client.post('/api/rj/native/parse-and-fill',
                               data={'file': (f, 'Daily_Rev.pdf'),
                                     'doc_type': 'daily_revenue',
                                     'date': '2026-02-08'},
                               content_type='multipart/form-data')
        assert resp.get_json()['success']

        # 3. Export
        resp = client.get('/api/rj/native/export/rj-filled/2026-02-08')
        assert resp.status_code == 200
        exported = resp.data

        # 4. Verify exported file
        of = olefile.OleFileIO(io.BytesIO(exported))
        vba_count = len([e for e in of.listdir()
                         if '_VBA_PROJECT_CUR' in '/'.join(e)])
        of.close()
        assert vba_count >= 100, "VBA macros should be preserved"

        rb = xlrd.open_workbook(file_contents=exported, formatting_info=True)
        assert len(rb.sheet_names()) == 38
        ctrl = rb.sheet_by_name('controle')
        assert ctrl.cell_value(2, 1) == 8  # Day 8

        # 5. Verify re-importable
        from utils.rj_reader import RJReader
        reader = RJReader(io.BytesIO(exported))
        ctrl2 = reader.read_controle()
        assert ctrl2.get('jour') == 8.0
