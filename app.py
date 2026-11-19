"""
app.py - Medical Report Summarizer Dashboard
Streamlit application for extracting, parsing, and explaining laboratory test reports
in simple Hindi and English using OCR and AI/NLP.
"""
import os
import glob
import pandas as pd
import streamlit as st

# Local modules
from extractor import extract_document_text, find_tesseract_path
from parser import extract_parameters, extract_patient_info
from summarizer import generate_llm_summary, generate_rule_based_summary
from visualizer import create_health_donut_chart, create_parameter_gauge
from pdf_generator import generate_summary_pdf

# Set page config
st.set_page_config(
    page_title="Medical Report Summarizer | AI & OCR",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished health-tech appearance
st.markdown("""
<style>
    /* Global Styles */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0d3b66;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #555555;
        margin-bottom: 1.2rem;
    }
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        margin-bottom: 12px;
    }
    .score-badge {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.1;
    }
    /* Status Badges */
    .badge-normal {
        background-color: #eafaf1;
        color: #27ae60;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-high {
        background-color: #fbeae8;
        color: #e74c3c;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-low {
        background-color: #fef6e7;
        color: #f39c12;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    /* Info Box */
    .patient-box {
        background-color: #f0f7ff;
        border-left: 5px solid #0077b6;
        padding: 12px 18px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 15px;
    }
    .disclaimer-box {
        background-color: #fff9db;
        border-left: 4px solid #f59f00;
        padding: 10px 14px;
        font-size: 0.85rem;
        color: #664d03;
        border-radius: 0 6px 6px 0;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "report_text" not in st.session_state:
    st.session_state.report_text = ""
if "filename" not in st.session_state:
    st.session_state.filename = ""
if "parsed_params" not in st.session_state:
    st.session_state.parsed_params = []
if "patient_info" not in st.session_state:
    st.session_state.patient_info = {}
if "summary_result" not in st.session_state:
    st.session_state.summary_result = None


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/medical-history.png", width=72)
    st.title("MedReport AI")
    st.caption("B.Tech (AI/ML) 5th Sem Project")
    st.markdown("---")

    # Language Preference
    st.subheader("🌐 Language / भाषा")
    lang_mode = st.radio(
        "Display Mode:",
        ["Bilingual (हिंदी + English)", "सरल हिंदी (Hindi Only)", "English Only"],
        index=0
    )

    st.markdown("---")
    # AI Engine Settings
    st.subheader("🤖 AI Settings")
    api_key_input = st.text_input(
        "Google Gemini API Key (Optional)",
        type="password",
        help="Optional. If left blank, the built-in deterministic clinical rule engine will run 100% offline!"
    )
    if api_key_input:
        st.success("✅ Custom Gemini Key Loaded")
    else:
        st.info("💡 Running in Clinical Rule-Based Mode (Fast & Offline)")

    st.markdown("---")
    # OCR Diagnostics
    st.subheader("🔍 OCR Engine Status")
    detected_tesseract = find_tesseract_path()
    if detected_tesseract:
        st.success(f"Tesseract OCR: Detected")
        st.caption(f"`{detected_tesseract}`")
    else:
        st.warning("Tesseract not found in PATH")
        st.caption("PDF extraction runs natively. For image OCR, install Tesseract or use sample PDFs.")

    st.markdown("---")
    # Quick Sample Report Loader
    st.subheader("📂 Quick Demo Samples")
    sample_choice = st.selectbox(
        "Load a Pre-configured Lab Report:",
        [
            "-- Select a Sample --",
            "Complete Blood Count (CBC - Anemia)",
            "Lipid Profile (High Cholesterol)",
            "Diabetic Evaluation (High Glucose)",
            "Kidney & Liver Panel (KFT + LFT)",
            "Thyroid Profile (Hypothyroidism)"
        ]
    )

    sample_mapping = {
        "Complete Blood Count (CBC - Anemia)": "sample_cbc.txt",
        "Lipid Profile (High Cholesterol)": "sample_lipid.txt",
        "Diabetic Evaluation (High Glucose)": "sample_diabetes.txt",
        "Kidney & Liver Panel (KFT + LFT)": "sample_kft_lft.txt",
        "Thyroid Profile (Hypothyroidism)": "sample_thyroid.txt"
    }

    if sample_choice in sample_mapping:
        sample_file_path = os.path.join(
            os.path.dirname(__file__), "sample_reports", sample_mapping[sample_choice]
        )
        if os.path.exists(sample_file_path):
            with open(sample_file_path, "r", encoding="utf-8") as sf:
                st.session_state.report_text = sf.read()
                st.session_state.filename = sample_mapping[sample_choice]
                st.session_state.patient_info = extract_patient_info(st.session_state.report_text)
                st.session_state.parsed_params = extract_parameters(st.session_state.report_text)
                st.session_state.summary_result = None
                st.toast(f"Loaded {sample_choice}!", icon="🩺")

    st.markdown("---")
    st.markdown(
        "<div style='font-size: 0.8rem; color: #7f8c8d; text-align: center;'>"
        "Designed for College Project Viva Defense<br>"
        "Tech: Streamlit · PyMuPDF · Tesseract · Gemini · Plotly · ReportLab"
        "</div>",
        unsafe_allow_html=True
    )


# ==========================================
# MAIN PAGE HEADER & UPLOADER
# ==========================================
st.markdown('<div class="main-title">🩺 Medical Report Summarizer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Lab reports ko simple Hindi aur English mein samjhein (LLM + OCR + Interactive Visualization)</div>', unsafe_allow_html=True)

# Upload Area
col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    uploaded_file = st.file_uploader(
        "Upload Medical Lab Report (PDF, PNG, JPG, or Scanned Document):",
        type=["pdf", "png", "jpg", "jpeg", "txt"],
        help="Upload digital laboratory PDFs or scanned images. Text will be extracted automatically."
    )

with col_up2:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Reset / Clear All", use_container_width=True):
        st.session_state.report_text = ""
        st.session_state.filename = ""
        st.session_state.parsed_params = []
        st.session_state.patient_info = {}
        st.session_state.summary_result = None
        st.rerun()

# Handle new file upload
if uploaded_file is not None and uploaded_file.name != st.session_state.filename:
    file_bytes = uploaded_file.read()
    with st.spinner("Extracting text and identifying lab parameters..."):
        text, err = extract_document_text(file_bytes, uploaded_file.name)
        if err:
            st.error(f"Extraction Error: {err}")
        else:
            st.session_state.report_text = text
            st.session_state.filename = uploaded_file.name
            st.session_state.patient_info = extract_patient_info(text)
            st.session_state.parsed_params = extract_parameters(text)
            st.session_state.summary_result = None
            st.success(f"Successfully processed {uploaded_file.name}!")


# ==========================================
# REPORT ANALYSIS VIEW
# ==========================================
if st.session_state.report_text:
    # Perform summary generation if not already cached
    if st.session_state.summary_result is None:
        with st.spinner("Analyzing parameters with medical intelligence engine..."):
            if api_key_input:
                st.session_state.summary_result = generate_llm_summary(
                    st.session_state.report_text,
                    st.session_state.parsed_params,
                    st.session_state.patient_info,
                    api_key=api_key_input
                )
            else:
                st.session_state.summary_result = generate_rule_based_summary(
                    st.session_state.patient_info,
                    st.session_state.parsed_params
                )

    patient_info = st.session_state.patient_info
    params = st.session_state.parsed_params
    summary = st.session_state.summary_result
    health_score = summary.get("health_score", {})

    # Patient Metadata Ribbon
    st.markdown(f"""
    <div class="patient-box">
        <div style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 15px;">
            <div>👤 <b>Patient:</b> {patient_info.get('name', 'N/A')}</div>
            <div>⚧ <b>Age / Gender:</b> {patient_info.get('age_gender', 'N/A')}</div>
            <div>📅 <b>Report Date:</b> {patient_info.get('date', 'Recent')}</div>
            <div>🩺 <b>Doctor:</b> {patient_info.get('doctor', 'N/A')}</div>
            <div>🏥 <b>Facility:</b> {patient_info.get('lab_name', 'Diagnostic Lab')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top KPI Metrics Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.85rem; color: #64748b;">Overall Health Index</div>
            <div class="score-badge" style="color: {health_score.get('color', '#0d3b66')};">{health_score.get('score', 85)}<span style="font-size: 1.1rem; color: #94a3b8;">/100</span></div>
            <div style="font-size: 0.8rem; color: #475569; margin-top: 4px;">{health_score.get('status', 'Stable')}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        norm_count = health_score.get("normal_count", 0)
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.85rem; color: #64748b;">Normal Parameters</div>
            <div class="score-badge" style="color: #27ae60;">{norm_count}</div>
            <div style="font-size: 0.8rem; color: #475569; margin-top: 4px;">Safe reference bounds</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        high_count = sum(1 for p in params if p["status"] == "High")
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.85rem; color: #64748b;">High Parameters (अधिक)</div>
            <div class="score-badge" style="color: #e74c3c;">{high_count}</div>
            <div style="font-size: 0.8rem; color: #475569; margin-top: 4px;">Above upper threshold</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        low_count = sum(1 for p in params if p["status"] == "Low")
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.85rem; color: #64748b;">Low Parameters (कम)</div>
            <div class="score-badge" style="color: #f39c12;">{low_count}</div>
            <div style="font-size: 0.8rem; color: #475569; margin-top: 4px;">Below lower threshold</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # Navigation Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Executive Summary (निष्कर्ष)",
        "📊 Visual Ranges & Gauges",
        "🇮🇳 सरल हिंदी समझ (Hindi)",
        "🇬🇧 Clinical English & Doctor Qs",
        "📥 Download PDF & Raw OCR"
    ])

    # ----------------------------------------------------
    # TAB 1: EXECUTIVE SUMMARY
    # ----------------------------------------------------
    with tab1:
        st.subheader("Key Findings & Synthesis")

        # LLM generated narrative if available
        if "ai_narrative" in summary:
            st.markdown("#### 🤖 AI Medical Assistant Synthesis (Gemini)")
            st.markdown(summary["ai_narrative"])
            st.markdown("---")
        else:
            if "llm_note" in summary:
                st.caption(f"ℹ️ {summary['llm_note']}")

        col_s1, col_s2 = st.columns([3, 2])
        with col_s1:
            st.markdown("#### 🚨 Out-of-Range Clinical Alerts")
            abnormals = [p for p in params if p["status"] != "Normal"]
            if abnormals:
                for ab in abnormals:
                    badge = f'<span class="badge-high">HIGH</span>' if ab["status"] == "High" else f'<span class="badge-low">LOW</span>'
                    st.markdown(f"""
                    <div style="padding: 10px; border-radius: 8px; background-color: #ffffff; border: 1px solid #e2e8f0; margin-bottom: 8px;">
                        <b>{ab['name']}</b>: <code>{ab['value']} {ab['unit']}</code> {badge}
                        <br><span style="font-size: 0.85rem; color: #64748b;">Normal Range: {ab['min_ref']} - {ab['max_ref']} {ab['unit']}</span>
                        <br><span style="font-size: 0.85rem; color: #334155;"><b>Impact:</b> {ab['high_en'] if ab['status'] == 'High' else ab['low_en']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("🎉 Excellent! All identified parameters fall strictly within normal physiological limits.")

            # Organ system highlights
            if summary.get("organ_insights_en"):
                st.markdown("#### 🩺 Organ System Observations")
                for insight in summary["organ_insights_en"]:
                    st.markdown(insight, unsafe_allow_html=True)

        with col_s2:
            st.markdown("#### 📈 Distribution")
            donut_fig = create_health_donut_chart(params)
            st.plotly_chart(donut_fig, use_container_width=True)

            # Quick Doctor Tips
            st.markdown("#### 👨‍⚕️ Quick Next Steps")
            st.info(
                "• Always share the original signed laboratory PDF with your physician.\n"
                "• Avoid self-adjusting medications without clinical prescription.\n"
                "• Repeat border-line abnormal tests in 4 to 6 weeks if recommended."
            )

    # ----------------------------------------------------
    # TAB 2: VISUAL RANGES & GAUGES
    # ----------------------------------------------------
    with tab2:
        st.subheader("Laboratory Test Value Gauges")
        st.caption("Each gauge visualizes your observed test result against the clinical reference interval (Green = Safe zone).")

        if params:
            # Display gauges in 2 columns
            gauge_cols = st.columns(2)
            for idx, p in enumerate(params):
                col_target = gauge_cols[idx % 2]
                with col_target:
                    g_fig = create_parameter_gauge(p)
                    st.plotly_chart(g_fig, use_container_width=True)

            # Interactive Table
            st.markdown("#### Detailed Parameter Data Table")
            df_params = pd.DataFrame([
                {
                    "Parameter": p["name"],
                    "Category": p["category"],
                    "Observed Value": p["value"],
                    "Unit": p["unit"],
                    "Reference Range": f"{p['min_ref']} - {p['max_ref']}",
                    "Status": p["status"],
                    "Hindi Status": p["status_hi"]
                }
                for p in params
            ])
            st.dataframe(df_params, use_container_width=True)
        else:
            st.warning("No standard parameters were detected to plot gauges. Please review the Raw Text tab.")

    # ----------------------------------------------------
    # TAB 3: HINDI EXPLANATION (सरल हिंदी समझ)
    # ----------------------------------------------------
    with tab3:
        st.subheader("🇮🇳 सरल हिंदी में संपूर्ण विश्लेषण (Patient-Friendly Hindi)")
        st.markdown(
            "यह खंड विशेष रूप से मरीजों और उनके परिजनों के लिए तैयार किया गया है, "
            "ताकि बिना किसी मेडिकल ज्ञान के रिपोर्ट को आसानी से समझा जा सके।"
        )

        # Hindi Highlights
        hi_highs = summary.get("hi_highlights", [])
        if hi_highs:
            st.markdown("#### 📌 मुख्य बिंदु:")
            for hh in hi_highs:
                st.markdown(f"• {hh}", unsafe_allow_html=True)
            st.markdown("---")

        # Organ level Hindi
        hi_organ = summary.get("organ_insights_hi", [])
        if hi_organ:
            st.markdown("#### 🩺 शरीर के अंगों पर प्रभाव:")
            for ho in hi_organ:
                st.markdown(ho, unsafe_allow_html=True)
            st.markdown("---")

        # Detailed breakdown per parameter
        st.markdown("#### 🔬 प्रत्येक टेस्ट का सरल हिंदी में अर्थ व घरेलू उपाय:")
        for p in params:
            with st.expander(f"🔹 {p['name']} — स्थिति: {p['status_hi']}"):
                st.markdown(f"**यह क्या है?** {p['meaning_hi']}")
                if p["status"] == "High":
                    st.markdown(f"**बढ़ने का कारण व असर:** 🔴 {p['high_hi']}")
                elif p["status"] == "Low":
                    st.markdown(f"**घटने का कारण व असर:** 🟠 {p['low_hi']}")
                else:
                    st.markdown("**स्थिति:** 🟢 यह टेस्ट बिल्कुल सामान्य सीमा के अंदर है। चिंता की बात नहीं है।")
                st.markdown(f"**खान-पान व दिनचर्या में क्या करें:** 🥗 {p['diet_hi']}")

        # Doctor questions in Hindi
        st.markdown("---")
        st.markdown("#### ❓ डॉक्टर के पास जाएं तो क्या पूछें?")
        for qh in summary.get("doctor_questions_hi", []):
            st.markdown(f"• **{qh}**")

    # ----------------------------------------------------
    # TAB 4: CLINICAL ENGLISH & DOCTOR QUESTIONS
    # ----------------------------------------------------
    with tab4:
        st.subheader("🇬🇧 Comprehensive Clinical English Analysis")

        en_highs = summary.get("en_highlights", [])
        if en_highs:
            st.markdown("#### Clinical Observations:")
            for eh in en_highs:
                st.markdown(f"• {eh}", unsafe_allow_html=True)
            st.markdown("---")

        st.markdown("#### Parameter Pathophysiology & Lifestyle Guidance:")
        for p in params:
            with st.expander(f"🔬 {p['name']} ({p['value']} {p['unit']}) — Status: {p['status']}"):
                st.markdown(f"**Biological Function:** {p['meaning_en']}")
                if p["status"] == "High":
                    st.markdown(f"**Elevated Clinical Significance:** ⚠️ {p['high_en']}")
                elif p["status"] == "Low":
                    st.markdown(f"**Low Clinical Significance:** ⚠️ {p['low_en']}")
                else:
                    st.markdown("**Status:** ✅ Optimal physiological range.")
                st.markdown(f"**Nutritional & Lifestyle Intervention:** 🥗 {p['diet_en']}")

        st.markdown("---")
        st.markdown("#### 🩺 Recommended Questions for Your Physician Consultation:")
        for eq in summary.get("doctor_questions", []):
            st.markdown(f"• {eq}")

    # ----------------------------------------------------
    # TAB 5: DOWNLOAD PDF & RAW OCR TEXT
    # ----------------------------------------------------
    with tab5:
        st.subheader("📥 Export Summary & Inspection")

        col_d1, col_d2 = st.columns([1, 1])
        with col_d1:
            st.markdown("#### 📄 Download Official PDF Summary")
            st.write("Generate a clean, printable PDF report containing the test table, clinical highlights, lifestyle recommendations, and physician consultation notes.")

            # Generate ReportLab PDF on demand
            try:
                pdf_bytes = generate_summary_pdf(patient_info, params, summary)
                clean_name = patient_info.get("name", "Patient").replace(" ", "_")
                st.download_button(
                    label="⬇️ Download Medical Summary PDF",
                    data=pdf_bytes,
                    file_name=f"Medical_Summary_{clean_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")

        with col_d2:
            st.markdown("#### 🔍 Extraction Transparency")
            st.caption(f"Processed file: `{st.session_state.filename}`")
            st.caption(f"Extracted parameters count: {len(params)}")
            st.caption(f"Engine: `{summary.get('engine', 'Clinical Rules')}`")

        st.markdown("---")
        st.markdown("#### 📝 Raw Extracted OCR / PDF Text")
        st.caption("Inspect the exact text parsed by the OCR/PyMuPDF pipeline before parameter extraction:")
        st.text_area("Extracted Text", st.session_state.report_text, height=300)

else:
    # Empty State - Welcome Banner & Quick Start
    st.info("👈 Please upload a medical lab report (PDF/Image) or select one of the pre-loaded sample reports from the sidebar to begin analysis!")

    st.markdown("""
    ### 🌟 How This Medical Summarizer Works
    
    ```mermaid
    flowchart LR
        A[Medical Report: PDF / Scanned Image] --> B[PyMuPDF / Tesseract OCR]
        B --> C[Text Normalization & Entity Parser]
        C --> D[Clinical Knowledge Base & Reference Range Engine]
        D --> E{AI Summarization Layer}
        E --> F[Google Gemini LLM: Empathetic Synthesis]
        E --> G[Clinical Rule Engine: 100% Offline Fallback]
        F --> H[Interactive Dashboard: Streamlit + Plotly]
        G --> H
        H --> I[Downloadable PDF: ReportLab]
    ```

    #### Key Capabilities:
    1. **Multi-Format Extraction:** Seamlessly reads digital PDFs, scanned documents, and camera photos.
    2. **Clinical Parameter Mapping:** Automatically detects Complete Blood Count (CBC), Lipid Profile, Blood Sugar / HbA1c, Liver Function (LFT), Kidney Function (KFT), and Thyroid (TSH/T3/T4).
    3. **Bilingual Clarity (सरल भाषा):** Bridges medical jargon by translating test meanings into simple Hindi and clear English.
    4. **Interactive Gauges:** Plotly visualizer immediately highlights safe green zones and out-of-bounds warning areas.
    5. **Exportable PDF:** Generates a patient-ready PDF summary with lifestyle advice and questions for the doctor.
    """)

# Footer Disclaimer
st.markdown("""
<div class="disclaimer-box">
    <b>⚠️ ACADEMIC & MEDICAL DISCLAIMER:</b> This application was developed as a B.Tech (AI/ML) academic project for educational demonstration.
    It utilizes optical character recognition and AI language processing. It is NOT intended to provide medical advice, diagnosis, or clinical treatment plans.
    Always seek the advice of a qualified physician with any questions regarding medical conditions or lab results.
</div>
""", unsafe_allow_html=True)
