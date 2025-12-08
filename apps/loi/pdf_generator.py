"""
PDF generation utility for LOI documents
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_loi_pdf(loi):
    """
    Generate PDF for LOI document

    Args:
        loi: LOI model instance

    Returns:
        BytesIO: PDF file content
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)

    # Container for the 'Flowable' objects
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        alignment=TA_LEFT
    )

    # Title
    title = Paragraph("LETTER OF INTENT", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))

    # Document Number
    doc_number = Paragraph(f"<b>Document Number:</b> {loi.document_number}", normal_style)
    elements.append(doc_number)
    elements.append(Spacer(1, 0.2*inch))

    # Date
    date_text = Paragraph(f"<b>Date:</b> {loi.created_at.strftime('%B %d, %Y')}", normal_style)
    elements.append(date_text)
    elements.append(Spacer(1, 0.3*inch))

    # Parties Information
    elements.append(Paragraph("PARTIES", heading_style))

    parties_data = [
        ['Party', 'Company', 'Country'],
        ['Buyer', loi.buyer_company, loi.buyer_country],
        ['Producer', loi.producer_company, loi.producer_country],
    ]

    parties_table = Table(parties_data, colWidths=[1.5*inch, 3*inch, 2*inch])
    parties_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(parties_table)
    elements.append(Spacer(1, 0.3*inch))

    # Content Information
    elements.append(Paragraph("CONTENT DETAILS", heading_style))
    elements.append(Paragraph(f"<b>Title:</b> {loi.content_title}", normal_style))
    elements.append(Spacer(1, 0.1*inch))

    # Wrap long description
    desc_text = loi.content_description.replace('\n', '<br/>')
    elements.append(Paragraph(f"<b>Description:</b>", normal_style))
    elements.append(Paragraph(desc_text, normal_style))
    elements.append(Spacer(1, 0.3*inch))

    # Deal Terms
    elements.append(Paragraph("DEAL TERMS", heading_style))

    price_formatted = f"{loi.currency} {loi.agreed_price:,.2f}"
    elements.append(Paragraph(f"<b>Agreed Price:</b> {price_formatted}", normal_style))
    elements.append(Spacer(1, 0.4*inch))

    # Agreement Statement
    agreement_text = """
    This Letter of Intent confirms the mutual interest of the above parties to proceed with
    the proposed content licensing agreement under the terms outlined above. This document
    represents a preliminary understanding and is subject to the execution of a formal agreement.
    """
    elements.append(Paragraph(agreement_text, normal_style))
    elements.append(Spacer(1, 0.5*inch))

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    from django.utils import timezone
    current_time = timezone.now()
    footer_text = f"Generated on {current_time.strftime('%B %d, %Y at %I:%M %p')}"
    elements.append(Paragraph(footer_text, footer_style))

    # Build PDF
    doc.build(elements)

    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()

    return pdf_data
