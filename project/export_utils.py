import io
import xlsxwriter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime


def export_to_excel(data, title, columns):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Rapor')

    header_fmt = workbook.add_format({
        'bold': True,
        'bg_color': '#1a5f7a',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    title_fmt = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center'
    })
    cell_fmt = workbook.add_format({'border': 1, 'valign': 'vcenter'})
    num_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'valign': 'vcenter'})
    date_fmt = workbook.add_format({'border': 1, 'num_format': 'dd/mm/yyyy', 'valign': 'vcenter'})

    worksheet.merge_range(0, 0, 0, len(columns) - 1, title, title_fmt)
    worksheet.set_row(0, 30)

    info_fmt = workbook.add_format({'italic': True, 'font_color': '#666666'})
    worksheet.merge_range(1, 0, 1, len(columns) - 1,
                          f"Oluşturulma Tarihi: {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_fmt)

    for col_idx, col in enumerate(columns):
        worksheet.write(2, col_idx, col['header'], header_fmt)
        worksheet.set_column(col_idx, col_idx, col.get('width', 15))

    worksheet.set_row(2, 25)

    for row_idx, row in enumerate(data):
        for col_idx, col in enumerate(columns):
            val = row.get(col['key'], '')
            if val is None:
                val = ''

            fmt = cell_fmt
            if col.get('type') == 'number':
                fmt = num_fmt
                try:
                    val = float(val) if val != '' else 0
                except:
                    val = 0
            elif col.get('type') == 'date':
                fmt = date_fmt

            worksheet.write(row_idx + 3, col_idx, val, fmt)

    workbook.close()
    output.seek(0)
    return output


def export_to_pdf(data, title, columns):
    output = io.BytesIO()

    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1*cm
    )

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=6,
        alignment=1
    )
    story.append(Paragraph(title, title_style))

    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=1
    )
    story.append(Paragraph(f"Oluşturulma Tarihi: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    story.append(Spacer(1, 0.4*cm))

    headers = [col['header'] for col in columns]
    table_data = [headers]

    for row in data:
        row_data = []
        for col in columns:
            val = row.get(col['key'], '')
            if val is None:
                val = ''
            if col.get('type') == 'number' and val != '':
                try:
                    val = f"{float(val):,.2f}"
                except:
                    pass
            row_data.append(str(val))
        table_data.append(row_data)

    col_widths = [col.get('pdf_width', 3*cm) for col in columns]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5f7a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f9fa')]),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWHEIGHT', (0, 0), (-1, 0), 20),
        ('ROWHEIGHT', (0, 1), (-1, -1), 16),
    ]))

    story.append(table)

    story.append(Spacer(1, 0.5*cm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    story.append(Paragraph(f"Toplam {len(data)} kayıt", footer_style))

    doc.build(story)
    output.seek(0)
    return output
