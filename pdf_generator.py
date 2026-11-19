"""
pdf_generator.py - Generates Downloadable Medical Analysis PDF Reports using ReportLab
Creates a beautifully formatted, clinical summary ready for patient download.
"""
import io
from datetime import datetime
from typing import Dict, List, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_summary_pdf(
    patient_info: Dict[str, str],
    parameters: List[Dict[str, Any]],
    summary_data: Dict[str, Any]
) -> bytes:
    """
    Builds a professional multi-section medical summary report in PDF format.
    Returns the binary content as bytes for direct browser download.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0d3b66'),
        alignment=1,
        spaceAfter=2
    )
    sub_title_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#555555'),
        alignment=1,
        spaceAfter=10
    )
    sec_title = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading2'],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0d3b66'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#2b2d42')
    )
    bold_style = ParagraphStyle(
        'BoldDark',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#111111')
    )
    alert_style = ParagraphStyle(
        'AlertText',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#c0392b')
    )
    badge_style = ParagraphStyle(
        'BadgeText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        alignment=1,
        fontName='Helvetica-Bold'
    )

    # 1. Header
    elements.append(Paragraph("SMART MEDICAL LAB REPORT SUMMARY", title_style))
    elements.append(Paragraph(
        f"Automated AI & Clinical Analysis | Generated on {datetime.now().strftime('%d-%b-%Y %I:%M %p')}",
        sub_title_style
    ))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0d3b66'), spaceAfter=10))

    # 2. Patient Demographics & Health Score Table
    health_score = summary_data.get("health_score", {})
    score_val = health_score.get("score", "N/A")
    score_status = health_score.get("status", "Analyzed")

    demo_data = [
        [
            Paragraph(f"<b>Patient Name:</b> {patient_info.get('name', 'N/A')}", body_style),
            Paragraph(f"<b>Age / Gender:</b> {patient_info.get('age_gender', 'N/A')}", body_style),
            Paragraph(f"<b>Overall Score:</b> <font color='#0d3b66'><b>{score_val}/100</b></font>", bold_style)
        ],
        [
            Paragraph(f"<b>Doctor:</b> {patient_info.get('doctor', 'N/A')}", body_style),
            Paragraph(f"<b>Report Date:</b> {patient_info.get('date', 'Recent')}", body_style),
            Paragraph(f"<b>Status:</b> {score_status}", body_style)
        ]
    ]
    demo_table = Table(demo_data, colWidths=[200, 180, 160])
    demo_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(demo_table)
    elements.append(Spacer(1, 10))

    # 3. Parameters Table
    elements.append(Paragraph("1. LABORATORY TEST RESULTS & STATUS", sec_title))
    table_rows = [[
        Paragraph("<b>TEST PARAMETER</b>", bold_style),
        Paragraph("<b>VALUE</b>", bold_style),
        Paragraph("<b>UNIT</b>", bold_style),
        Paragraph("<b>NORMAL RANGE</b>", bold_style),
        Paragraph("<b>STATUS</b>", bold_style)
    ]]

    for p in parameters:
        stat = p["status"]
        if stat == "High":
            stat_color = colors.HexColor('#fbeae8')
            txt_color = colors.HexColor('#c0392b')
        elif stat == "Low":
            stat_color = colors.HexColor('#fef6e7')
            txt_color = colors.HexColor('#d35400')
        else:
            stat_color = colors.HexColor('#eafaf1')
            txt_color = colors.HexColor('#27ae60')

        table_rows.append([
            Paragraph(p["name"], body_style),
            Paragraph(str(p["value"]), bold_style),
            Paragraph(p["unit"], body_style),
            Paragraph(f"{p['min_ref']} - {p['max_ref']}", body_style),
            Paragraph(f"<font color='{txt_color}'><b>{stat}</b></font>", badge_style)
        ])

    param_table = Table(table_rows, colWidths=[180, 75, 75, 110, 100])
    param_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0d3b66')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('ALIGN', (1,0), (4,-1), 'CENTER'),
    ]))
    elements.append(param_table)
    elements.append(Spacer(1, 12))

    # 4. Clinical Highlights
    elements.append(Paragraph("2. CLINICAL OBSERVATIONS & KEY TAKEAWAYS", sec_title))
    en_highlights = summary_data.get("en_highlights", [])
    if en_highlights:
        for hl in en_highlights:
            elements.append(Paragraph(f"• {hl}", body_style))
            elements.append(Spacer(1, 3))
    else:
        elements.append(Paragraph("All tested parameters fall within healthy physiological ranges.", body_style))

    organ_insights = summary_data.get("organ_insights_en", [])
    if organ_insights:
        elements.append(Spacer(1, 4))
        for oi in organ_insights:
            elements.append(Paragraph(oi, body_style))
            elements.append(Spacer(1, 3))

    # 5. Diet & Lifestyle Guidance
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("3. RECOMMENDED LIFESTYLE & DIETARY ADVICE", sec_title))
    abnormal = [p for p in parameters if p["status"] != "Normal"]
    if abnormal:
        for p in abnormal[:3]:
            elements.append(Paragraph(f"<b>For {p['name']}:</b> {p.get('diet_en', 'Maintain balanced nutrition and follow physician guidance.')}", body_style))
            elements.append(Spacer(1, 3))
    else:
        elements.append(Paragraph("Maintain active hydration, balanced colorful diet, and 30 minutes of daily physical exercise.", body_style))

    # 6. Questions for Doctor Consultation
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("4. QUESTIONS TO ASK YOUR DOCTOR", sec_title))
    doc_qs = summary_data.get("doctor_questions", [])
    for q in doc_qs[:3]:
        elements.append(Paragraph(f"• {q}", body_style))
        elements.append(Spacer(1, 2))

    # 7. Disclaimer
    elements.append(Spacer(1, 15))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#cccccc'), spaceAfter=6))
    elements.append(Paragraph(
        "<b>MEDICAL DISCLAIMER:</b> This computer-generated summary uses optical character recognition and clinical natural language processing. "
        "It is designed solely for patient education and informational transparency. It does NOT constitute medical diagnosis, prescription, or clinical judgment. "
        "Always consult a qualified registered medical practitioner for interpretation and treatment decisions.",
        ParagraphStyle('Disc', parent=styles['Normal'], fontSize=7, leading=9, textColor=colors.HexColor('#777777'), alignment=1)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
