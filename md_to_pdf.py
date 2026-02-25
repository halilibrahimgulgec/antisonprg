import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def generate_pdf(md_file, pdf_file):
    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom styles
    h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=18, spaceAfter=12, textColor=colors.HexColor("#2E5077"))
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, spaceBefore=10, spaceAfter=8, textColor=colors.HexColor("#4DA1A9"))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=6)
    
    elements = []
    
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    in_table = False
    table_data = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_table:
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#79D7BE")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 12))
                in_table = False
                table_data = []
            continue
            
        if line.startswith('# '):
            elements.append(Paragraph(line[2:], h1_style))
        elif line.startswith('## '):
            elements.append(Paragraph(line[3:], h2_style))
        elif line.startswith('### '):
            elements.append(Paragraph(line[4:], h2_style))
        elif line.startswith('|'):
            in_table = True
            cols = [c.strip() for c in line.split('|') if c.strip()]
            if not all(c.startswith('---') for c in cols): # Skip separator row
                table_data.append(cols)
        elif line.startswith('- '):
            elements.append(Paragraph(f"• {line[2:]}", body_style))
        elif line.startswith('---'):
            pass # Horizontal line skip for simplicity
        elif 'mermaid' in line or '```' in line:
            pass # Skip code blocks for PDF
        else:
            elements.append(Paragraph(line, body_style))
            
    doc.build(elements)

if __name__ == "__main__":
    md_path = r"C:\Users\User\.gemini\antigravity\brain\5f5a867e-c547-48f8-a740-c1a6d08a3d4e\presentation.md"
    pdf_path = r"C:\Users\User\.gemini\antigravity\brain\5f5a867e-c547-48f8-a740-c1a6d08a3d4e\presentation.pdf"
    generate_pdf(md_path, pdf_path)
    print(f"Successfully generated {pdf_path}")
