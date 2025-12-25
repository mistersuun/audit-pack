"""
Blueprint for generating night audit template documents dynamically.
"""

from flask import Blueprint, request, jsonify, send_file, render_template
from functools import wraps
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from openpyxl import load_workbook
import io
import os
from routes.checklist import login_required
from utils.weather_capture import get_weather_screenshot

generators_bp = Blueprint('generators', __name__)

@generators_bp.route('/generators')
@login_required
def generators_page():
    """Display the generators page."""
    return render_template('generators.html')

# Path to template files
TEMPLATE_DIR = 'static/templates'

@generators_bp.route('/api/generators/separateur-date', methods=['POST'])
@login_required
def generate_separateur_date():
    """
    Generate Séparateur Date document with specified date.
    Expected JSON: { "date": "2025-12-11" }
    """
    data = request.get_json()
    date_str = data.get('date')

    if not date_str:
        return jsonify({'error': 'Date is required'}), 400

    try:
        # Parse the date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')

        # Format in French: "Lundi le 11 Décembre 2025"
        days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        months_fr = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                     'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

        day_name = days_fr[date_obj.weekday()]
        month_name = months_fr[date_obj.month - 1]
        formatted_date = f"{day_name} le {date_obj.day} {month_name} {date_obj.year}"

        # Create a simple Word document
        doc = Document()
        paragraph = doc.add_paragraph(formatted_date)
        paragraph.alignment = 1  # Center alignment
        run = paragraph.runs[0]
        run.font.size = Pt(18)
        run.font.bold = True

        # Save to memory buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        filename = f'Separateur_Date_{date_obj.strftime("%Y-%m-%d")}.docx'

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@generators_bp.route('/api/generators/checklist-tournee', methods=['POST'])
@login_required
def generate_checklist_tournee():
    """
    Generate Checklist Tournée des Étages with specified date.
    Expected JSON: { "date": "2025-12-11" }
    """
    data = request.get_json()
    date_str = data.get('date')

    if not date_str:
        return jsonify({'error': 'Date is required'}), 400

    try:
        # Parse the date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%m/%d/%Y')

        # Load the template
        template_path = os.path.join(TEMPLATE_DIR, 'Checklist Tournée Étages.xlsx')
        wb = load_workbook(template_path)
        ws = wb.active

        # Update the date in cell A1 (adjust if needed)
        ws['A1'] = f"liste des vérifications pour auditeur de nuit {formatted_date}"

        # Save to memory buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        filename = f'Checklist_Tournee_{date_obj.strftime("%Y-%m-%d")}.xlsx'

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@generators_bp.route('/api/generators/entretien-hiver', methods=['POST'])
@login_required
def generate_entretien_hiver():
    """
    Generate Feuille d'Entretien with date and automatic weather screenshot.
    Expected JSON: {
        "date": "2025-12-11"
    }
    """
    data = request.get_json()
    date_str = data.get('date')

    if not date_str:
        return jsonify({'error': 'Date is required'}), 400

    try:
        # Parse the date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')

        days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        months_fr = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                     'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

        day_name = days_fr[date_obj.weekday()]
        day_num = date_obj.day
        month_name = months_fr[date_obj.month - 1]
        year = date_obj.year

        # Load the template
        template_path = os.path.join(TEMPLATE_DIR, 'Entretien Sheraton Laval Hiver.docx')
        doc = Document(template_path)

        # Update the date in the header
        if doc.paragraphs:
            for paragraph in doc.paragraphs:
                if 'hiver' in paragraph.text.lower():
                    paragraph.text = paragraph.text.replace(
                        paragraph.text.split('–')[0].split(chr(10))[-1].strip() if '–' in paragraph.text else '',
                        f"{day_name} {day_num} {month_name} {year}"
                    )
                    break

        # Get weather forecast screenshot
        print("🌤️ Capturing weather forecast...")
        weather_image = get_weather_screenshot()

        if weather_image:
            # Save image to temporary buffer
            img_buffer = io.BytesIO()
            weather_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            # Add weather screenshot to document
            doc.add_paragraph()
            weather_paragraph = doc.add_paragraph()
            weather_run = weather_paragraph.add_run()
            weather_run.add_picture(img_buffer, width=Inches(6.0))

            # Add some spacing
            doc.add_paragraph()

            print("✅ Weather forecast screenshot added to document")
        else:
            # Add a note that weather couldn't be fetched
            weather_paragraph = doc.add_paragraph()
            weather_paragraph.add_run("⚠️ Prévisions météo temporairement indisponibles").bold = True
            print("⚠️ Weather capture failed")

        # Save to memory buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        filename = f'Entretien_Hiver_{date_obj.strftime("%Y-%m-%d")}.docx'

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        print(f"Error generating document: {e}")
        return jsonify({'error': str(e)}), 500


@generators_bp.route('/api/generators/cles-banquets', methods=['POST'])
@login_required
def generate_cles_banquets():
    """
    Generate Clés Banquets document with event details.
    Expected JSON: {
        "date": "2025-12-11",
        "events": [
            {
                "salon": "Aut-Vimont",
                "compagnie": "SAPUTO",
                "heure": "08:00-13:00",
                "responsable": "JOANNA KOLANKAWSKA"
            },
            ...
        ]
    }
    """
    data = request.get_json()
    date_str = data.get('date')
    events = data.get('events', [])

    if not date_str:
        return jsonify({'error': 'Date is required'}), 400

    if not events:
        return jsonify({'error': 'At least one event is required'}), 400

    try:
        # Parse the date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d %B %Y').upper()

        # Load the template
        template_path = os.path.join(TEMPLATE_DIR, 'CLES BANQUETS.doc')
        doc = Document(template_path)

        # Update the date
        for paragraph in doc.paragraphs:
            if 'DATE :' in paragraph.text:
                paragraph.text = f'DATE : {formatted_date}'
                break

        # Update the table with events
        if doc.tables:
            table = doc.tables[0]  # First table

            # Clear existing data rows (keep header)
            while len(table.rows) > 1:
                table._element.remove(table.rows[-1]._element)

            # Add new event rows
            for event in events:
                row = table.add_row()
                row.cells[0].text = event.get('salon', '')
                row.cells[1].text = event.get('compagnie', '')
                row.cells[2].text = event.get('heure', '')
                row.cells[3].text = event.get('responsable', '')
                # Cell 4 is for signature (leave empty)

        # Save to memory buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        filename = f'Cles_Banquets_{date_obj.strftime("%Y-%m-%d")}.docx'

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
