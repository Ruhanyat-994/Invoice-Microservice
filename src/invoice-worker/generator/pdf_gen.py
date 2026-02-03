from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

def generate(data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Logo/Company Name
    elements.append(Paragraph(f"<b>{data.get('company_name', '[Company Name]')}</b>", styles['Title']))
    elements.append(Paragraph(data.get('company_address', '[Street Address, City, ST ZIP]'), styles['Normal']))
    elements.append(Paragraph(f"Phone: {data.get('company_phone', '[000-000-0000]')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Invoice Header
    elements.append(Paragraph("<font size=24 color=blue>INVOICE</font>", styles['Normal']))
    elements.append(Paragraph(f"DATE: {data.get('date', '5/1/2014')}", styles['Normal']))
    elements.append(Paragraph(f"INVOICE #: {data.get('invoice_no', '[123456]')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Bill To / Ship To
    bt_st_data = [
        [Paragraph("<b>BILL TO:</b>", styles['Normal']), Paragraph("<b>SHIP TO:</b>", styles['Normal'])],
        [data.get('bill_to_name', '[Name]'), data.get('ship_to_name', '[Name]')],
        [data.get('bill_to_company', '[Company Name]'), data.get('ship_to_company', '[Company Name]')],
        [data.get('bill_to_address', '[Street Address]'), data.get('ship_to_address', '[Street Address]')]
    ]
    bt_st_table = Table(bt_st_data, colWidths=[250, 250])
    elements.append(bt_st_table)
    elements.append(Spacer(1, 20))

    # Items Table
    table_data = [['ITEM #', 'DESCRIPTION', 'QTY', 'UNIT PRICE', 'TOTAL']]
    for item in data.get('items', []):
        table_data.append([
            item.get('id', ''),
            item.get('description', ''),
            str(item.get('qty', 0)),
            f"{item.get('unit_price', 0.0):.2f}",
            f"{item.get('total', 0.0):.2f}"
        ])
    
    # Add empty rows to match pattern
    for _ in range(5):
        table_data.append(['', '', '', '', ''])

    items_table = Table(table_data, colWidths=[80, 200, 50, 80, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))

    # Totals
    totals_data = [
        ['', '', 'SUBTOTAL', f"{data.get('subtotal', 0.0):.2f}"],
        ['', '', 'TAX RATE', f"{data.get('tax_rate', 0.0):.3f}%"],
        ['', '', 'TAX', f"{data.get('tax_amount', 0.0):.2f}"],
        ['', '', 'TOTAL', f"$ {data.get('total_amount', 0.0):.2f}"]
    ]
    totals_table = Table(totals_data, colWidths=[80, 200, 130, 80])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('GRID', (2, 0), (3, -1), 0.5, colors.grey),
        ('BACKGROUND', (2, 3), (3, 3), colors.lightgrey),
    ]))
    elements.append(totals_table)

    # Footer
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Thank You For Your Business!", styles['Italic']))

    doc.build(elements)
