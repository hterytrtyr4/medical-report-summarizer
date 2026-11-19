"""
app.py - Medical Report Summarizer Dashboard
Streamlit application for extracting, parsing, and explaining laboratory test reports
in simple Hindi and English using OCR and AI/NLP.
"""
import os
import hashlib
import pandas as pd
import streamlit as st

# Local modules
from extractor import extract_document_text, find_tesseract_path
from parser import extract_parameters, extract_patient_info
from summarizer import (
    generate_llm_summary,
    generate_rule_based_summary,
    answer_question_llm,
    answer_question_offline,
)
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


# ==========================================
# UI TEXT (English / Hindi)
# ==========================================
T = {
    "en": {
        "tab_summary": "📋 Executive Summary",
        "tab_gauges": "📊 Visual Ranges & Gauges",
        "tab_hindi": "🇮🇳 सरल हिंदी समझ (Hindi)",
        "tab_english": "🇬🇧 Clinical English & Doctor Qs",
        "tab_ask": "💬 Ask about your report",
        "tab_export": "📥 Download PDF & Raw OCR",
        "summary_h": "Key Findings & Synthesis",
        "ai_h": "🤖 AI Medical Assistant Synthesis",
        "alerts_h": "🚨 Out-of-Range Clinical Alerts",
        "normal_range": "Normal Range",
        "impact": "Impact",
        "all_ok": "🎉 Excellent! All identified parameters fall within normal limits.",
        "organ_h": "🩺 Organ System Observations",
        "dist_h": "📈 Distribution",
        "next_h": "👨‍⚕️ Quick Next Steps",
        "next_body": (
            "• Always share the original signed laboratory report with your physician.\n"
            "• Avoid self-adjusting medications without a prescription.\n"
            "• Repeat borderline abnormal tests in 4 to 6 weeks if recommended."
        ),
        "kpi_score": "Overall Health Index",
        "kpi_normal": "Normal Parameters",
        "kpi_high": "High Parameters",
        "kpi_low": "Low Parameters",
        "no_key_note": "ℹ️ Rule-based summary shown. Add a Gemini API key in the sidebar for a personalised AI summary.",
        "llm_err": "⚠️ Gemini could not be reached, so the built-in rule engine was used instead.",
        "ask_h": "💬 Ask a question about this report",
        "ask_hint": "e.g. What does my low hemoglobin mean? What should I eat?",
        "ask_btn": "Ask",
        "ask_none": "No questions yet.",
        "ask_offline": "Running without a Gemini key: only simple per-test answers are available. Add a key in the sidebar to ask anything.",
        "thinking": "Thinking...",
        "regen": "🔁 Regenerate summary",
    },
    "hi": {
        "tab_summary": "📋 मुख्य निष्कर्ष",
        "tab_gauges": "📊 रेंज और गेज",
        "tab_hindi": "🇮🇳 सरल हिंदी समझ",
        "tab_english": "🇬🇧 Clinical English",
        "tab_ask": "💬 रिपोर्ट के बारे में पूछें",
        "tab_export": "📥 PDF डाउनलोड व Raw Text",
        "summary_h": "मुख्य निष्कर्ष",
        "ai_h": "🤖 AI मेडिकल असिस्टेंट का सारांश",
        "alerts_h": "🚨 सामान्य सीमा से बाहर के टेस्ट",
        "normal_range": "सामान्य रेंज",
        "impact": "असर",
        "all_ok": "🎉 बहुत अच्छा! सभी टेस्ट सामान्य सीमा में हैं।",
        "organ_h": "🩺 शरीर के अंगों पर असर",
        "dist_h": "📈 वितरण",
        "next_h": "👨‍⚕️ आगे क्या करें",
        "next_body": (
            "• अपनी मूल लैब रिपोर्ट डॉक्टर को ज़रूर दिखाएं।\n"
            "• डॉक्टर की सलाह के बिना कोई दवा न बदलें।\n"
            "• यदि डॉक्टर कहें तो 4-6 हफ्ते बाद टेस्ट दोबारा कराएं।"
        ),
        "kpi_score": "कुल स्वास्थ्य सूचकांक",
        "kpi_normal": "सामान्य टेस्ट",
        "kpi_high": "सामान्य से अधिक",
        "kpi_low": "सामान्य से कम",
        "no_key_note": "ℹ️ अभी बिल्ट-इन नियम-आधारित सारांश दिख रहा है। AI सारांश के लिए साइडबार में Gemini API Key डालें।",
        "llm_err": "⚠️ Gemini से संपर्क नहीं हो सका, इसलिए बिल्ट-इन नियम-आधारित सारांश दिखाया गया।",
        "ask_h": "💬 इस रिपोर्ट के बारे में सवाल पूछें",
        "ask_hint": "जैसे: मेरा हीमोग्लोबिन कम है, इसका क्या मतलब है? क्या खाना चाहिए?",
        "ask_btn": "पूछें",
        "ask_none": "अभी कोई सवाल नहीं पूछा गया।",
        "ask_offline": "Gemini Key के बिना केवल सरल टेस्ट-वार जवाब मिलेंगे। कुछ भी पूछने के लिए साइडबार में Key डालें।",
        "thinking": "सोच रहा हूँ...",
        "regen": "🔁 सारांश दोबारा बनाएं",
    },
}

