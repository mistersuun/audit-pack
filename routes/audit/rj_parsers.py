"""
RJ Parsers blueprint - handles document parsing and auto-fill.
"""

from flask import Blueprint, request, jsonify, session
import io
from routes.checklist import login_required
from utils.csrf import csrf_protect
from utils.rj_filler import RJFiller
from .rj_core import RJ_FILES, get_session_id


rj_parsers_bp = Blueprint('rj_parsers', __name__)


@rj_parsers_bp.route('/api/rj/parse', methods=['POST'])
@login_required
@csrf_protect
def parse_document():
    """
    Parse an uploaded document and return extracted data for review.

    Form data:
        doc_type: 'daily_revenue' | 'advance_deposit' | 'freedompay' | 'hp_excel'
        file: uploaded file

    Returns:
        {
            'success': true,
            'data': { extracted fields },
            'field_mappings': { field -> cell reference },
            'confidence': 0.0-1.0,
            'warnings': [...],
            'errors': [...]
        }
    """
    from utils.parsers import ParserFactory

    doc_type = request.form.get('doc_type')
    file = request.files.get('file')

    if not doc_type:
        return jsonify({'success': False, 'error': 'Type de document requis'}), 400
    if not file:
        return jsonify({'success': False, 'error': 'Fichier requis'}), 400

    try:
        file_bytes = file.read()

        # Extra kwargs per parser type (e.g., day for HP parser)
        extra_kwargs = {}
        if doc_type == 'hp_excel':
            day = request.form.get('day')
            if day:
                try:
                    extra_kwargs['day'] = int(day)
                except (ValueError, TypeError):
                    pass

        parser = ParserFactory.create(doc_type, file_bytes, filename=file.filename, **extra_kwargs)
        result = parser.get_result()

        return jsonify(result)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur de parsing: {str(e)}'}), 500


@rj_parsers_bp.route('/api/rj/parse-and-fill', methods=['POST'])
@login_required
def parse_and_fill():
    """
    Parse document AND auto-fill the corresponding RJ sheet.

    Form data:
        doc_type: parser type
        file: uploaded document

    Returns:
        Parsed data + list of cells that were filled
    """
    from utils.parsers import ParserFactory

    doc_type = request.form.get('doc_type')
    file = request.files.get('file')

    if not doc_type or not file:
        return jsonify({'success': False, 'error': 'Type et fichier requis'}), 400

    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé. Charger un RJ d\'abord.'}), 400

    try:
        # 1. Parse the document
        file_bytes = file.read()
        parser = ParserFactory.create(doc_type, file_bytes, filename=file.filename)
        result = parser.get_result()

        if not result['success']:
            return jsonify(result), 400

        # 2. Get fillable data (cell_ref -> value)
        fillable = parser.get_fillable_data()

        if not fillable:
            return jsonify({
                'success': True,
                'data': result['data'],
                'filled_cells': [],
                'message': 'Données extraites mais aucune cellule à remplir (parser en mode squelette)'
            })

        # 3. Fill RJ file
        rj_bytes = RJ_FILES[session_id]
        rj_bytes.seek(0)
        filler = RJFiller(rj_bytes)

        # Determine target sheet from parser type info
        type_info = ParserFactory.get_type_info().get(doc_type, {})
        target_sheet = type_info.get('target_sheet', 'Recap')

        filled_count = filler.fill_sheet(target_sheet, {
            k: v for k, v in result['data'].items()
            if k in parser.FIELD_MAPPINGS
        })

        # 4. Save modified RJ back to memory
        output = io.BytesIO()
        filler.save(output)
        output.seek(0)
        RJ_FILES[session_id] = output

        return jsonify({
            'success': True,
            'data': result['data'],
            'filled_cells': list(fillable.keys()),
            'filled_count': filled_count,
            'confidence': result['confidence'],
            'warnings': result['warnings'],
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_parsers_bp.route('/api/rj/fill-jour', methods=['POST'])
@login_required
def fill_jour():
    """
    Compute jour values from all parsed data + manual values + adjustments,
    then write to the jour sheet for the specified day.

    JSON body:
        day: int (1-31) — if omitted, reads from controle B3
        parsed_data: dict of {doc_type: extracted_data}
        manual_values: dict with 'club_lounge', 'deposit_on_hand'
        adjustments: list of {department, amount}

    Returns:
        {
            'success': true,
            'filled_count': N,
            'day': D,
            'target_row': R,
            'values': {col_letter: value},
            'summary': {warnings, errors, column_count}
        }
    """
    import json as json_mod
    from utils.jour_mapper import JourMapper
    from utils.rj_reader import RJReader

    data = request.get_json(silent=True) or {}

    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 400

    try:
        # Get day (from request or from controle B3)
        day = data.get('day')
        if not day:
            rj_bytes = RJ_FILES[session_id]
            rj_bytes.seek(0)
            reader = RJReader(rj_bytes)
            day = reader.get_current_audit_day()

        if not day or day < 1 or day > 31:
            return jsonify({'success': False, 'error': f'Jour invalide: {day}'}), 400

        # Get all data sources
        parsed_data = data.get('parsed_data', {})
        manual_values = data.get('manual_values', {})
        adjustments = data.get('adjustments', [])

        # Compute jour values
        mapper = JourMapper(
            daily_rev_data=parsed_data.get('daily_revenue', {}),
            sales_journal_data=parsed_data.get('sales_journal', {}),
            ar_summary_data=parsed_data.get('ar_summary', {}),
            hp_data=parsed_data.get('hp_excel', {}),
            manual_values=manual_values,
            adjustments=adjustments,
        )

        jour_values = mapper.compute_all()
        summary = mapper.get_summary()

        if not jour_values:
            return jsonify({
                'success': True,
                'filled_count': 0,
                'day': day,
                'message': 'Aucune valeur calculée (données insuffisantes)',
                'summary': summary
            })

        # Write to RJ
        rj_bytes = RJ_FILES[session_id]
        rj_bytes.seek(0)
        filler = RJFiller(rj_bytes)

        result = filler.fill_jour_day(day, jour_values)

        # Save modified RJ back to memory
        output = io.BytesIO()
        filler.save(output)
        output.seek(0)
        RJ_FILES[session_id] = output

        # Convert column indices to letters for display
        from utils.daily_rev_jour_mapping import col_index_to_letter
        values_display = {}
        for col_idx, val in jour_values.items():
            letter = col_index_to_letter(int(col_idx))
            values_display[letter] = round(val, 2) if val else 0

        return jsonify({
            'success': True,
            'filled_count': result['filled_count'],
            'day': day,
            'target_row': result['target_row'],
            'values': values_display,
            'summary': summary,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_parsers_bp.route('/api/rj/departments', methods=['GET'])
@login_required
def get_departments():
    """Get available departments for adjustments."""
    from utils.adjustment_handler import get_departments
    return jsonify({
        'success': True,
        'departments': get_departments()
    })


@rj_parsers_bp.route('/api/rj/parser-types', methods=['GET'])
@login_required
def get_parser_types():
    """Get available parser types and their info."""
    from utils.parsers import ParserFactory
    return jsonify({
        'success': True,
        'types': ParserFactory.get_type_info()
    })
