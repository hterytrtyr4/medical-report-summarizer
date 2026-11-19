"""
Generate sample PDF lab reports using ReportLab so that the user and evaluators
can directly upload and test realistic PDF medical reports.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

SAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))

def create_sample_pdf(title, subtitle, patient_info, test_rows, output_filename, impression):
    filepath = os.path.join(SAMPLES_DIR, output_filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#003366'),
        alignment=1, # Center
        spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'SubStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#555555'),
        alignment=1,
        spaceAfter=10
    )
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=11
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#111111')
    )

    elements.append(Paragraph(title, header_style))
    elements.append(Paragraph(subtitle, sub_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#003366'), spaceAfter=10))

    # Patient Details Table
    p_data = [
        [f"Patient: {patient_info['name']}", f"Age/Gender: {patient_info['age_gender']}"],
        [f"Ref Doctor: {patient_info['doctor']}", f"Date: {patient_info['date']}"],
        [f"Sample ID: {patient_info['id']}", f"Status: Final"]
    ]
    p_table = Table(p_data, colWidths=[270, 270])
    p_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(p_table)
    elements.append(Spacer(1, 12))

    # Test Table
    t_data = [["INVESTIGATION", "OBSERVED VALUE", "UNITS", "REFERENCE RANGE"]]
    for row in test_rows:
        t_data.append(row)

    test_table = Table(t_data, colWidths=[200, 100, 90, 150])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('ALIGN', (1,0), (2,-1), 'CENTER'),
    ]))
    elements.append(test_table)
    elements.append(Spacer(1, 14))

    # Impression
    elements.append(Paragraph(f"<b>CLINICAL IMPRESSION:</b> {impression}", ParagraphStyle(
        'ImpStyle', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#333333')
    )))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<i>*** This report is generated for academic demonstration and clinical reference ***</i>", ParagraphStyle(
        'FootStyle', parent=styles['Normal'], fontSize=8, alignment=1, textColor=colors.gray
    )))

    doc.build(elements)
    print(f"Created {output_filename}")

if __name__ == '__main__':
    # 1. CBC
    create_sample_pdf(
        "METROPATH DIAGNOSTIC CLINIC",
        "NABL Accredited & ISO Certified Lab | 124 Health Ave, Delhi",
        {"name": "Rajesh Kumar", "age_gender": "42 Y / Male", "doctor": "Dr. S. K. Sharma", "date": "18-Nov-2026", "id": "MP-892341"},
        [
            ["Hemoglobin (Hb)", "10.2", "g/dL", "13.0 - 17.0"],
            ["Total Leukocyte Count (WBC)", "12500", "/cumm", "4000 - 11000"],
            ["Red Blood Cell (RBC) Count", "4.1", "mil/cumm", "4.5 - 5.9"],
            ["Packed Cell Volume (PCV)", "32.0", "%", "40.0 - 50.0"],
            ["Mean Corpuscular Volume (MCV)", "78.0", "fL", "82.0 - 98.0"],
            ["Platelet Count", "240000", "/cumm", "150000 - 450000"],
            ["Erythrocyte Sedimentation Rate (ESR)", "28", "mm/hr", "0 - 15"]
        ],
        "sample_cbc.pdf",
        "Microcytic hypochromic anemia with leukocytosis and high ESR. Clinical correlation with iron profile recommended."
    )

    # 2. Lipid
    create_sample_pdf(
        "APOLLO CLINICAL DIAGNOSTICS",
        "Automated Lipid Profile Lab | MG Road, Bengaluru",
        {"name": "Sunita Verma", "age_gender": "48 Y / Female", "doctor": "Dr. Ananya Sen", "date": "17-Nov-2026", "id": "AP-542109"},
        [
            ["Total Cholesterol", "245.0", "mg/dL", "125.0 - 200.0"],
            ["Triglycerides", "220.0", "mg/dL", "50.0 - 150.0"],
            ["HDL Cholesterol (Good)", "38.0", "mg/dL", "40.0 - 60.0"],
            ["LDL Cholesterol (Bad)", "163.0", "mg/dL", "60.0 - 100.0"],
            ["VLDL Cholesterol", "44.0", "mg/dL", "5.0 - 30.0"],
            ["Cholesterol / HDL Ratio", "6.45", "Ratio", "3.3 - 4.4"]
        ],
        "sample_lipid.pdf",
        "Elevated total cholesterol, triglycerides, and LDL cholesterol indicating dyslipidemia and moderate cardiovascular risk."
    )

    # 3. Diabetes
    create_sample_pdf(
        "LAL PATHOLOGICAL SERVICES",
        "Diabetes Care & Biochemistry Centre | Connaught Place, New Delhi",
        {"name": "Ramesh Gupta", "age_gender": "54 Y / Male", "doctor": "Dr. Rajiv Mehra", "date": "18-Nov-2026", "id": "LP-994321"},
        [
            ["Fasting Blood Glucose", "158.0", "mg/dL", "70.0 - 99.0"],
            ["Post Prandial Glucose (PPBS)", "245.0", "mg/dL", "70.0 - 140.0"],
            ["HbA1c (Glycated Hemoglobin)", "8.4", "%", "4.0 - 5.6"],
            ["Estimated Average Glucose (eAG)", "194.0", "mg/dL", "70.0 - 126.0"]
        ],
        "sample_diabetes.pdf",
        "Elevated fasting and post-meal glucose with HbA1c 8.4% reflecting suboptimal glycemic control."
    )