LANG_OPTIONS = {
    "Bilingual (हिंदी + English)": "bilingual",
    "सरल हिंदी (Hindi Only)": "hindi",
    "English Only": "english",
}

SAMPLE_MAPPING = {
    "Complete Blood Count (CBC - Anemia)": "sample_cbc.txt",
    "Lipid Profile (High Cholesterol)": "sample_lipid.txt",
    "Diabetic Evaluation (High Glucose)": "sample_diabetes.txt",
    "Kidney & Liver Panel (KFT + LFT)": "sample_kft_lft.txt",
    "Thyroid Profile (Hypothyroidism)": "sample_thyroid.txt",
}
SAMPLE_PLACEHOLDER = "-- Select a Sample --"


# ==========================================
# SESSION STATE
# ==========================================
_DEFAULTS = {
    "report_text": "",
    "filename": "",
    "parsed_params": [],
    "patient_info": {},
    "summary_cache": {},     # (report_hash, language, engine) -> summary dict
    "chat_history": [],
    "last_upload_id": None,
    "uploader_key": 0,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def get_secret_key() -> str:
    """Gemini key from Streamlit secrets or environment (set on Streamlit Cloud)."""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "").strip()


def load_report(text: str, filename: str):
    """Stores a new report and clears everything derived from the previous one."""
    st.session_state.report_text = text
    st.session_state.filename = filename
    st.session_state.patient_info = extract_patient_info(text)
    st.session_state.parsed_params = extract_parameters(text)
    st.session_state.summary_cache = {}
    st.session_state.chat_history = []


def clear_report():
    st.session_state.report_text = ""
    st.session_state.filename = ""
    st.session_state.parsed_params = []
    st.session_state.patient_info = {}
    st.session_state.summary_cache = {}
    st.session_state.chat_history = []


def on_sample_change():
    """Runs ONLY when the sample dropdown changes (not on every rerun)."""
    choice = st.session_state.get("sample_choice", SAMPLE_PLACEHOLDER)
    fname = SAMPLE_MAPPING.get(choice)
    if not fname:
        return
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_reports", fname)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as sf:
            load_report(sf.read(), fname)
        st.session_state.last_upload_id = None  # an old upload must not override the sample
        st.toast(f"Loaded {choice}!", icon="🩺")


