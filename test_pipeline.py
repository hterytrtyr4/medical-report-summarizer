"""
test_pipeline.py - Comprehensive Unit & Pipeline Verification
Tests OCR/PDF extraction, parameter parsing, clinical summarization,
Plotly visualizer generation, and ReportLab PDF compilation.
"""
import os
import sys
from extractor import extract_document_text
from parser import extract_parameters, extract_patient_info
from summarizer import generate_rule_based_summary
from visualizer import create_health_donut_chart, create_parameter_gauge
from pdf_generator import generate_summary_pdf

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "sample_reports")

def test_cbc_sample():
    print("Testing CBC sample text...")
    cbc_path = os.path.join(SAMPLES_DIR, "sample_cbc.txt")
    with open(cbc_path, "r", encoding="utf-8") as f:
        text = f.read()

    patient_info = extract_patient_info(text)
    print("Patient Info:", patient_info)
    assert patient_info["name"] == "Rajesh Kumar", f"Expected Rajesh Kumar, got {patient_info['name']}"

    params = extract_parameters(text)
    print(f"Extracted {len(params)} parameters:")
    for p in params:
        print(f"  - {p['name']}: {p['value']} {p['unit']} [{p['status']}] (Normal: {p['min_ref']}-{p['max_ref']})")

    assert len(params) >= 5, f"Expected at least 5 parameters, got {len(params)}"

    # Test summary
    summary = generate_rule_based_summary(patient_info, params)
    print("Health Score:", summary["health_score"])
    print("Highlights (EN):", len(summary["en_highlights"]))
    print("Highlights (HI):", len(summary["hi_highlights"]))

    # Test visualizers
    donut = create_health_donut_chart(params)
    gauge = create_parameter_gauge(params[0])
    assert donut is not None
    assert gauge is not None

    # Test PDF generation
    pdf_bytes = generate_summary_pdf(patient_info, params, summary)
    print(f"Generated PDF size: {len(pdf_bytes)} bytes")
    assert len(pdf_bytes) > 1000, "PDF bytes should be non-trivial"

    print("✅ All CBC tests passed successfully!\n")

def test_pdf_extraction():
    print("Testing sample PDF extraction (PyMuPDF)...")
    pdf_path = os.path.join(SAMPLES_DIR, "sample_lipid.pdf")
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    text, err = extract_document_text(pdf_bytes, "sample_lipid.pdf")
    assert err is None, f"PDF extraction error: {err}"
    assert "Cholesterol" in text, f"Extracted text missing Cholesterol keyword: {text[:200]}"
    
    params = extract_parameters(text)
    print(f"Extracted {len(params)} parameters from PDF:")
    for p in params:
        print(f"  - {p['name']}: {p['value']} {p['unit']} [{p['status']}]")
    assert len(params) >= 3, f"Expected at least 3 parameters from Lipid PDF, got {len(params)}"

    print("✅ All PDF extraction tests passed successfully!\n")

if __name__ == "__main__":
    test_cbc_sample()
    test_pdf_extraction()
    print("🎉 FULL PIPELINE TEST PASSED 100%!")
