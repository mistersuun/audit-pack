"""Tests for OLE builder — preserving VBA macros in exported .xls files."""

import io
import xlrd
import olefile
import pytest
from xlutils.copy import copy as copy_workbook
from utils.ole_builder import OLEBuilder, rebuild_xls_with_vba


class TestOLEBuilder:
    """Test low-level OLE compound file builder."""

    def test_build_simple_file(self):
        builder = OLEBuilder()
        result = builder.build({'TestStream': b'Hello World' * 1000})
        assert len(result) > 512  # At least header
        # Should be readable by olefile
        of = olefile.OleFileIO(io.BytesIO(result))
        assert 'TestStream' in ['/'.join(e) for e in of.listdir()]
        data = of.openstream('TestStream').read()
        assert data == b'Hello World' * 1000
        of.close()

    def test_build_nested_storages(self):
        builder = OLEBuilder()
        result = builder.build({
            'Workbook': b'\x00' * 1024,
            '_VBA/Module1': b'Sub Main()\nEnd Sub',
            '_VBA/Module2': b'Sub Test()\nEnd Sub',
        })
        of = olefile.OleFileIO(io.BytesIO(result))
        streams = ['/'.join(e) for e in of.listdir()]
        assert 'Workbook' in streams
        assert '_VBA/Module1' in streams
        assert '_VBA/Module2' in streams
        of.close()

    def test_build_large_stream(self):
        """Large streams (> 4096 bytes) should be stored as regular streams."""
        builder = OLEBuilder()
        large_data = b'\x42' * 100000
        result = builder.build({'BigStream': large_data})
        of = olefile.OleFileIO(io.BytesIO(result))
        data = of.openstream('BigStream').read()
        assert data == large_data
        of.close()

    def test_build_mini_stream(self):
        """Small streams (< 4096 bytes) should be stored in mini stream."""
        builder = OLEBuilder()
        small_data = b'tiny'
        result = builder.build({'SmallStream': small_data})
        of = olefile.OleFileIO(io.BytesIO(result))
        data = of.openstream('SmallStream').read()
        assert data == small_data
        of.close()


class TestRebuildXlsWithVba:
    """Test the main rebuild function that preserves VBA."""

    def test_preserves_vba_streams(self, rj07_bytes):
        # Count VBA streams in original
        of_orig = olefile.OleFileIO(io.BytesIO(rj07_bytes))
        orig_vba = len([e for e in of_orig.listdir()
                        if '_VBA_PROJECT_CUR' in '/'.join(e)])
        of_orig.close()

        # Create modified file with xlutils.copy
        rb = xlrd.open_workbook(file_contents=rj07_bytes, formatting_info=True)
        wb = copy_workbook(rb)
        buf = io.BytesIO()
        wb.save(buf)
        modified_bytes = buf.getvalue()

        # Rebuild
        result = rebuild_xls_with_vba(rj07_bytes, modified_bytes)

        # Verify VBA preserved
        of_result = olefile.OleFileIO(io.BytesIO(result))
        result_vba = len([e for e in of_result.listdir()
                          if '_VBA_PROJECT_CUR' in '/'.join(e)])
        of_result.close()

        assert result_vba == orig_vba

    def test_preserves_sheet_count(self, rj07_bytes):
        rb = xlrd.open_workbook(file_contents=rj07_bytes, formatting_info=True)
        orig_sheets = len(rb.sheet_names())

        wb = copy_workbook(rb)
        buf = io.BytesIO()
        wb.save(buf)
        result = rebuild_xls_with_vba(rj07_bytes, buf.getvalue())

        rb2 = xlrd.open_workbook(file_contents=result, formatting_info=True)
        assert len(rb2.sheet_names()) == orig_sheets

    def test_applies_modifications(self, rj07_bytes):
        rb = xlrd.open_workbook(file_contents=rj07_bytes, formatting_info=True)
        wb = copy_workbook(rb)
        # Set day to 99
        ctrl = wb.get_sheet(1)
        ctrl.write(2, 1, 99)
        buf = io.BytesIO()
        wb.save(buf)

        result = rebuild_xls_with_vba(rj07_bytes, buf.getvalue())

        rb2 = xlrd.open_workbook(file_contents=result, formatting_info=True)
        assert rb2.sheet_by_name('controle').cell_value(2, 1) == 99

    def test_result_readable_by_rj_reader(self, rj07_bytes):
        from utils.rj_reader import RJReader

        rb = xlrd.open_workbook(file_contents=rj07_bytes, formatting_info=True)
        wb = copy_workbook(rb)
        buf = io.BytesIO()
        wb.save(buf)

        result = rebuild_xls_with_vba(rj07_bytes, buf.getvalue())

        # Should be parseable by our RJReader
        reader = RJReader(io.BytesIO(result))
        ctrl = reader.read_controle()
        assert 'jour' in ctrl
        recap = reader.read_recap()
        assert isinstance(recap, dict)

    def test_result_file_size_reasonable(self, rj07_bytes):
        rb = xlrd.open_workbook(file_contents=rj07_bytes, formatting_info=True)
        wb = copy_workbook(rb)
        buf = io.BytesIO()
        wb.save(buf)

        result = rebuild_xls_with_vba(rj07_bytes, buf.getvalue())

        # Should be roughly similar size to original (within 50%)
        orig_size = len(rj07_bytes)
        assert len(result) > orig_size * 0.5
        assert len(result) < orig_size * 2.0