def on_reset():
    clear_report()
    st.session_state.last_upload_id = None
    st.session_state.uploader_key += 1          # gives a fresh, empty uploader
    st.session_state.sample_choice = SAMPLE_PLACEHOLDER


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/medical-history.png", width=72)
    st.title("MedReport AI")
    st.caption("B.Tech (AI/ML) 5th Sem Project")
    st.markdown("---")

    st.subheader("🌐 Language / भाषा")
    lang_label = st.radio(
        "Display Mode:",
        list(LANG_OPTIONS.keys()),
        index=0,
        key="lang_mode_label",
    )
    lang_mode = LANG_OPTIONS[lang_label]          # "bilingual" | "hindi" | "english"
    ui = T["hi"] if lang_mode == "hindi" else T["en"]

    st.markdown("---")
    st.subheader("🤖 AI Settings")
    typed_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        help="Free key: https://aistudio.google.com/app/apikey. Leave blank to use the built-in offline rule engine.",
    ).strip()
    secret_key = get_secret_key()
    api_key = typed_key or secret_key
    if typed_key:
        st.success("✅ Using the Gemini key you entered")
    elif secret_key:
        st.success("✅ Using Gemini key from app secrets")
    else:
        st.info("💡 No key: running in offline rule-based mode")

    st.markdown("---")
    st.subheader("🔍 OCR Engine Status")
    detected_tesseract = find_tesseract_path()
    if detected_tesseract:
        st.success("Tesseract OCR: Detected")
        st.caption(f"`{detected_tesseract}`")
    else:
        st.warning("Tesseract not found in PATH")
        st.caption("PDF text extraction works natively. Image OCR needs Tesseract.")

    st.markdown("---")
    st.subheader("📂 Quick Demo Samples")
    st.selectbox(
        "Load a Pre-configured Lab Report:",
        [SAMPLE_PLACEHOLDER] + list(SAMPLE_MAPPING.keys()),
        key="sample_choice",
        on_change=on_sample_change,
    )

    st.markdown("---")
    st.markdown(
        "<div style='font-size: 0.8rem; color: #7f8c8d; text-align: center;'>"
        "Tech: Streamlit · PyMuPDF · Tesseract · Gemini · Plotly · ReportLab"
        "</div>",
        unsafe_allow_html=True,
    )


# ==========================================
# HEADER & UPLOADER
# ==========================================
st.markdown('<div class="main-title">🩺 Medical Report Summarizer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Lab reports ko simple Hindi aur English mein samjhein (LLM + OCR + Interactive Visualization)</div>', unsafe_allow_html=True)

col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    uploaded_file = st.file_uploader(
        "Upload Medical Lab Report (PDF, PNG, JPG, or TXT):",
        type=["pdf", "png", "jpg", "jpeg", "txt"],
        key=f"uploader_{st.session_state.uploader_key}",
        help="Upload digital laboratory PDFs or scanned images. Text is extracted automatically.",
    )
with col_up2:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("🔄 Reset / Clear All", use_container_width=True, on_click=on_reset)

# Process a NEW upload exactly once (file_id changes for every new upload)
if uploaded_file is not None:
    upload_id = getattr(uploaded_file, "file_id", None) or f"{uploaded_file.name}:{uploaded_file.size}"
    if upload_id != st.session_state.last_upload_id:
        st.session_state.last_upload_id = upload_id
        with st.spinner("Extracting text and identifying lab parameters..."):
            text, err = extract_document_text(uploaded_file.getvalue(), uploaded_file.name)
        if err:
            st.error(f"Extraction Error: {err}")
        else:
            load_report(text, uploaded_file.name)
            st.success(f"Successfully processed {uploaded_file.name}!")


def get_summary(language: str) -> dict:
    """
    Returns the summary for (this report, this language, this engine).
    Generated once and cached, so switching language regenerates it
    and normal reruns never call the LLM again.
    """
    text = st.session_state.report_text
    report_hash = hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()
    engine = "gemini" if api_key else "rules"
    cache_key = (report_hash, language, engine)
    cache = st.session_state.summary_cache
    if cache_key not in cache:
        if api_key:
            with st.spinner("Generating your personalised summary with Gemini..."):
                cache[cache_key] = generate_llm_summary(
                    text,
                    st.session_state.parsed_params,
                    st.session_state.patient_info,
                    api_key=api_key,
                    language=language,
                )
        else:
            cache[cache_key] = generate_rule_based_summary(
                st.session_state.patient_info, st.session_state.parsed_params
            )
            cache[cache_key]["llm_note"] = "no_key"
    return cache[cache_key]


