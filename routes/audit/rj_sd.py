"""
RJ SD blueprint - handles Sommaire Journalier (SD) file operations.
"""

from flask import Blueprint, request, jsonify, send_file, session
from datetime import datetime
import io
from routes.checklist import login_required
from .rj_core import RJ_FILES, SD_FILES, get_session_id


rj_sd_bp = Blueprint('rj_sd', __name__)
from utils.csrf import csrf_protect


@rj_sd_bp.route('/api/sd/upload', methods=['POST'])
@login_required
@csrf_protect
def upload_sd():
    """
    Upload SD (Sommaire Journalier) file.

    Expects:
        - File upload with key 'sd_file'

    Returns:
        {
            'success': bool,
            'message': str,
            'file_info': {
                'filename': str,
                'size': int,
                'available_days': list
            }
        }
    """
    if 'sd_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    file = request.files['sd_file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not file.filename.endswith(('.xls', '.xlsx')):
        return jsonify({'success': False, 'error': 'File must be .xls or .xlsx'}), 400

    try:
        from utils.sd_reader import SDReader

        # Read file to memory
        file_bytes = io.BytesIO(file.read())

        # Validate it's a proper SD file
        reader = SDReader(file_bytes)
        available_days = reader.get_available_days()

        # Store in session-based storage
        session_id = get_session_id()
        file_bytes.seek(0)
        SD_FILES[session_id] = file_bytes

        return jsonify({
            'success': True,
            'message': 'Fichier SD uploadé avec succès',
            'file_info': {
                'filename': file.filename,
                'size': len(file_bytes.getvalue()),
                'available_days': available_days
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_sd_bp.route('/api/sd/day/<int:day>', methods=['GET'])
@login_required
def get_sd_day(day):
    """
    Get all entries for a specific day from SD file.

    Args:
        day: Day number (1-31)

    Returns:
        {
            'success': bool,
            'data': {
                'day': int,
                'date': str or float,
                'entries': [...]
            }
        }
    """
    session_id = get_session_id()
    if session_id not in SD_FILES:
        return jsonify({'success': False, 'error': 'No SD file uploaded'}), 400

    if not 1 <= day <= 31:
        return jsonify({'success': False, 'error': 'Day must be between 1-31'}), 400

    try:
        from utils.sd_reader import SDReader

        file_bytes = SD_FILES[session_id]
        file_bytes.seek(0)
        reader = SDReader(file_bytes)

        data = reader.read_day_data(day)

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_sd_bp.route('/api/sd/day/<int:day>/totals', methods=['GET'])
@login_required
def get_sd_day_totals(day):
    """
    Get totals for a specific day from SD file.

    Args:
        day: Day number (1-31)

    Returns:
        {
            'success': bool,
            'day': int,
            'totals': {
                'total_montant': float,
                'total_verifie': float,
                'total_remboursement': float,
                'total_variance': float
            }
        }
    """
    session_id = get_session_id()
    if session_id not in SD_FILES:
        return jsonify({'success': False, 'error': 'No SD file uploaded'}), 400

    if not 1 <= day <= 31:
        return jsonify({'success': False, 'error': 'Day must be between 1-31'}), 400

    try:
        from utils.sd_reader import SDReader

        file_bytes = SD_FILES[session_id]
        file_bytes.seek(0)
        reader = SDReader(file_bytes)

        totals = reader.get_totals_for_day(day)

        return jsonify({
            'success': True,
            'day': day,
            'totals': totals
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_sd_bp.route('/api/sd/day/<int:day>/entries', methods=['POST'])
@login_required
@csrf_protect
def write_sd_day_entries(day):
    """
    Write entries to a specific day in SD file.

    Args:
        day: Day number (1-31)

    Request body:
        {
            'entries': [
                {
                    'departement': str,
                    'nom': str,
                    'cdn_us': str,
                    'montant': float,
                    'montant_verifie': float (optional),
                    'remboursement': float (optional),
                    'variance': float (optional)
                },
                ...
            ]
        }

    Returns:
        {
            'success': bool,
            'message': str,
            'day': int,
            'entries_written': int
        }
    """
    session_id = get_session_id()
    if session_id not in SD_FILES:
        return jsonify({'success': False, 'error': 'No SD file uploaded'}), 400

    if not 1 <= day <= 31:
        return jsonify({'success': False, 'error': 'Day must be between 1-31'}), 400

    data = request.get_json()
    entries = data.get('entries', [])

    if not entries:
        return jsonify({'success': False, 'error': 'No entries provided'}), 400

    try:
        from utils.sd_writer import SDWriter

        # Get current SD file
        sd_bytes = SD_FILES[session_id]

        # Write entries
        updated_sd = SDWriter.write_entries(sd_bytes, day, entries)

        # Update in session
        SD_FILES[session_id] = updated_sd

        return jsonify({
            'success': True,
            'message': f'{len(entries)} entrées écrites pour le jour {day}',
            'day': day,
            'entries_written': len(entries)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_sd_bp.route('/api/sd/download', methods=['GET'])
@login_required
def download_sd():
    """
    Download the current SD file.

    Returns:
        SD Excel file
    """
    session_id = get_session_id()
    if session_id not in SD_FILES:
        return jsonify({'success': False, 'error': 'No SD file uploaded'}), 400

    try:
        file_bytes = SD_FILES[session_id]
        file_bytes.seek(0)

        return send_file(
            file_bytes,
            mimetype='application/vnd.ms-excel',
            as_attachment=True,
            download_name=f'SD_{datetime.now().strftime("%Y-%m-%d")}.xls'
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_sd_bp.route('/api/sd/export_setd', methods=['POST'])
@login_required
@csrf_protect
def export_sd_to_setd():
    """
    Export SD variances to SetD sheet in RJ file.

    Request body:
        {
            'day': int (1-31),
            'variances': [
                {'nom': str, 'variance': float},
                ...
            ]
        }

    Returns:
        {
            'success': bool,
            'message': str,
            'exported': int (number of variances written),
            'unmatched': list (names not found in SetD mapping)
        }
    """
    session_id = get_session_id()

    # Check that RJ file is uploaded
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded. Please upload RJ first.'}), 400

    data = request.get_json()
    day = data.get('day')
    variances = data.get('variances', [])

    if not day or not 1 <= day <= 31:
        return jsonify({'success': False, 'error': 'Day must be between 1-31'}), 400

    if not variances:
        return jsonify({'success': False, 'error': 'No variances to export'}), 400

    try:
        from utils.rj_mapper import SETD_PERSONNEL_COLUMNS, get_setd_cell
        import xlrd
        from xlutils.copy import copy as xlcopy

        # Get RJ file
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        # Open workbook
        workbook = xlrd.open_workbook(file_contents=file_bytes.read(), formatting_info=True)
        wb_copy = xlcopy(workbook)

        # Find SetD sheet
        setd_sheet = None
        setd_idx = None
        for idx, name in enumerate(workbook.sheet_names()):
            if name.lower() == 'setd':
                setd_sheet = wb_copy.get_sheet(idx)
                setd_idx = idx
                break

        if setd_sheet is None:
            return jsonify({'success': False, 'error': 'SetD sheet not found in RJ file'}), 400

        exported = 0
        unmatched = []

        # Process each variance
        for item in variances:
            nom = item.get('nom', '').strip()
            variance = item.get('variance', 0)

            if not nom or variance == 0:
                continue

            # Find column for this employee
            col_letter = SETD_PERSONNEL_COLUMNS.get(nom)

            if col_letter:
                # Calculate row (day 1 = row 5, day 2 = row 6, etc.)
                row = 4 + day

                # Convert column letter to index
                col_idx = 0
                for i, char in enumerate(reversed(col_letter)):
                    col_idx += (ord(char.upper()) - ord('A') + 1) * (26 ** i)
                col_idx -= 1  # 0-indexed

                # Write variance
                setd_sheet.write(row - 1, col_idx, variance)  # row is 0-indexed
                exported += 1
            else:
                unmatched.append(nom)

        # Save updated workbook
        output = io.BytesIO()
        wb_copy.save(output)
        output.seek(0)
        RJ_FILES[session_id] = output

        return jsonify({
            'success': True,
            'message': f'{exported} variance(s) exportée(s) vers SetD pour le jour {day}',
            'exported': exported,
            'unmatched': unmatched,
            'day': day
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_sd_bp.route('/api/sd/auto-import-setd', methods=['POST'])
@login_required
@csrf_protect
def auto_import_sd_to_setd():
    """
    Auto-import SD variances to SetD sheet in RJ file.

    Automatically matches employee names from SD file to SetD personnel columns
    using fuzzy matching and writes matched variances to the RJ file.

    Request body (optional):
        {
            'day': int (1-31, optional - defaults to current audit day)
        }

    Returns:
        {
            'success': bool,
            'message': str,
            'day': int,
            'exported': int (number of variances written),
            'matched': [
                {'nom': str, 'variance': float, 'col_letter': str},
                ...
            ],
            'unmatched': [
                {'nom': str, 'variance': float},
                ...
            ],
            'confidence': float (0.0 - 1.0),
            'totals': {
                'total_montant': float,
                'total_verifie': float,
                'total_remboursement': float,
                'total_variance': float
            }
        }
    """
    session_id = get_session_id()

    # Check that both SD and RJ files are uploaded
    if session_id not in SD_FILES:
        return jsonify({'success': False, 'error': 'No SD file uploaded. Please upload SD first.'}), 400

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded. Please upload RJ first.'}), 400

    data = request.get_json() or {}
    day = data.get('day')

    # If no day specified, default to current audit day (1)
    if day is None:
        day = 1

    if not 1 <= day <= 31:
        return jsonify({'success': False, 'error': 'Day must be between 1-31'}), 400

    try:
        from utils.parsers.sd_parser import SDParser
        from utils.rj_filler import excel_col_to_index
        import xlrd
        from xlutils.copy import copy as xlcopy

        # Parse SD file with SDParser
        sd_bytes = SD_FILES[session_id]
        sd_bytes.seek(0)

        parser = SDParser(sd_bytes.read(), day=day)
        parse_result = parser.get_result()

        if not parse_result['success']:
            return jsonify({
                'success': False,
                'error': f"SD parsing failed: {parse_result['errors']}"
            }), 400

        extracted = parse_result['data']
        setd_fillable = extracted.get('setd_fillable', {})
        matched_employees = extracted.get('matched_count', 0)
        unmatched_names = extracted.get('unmatched_count', 0)

        # Get RJ file and open for writing
        rj_bytes = RJ_FILES[session_id]
        rj_bytes.seek(0)

        workbook = xlrd.open_workbook(file_contents=rj_bytes.read(), formatting_info=True)
        wb_copy = xlcopy(workbook)

        # Find SetD sheet
        setd_sheet = None
        for idx, name in enumerate(workbook.sheet_names()):
            if name.lower() == 'setd':
                setd_sheet = wb_copy.get_sheet(idx)
                break

        if setd_sheet is None:
            return jsonify({'success': False, 'error': 'SetD sheet not found in RJ file'}), 400

        # Write variances to SetD
        exported = 0
        for col_letter, variance in setd_fillable.items():
            if variance == 0:
                continue

            try:
                # Calculate row (day 1 = row 5, day 2 = row 6, etc.)
                row = 4 + day

                # Convert column letter to index
                col_idx = excel_col_to_index(col_letter)

                # Write variance
                setd_sheet.write(row - 1, col_idx, variance)
                exported += 1
            except Exception as write_err:
                # Log but continue with other entries
                import traceback
                traceback.print_exc()
                continue

        # Save updated workbook
        output = io.BytesIO()
        wb_copy.save(output)
        output.seek(0)
        RJ_FILES[session_id] = output

        # Build matched/unmatched lists for response
        matched_list = []
        unmatched_list = []

        for entry in extracted.get('entries', []):
            nom = entry.get('nom', '').strip()
            variance = entry.get('variance', 0)

            if not nom or variance == 0:
                continue

            # Check if matched (would be in setd_fillable if matched)
            # Re-match to get the column letter
            parser_obj = SDParser(SD_FILES[session_id].getvalue() if hasattr(SD_FILES[session_id], 'getvalue') else SD_FILES[session_id].read(), day=day)
            parser_obj.parse()

            is_matched = False
            for match in parser_obj.matched_employees:
                if match['nom'] == nom:
                    matched_list.append({
                        'nom': nom,
                        'variance': variance,
                        'col_letter': match['col_letter']
                    })
                    is_matched = True
                    break

            if not is_matched and nom not in [u['nom'] for u in unmatched_list]:
                unmatched_list.append({
                    'nom': nom,
                    'variance': variance
                })

        return jsonify({
            'success': True,
            'message': f'{exported} variance(s) auto-importée(s) vers SetD pour le jour {day}',
            'day': day,
            'exported': exported,
            'matched': matched_list,
            'unmatched': unmatched_list,
            'confidence': parse_result.get('confidence', 0.0),
            'totals': extracted.get('totals', {}),
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