# ==========================================
# REPORT ANALYSIS VIEW
# ==========================================
if st.session_state.report_text:
    patient_info = st.session_state.patient_info
    params = st.session_state.parsed_params
    summary = get_summary(lang_mode)
    health_score = summary.get("health_score", {})
    show_hi = lang_mode in ("hindi", "bilingual")
    show_en = lang_mode in ("english", "bilingual")

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

    # KPI row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    high_count = sum(1 for p in params if p["status"] == "High")
    low_count = sum(1 for p in params if p["status"] == "Low")
    with kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.85rem; color: #64748b;">{ui['kpi_score']}</div>
            <div class="score-badge" style="color: {health_score.get('color', '#0d3b66')};">{health_score.get('score') if health_score.get('score') is not None else 'N/A'}{ '<span style="font-size: 1.1rem; color: #94a3b8;">/100</span>' if health_score.get('score') is not None else ''}</div>
            <div style="font-size: 0.8rem; color: #475569; margin-top: 4px;">{health_score.get('status', 'Stable')}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.85rem; color: #64748b;">{ui['kpi_normal']}</div>
            <div class="score-badge" style="color: #27ae60;">{health_score.get("normal_count", 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.85rem; color: #64748b;">{ui['kpi_high']}</div>
            <div class="score-badge" style="color: #e74c3c;">{high_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.85rem; color: #64748b;">{ui['kpi_low']}</div>
            <div class="score-badge" style="color: #f39c12;">{low_count}</div>
        </div>
        """, unsafe_allow_html=True)

    # Tabs depend on the selected language
    tab_defs = [("summary", ui["tab_summary"]), ("gauges", ui["tab_gauges"])]
    if show_hi:
        tab_defs.append(("hindi", ui["tab_hindi"]))
    if show_en:
        tab_defs.append(("english", ui["tab_english"]))
    tab_defs += [("ask", ui["tab_ask"]), ("export", ui["tab_export"])]
    tabs = dict(zip([k for k, _ in tab_defs], st.tabs([label for _, label in tab_defs])))

    # ---------------- SUMMARY ----------------
    with tabs["summary"]:
        st.subheader(ui["summary_h"])

        if "ai_narrative" in summary:
            st.markdown(f"#### {ui['ai_h']}")
            st.caption(f"Engine: {summary.get('engine', '')}")
            st.markdown(summary["ai_narrative"])
            st.markdown("---")
        else:
            note = summary.get("llm_note", "")
            if note == "no_key":
                st.caption(ui["no_key_note"])
            elif note.startswith("error:"):
                st.warning(ui["llm_err"])
                st.caption(note[6:].strip())

        if api_key and st.button(ui["regen"], key="regen_btn"):
            st.session_state.summary_cache = {}
            st.rerun()

        col_s1, col_s2 = st.columns([3, 2])
        with col_s1:
            st.markdown(f"#### {ui['alerts_h']}")
            abnormals = [p for p in params if p["status"] != "Normal"]
            if not params:
                st.warning("No test values were detected. No health status can be inferred. Check the Raw OCR Text below or upload a clearer, well-lit report image / searchable PDF.")
            elif abnormals:
                for ab in abnormals:
                    is_high = ab["status"] == "High"
                    badge = '<span class="badge-high">HIGH</span>' if is_high else '<span class="badge-low">LOW</span>'
                    if lang_mode == "hindi":
                        impact = ab["high_hi"] if is_high else ab["low_hi"]
                    elif lang_mode == "english":
                        impact = ab["high_en"] if is_high else ab["low_en"]
                    else:
                        impact = (ab["high_en"] if is_high else ab["low_en"]) + "<br>" + (ab["high_hi"] if is_high else ab["low_hi"])
                    st.markdown(f"""
                    <div style="padding: 10px; border-radius: 8px; background-color: #ffffff; border: 1px solid #e2e8f0; margin-bottom: 8px;">
                        <b>{ab['name']}</b>: <code>{ab['value']} {ab['unit']}</code> {badge}
                        <br><span style="font-size: 0.85rem; color: #64748b;">{ui['normal_range']}: {ab['min_ref']} - {ab['max_ref']} {ab['unit']}</span>
                        <br><span style="font-size: 0.85rem; color: #334155;"><b>{ui['impact']}:</b> {impact}</span>
                    </div>
                    """, unsafe_allow_html=True)
            elif params:
                st.success(ui["all_ok"])

            organ_en = summary.get("organ_insights_en", [])
            organ_hi = summary.get("organ_insights_hi", [])
            if organ_en or organ_hi:
                st.markdown(f"#### {ui['organ_h']}")
                if show_en:
                    for insight in organ_en:
                        st.markdown(insight, unsafe_allow_html=True)
                if show_hi:
                    for insight in organ_hi:
                        st.markdown(insight, unsafe_allow_html=True)

        with col_s2:
            st.markdown(f"#### {ui['dist_h']}")
            st.plotly_chart(create_health_donut_chart(params), use_container_width=True)
            st.markdown(f"#### {ui['next_h']}")
            st.info(ui["next_body"])

    # ---------------- GAUGES ----------------
    with tabs["gauges"]:
        st.subheader("Laboratory Test Value Gauges" if lang_mode != "hindi" else "टेस्ट वैल्यू गेज")
        if params:
            gauge_cols = st.columns(2)
            for idx, p in enumerate(params):
                with gauge_cols[idx % 2]:
                    st.plotly_chart(create_parameter_gauge(p), use_container_width=True, key=f"gauge_{idx}")

            rows = []
            for p in params:
                row = {
                    "Parameter": p["name"],
                    "Category": p["category"],
                    "Observed Value": p["value"],
                    "Unit": p["unit"],
                    "Reference Range": f"{p['min_ref']} - {p['max_ref']}",
                }
                if show_en:
                    row["Status"] = p["status"]
                if show_hi:
                    row["स्थिति"] = p["status_hi"]
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.warning("No standard parameters were detected. Please review the Raw Text tab.")

    # ---------------- HINDI ----------------
    if show_hi:
        with tabs["hindi"]:
            st.subheader("🇮🇳 सरल हिंदी में संपूर्ण विश्लेषण")
            hi_highs = summary.get("hi_highlights", [])
            if hi_highs:
                st.markdown("#### 📌 मुख्य बिंदु:")
                for hh in hi_highs:
                    st.markdown(f"• {hh}", unsafe_allow_html=True)
                st.markdown("---")
            hi_organ = summary.get("organ_insights_hi", [])
            if hi_organ:
                st.markdown("#### 🩺 शरीर के अंगों पर प्रभाव:")
                for ho in hi_organ:
                    st.markdown(ho, unsafe_allow_html=True)
                st.markdown("---")
            st.markdown("#### 🔬 प्रत्येक टेस्ट का सरल हिंदी में अर्थ व घरेलू उपाय:")
            for p in params:
                with st.expander(f"🔹 {p['name']} — स्थिति: {p['status_hi']}"):
                    st.markdown(f"**यह क्या है?** {p['meaning_hi']}")
                    if p["status"] == "High":
                        st.markdown(f"**बढ़ने का कारण व असर:** 🔴 {p['high_hi']}")
                    elif p["status"] == "Low":
                        st.markdown(f"**घटने का कारण व असर:** 🟠 {p['low_hi']}")
                    else:
                        st.markdown("**स्थिति:** 🟢 यह टेस्ट सामान्य सीमा के अंदर है। चिंता की बात नहीं है।")
                    st.markdown(f"**खान-पान व दिनचर्या में क्या करें:** 🥗 {p['diet_hi']}")
            st.markdown("---")
            st.markdown("#### ❓ डॉक्टर के पास जाएं तो क्या पूछें?")
            for qh in summary.get("doctor_questions_hi", []):
                st.markdown(f"• **{qh}**")

    # ---------------- ENGLISH ----------------
    if show_en:
        with tabs["english"]:
            st.subheader("🇬🇧 Comprehensive Clinical English Analysis")
            en_highs = summary.get("en_highlights", [])
            if en_highs:
                st.markdown("#### Clinical Observations:")
                for eh in en_highs:
                    st.markdown(f"• {eh}", unsafe_allow_html=True)
                st.markdown("---")
            st.markdown("#### Parameter Details & Lifestyle Guidance:")
            for p in params:
                with st.expander(f"🔬 {p['name']} ({p['value']} {p['unit']}) — Status: {p['status']}"):
                    st.markdown(f"**Biological Function:** {p['meaning_en']}")
                    if p["status"] == "High":
                        st.markdown(f"**Elevated Clinical Significance:** ⚠️ {p['high_en']}")
                    elif p["status"] == "Low":
                        st.markdown(f"**Low Clinical Significance:** ⚠️ {p['low_en']}")
                    else:
                        st.markdown("**Status:** ✅ Within the normal range.")
                    st.markdown(f"**Nutritional & Lifestyle Intervention:** 🥗 {p['diet_en']}")
            st.markdown("---")
            st.markdown("#### 🩺 Questions for Your Physician:")
            for eq in summary.get("doctor_questions", []):
                st.markdown(f"• {eq}")

    # ---------------- ASK ----------------
    with tabs["ask"]:
        st.subheader(ui["ask_h"])
        if not api_key:
            st.caption(ui["ask_offline"])

        history = st.session_state.chat_history
        if not history:
            st.caption(ui["ask_none"])
        for msg in history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        with st.form("ask_form", clear_on_submit=True):
            question = st.text_area("Question", placeholder=ui["ask_hint"], label_visibility="collapsed", height=80)
            submitted = st.form_submit_button(ui["ask_btn"])

        if submitted and question.strip():
            q = question.strip()
            if api_key:
                with st.spinner(ui["thinking"]):
                    answer, err = answer_question_llm(
                        q, history, params, patient_info,
                        st.session_state.report_text, api_key, lang_mode,
                    )
                if not answer:
                    answer = f"⚠️ {ui['llm_err']}\n\n`{err}`\n\n" + answer_question_offline(q, params, lang_mode)
            else:
                answer = answer_question_offline(q, params, lang_mode)
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": answer})
            st.rerun()

    # ---------------- EXPORT ----------------
    with tabs["export"]:
        st.subheader("📥 Export Summary & Inspection")
        col_d1, col_d2 = st.columns([1, 1])
        with col_d1:
            st.markdown("#### 📄 Download PDF Summary")
            st.write("Printable English PDF with the test table, highlights, lifestyle tips and questions for your doctor.")
            try:
                pdf_bytes = generate_summary_pdf(patient_info, params, summary)
                clean_name = patient_info.get("name", "Patient").replace(" ", "_")
                st.download_button(
                    label="⬇️ Download Medical Summary PDF",
                    data=pdf_bytes,
                    file_name=f"Medical_Summary_{clean_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
        with col_d2:
            st.markdown("#### 🔍 Extraction Transparency")
            st.caption(f"Processed file: `{st.session_state.filename}`")
            st.caption(f"Extracted parameters: {len(params)}")
            st.caption(f"Engine: `{summary.get('engine', 'Clinical Rules')}`")
        st.markdown("---")
        st.markdown("#### 📝 Raw Extracted OCR / PDF Text")
        st.text_area("Extracted Text", st.session_state.report_text, height=300)

else:
    st.info("👈 Upload a medical lab report (PDF/Image) or pick a sample report from the sidebar to begin.")
    st.markdown("#### 🌟 How This Medical Summarizer Works")
    st.graphviz_chart("""
    digraph G {
        rankdir=LR; node [shape=box, style=rounded];
        A [label="PDF / Image report"]; B [label="PyMuPDF / Tesseract OCR"];
        C [label="Parameter parser"]; D [label="Reference-range engine"];
        E [label="Gemini LLM (or offline rules)"]; F [label="Dashboard + Q&A"]; G [label="PDF export"];
        A -> B -> C -> D -> E -> F -> G;
    }
    """)
    st.markdown("""
    1. **Multi-format extraction:** digital PDFs, scanned documents and photos.
    2. **Parameter mapping:** CBC, lipid, sugar/HbA1c, liver, kidney and thyroid tests.
    3. **Language switch:** Bilingual, Hindi-only or English-only; the AI summary is regenerated in the chosen language.
    4. **Ask questions:** chat about your own report in Hindi or English.
    5. **Export:** printable PDF summary.
    """)

st.markdown("""
<div class="disclaimer-box">
    <b>⚠️ ACADEMIC & MEDICAL DISCLAIMER:</b> This application is a B.Tech (AI/ML) academic project for educational demonstration.
    It uses optical character recognition and AI language processing and is NOT medical advice, diagnosis, or a treatment plan.
    Always consult a qualified physician about your lab results.
</div>
""", unsafe_allow_html=True)
