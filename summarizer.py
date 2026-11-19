"""
summarizer.py - Bilingual AI & Clinical Rule-Based Medical Summarization Engine
Generates patient-friendly explanations in Hindi, English, and Hinglish.
Integrates Google Gemini LLM with robust deterministic fallback.
"""
import os
from typing import Dict, List, Any, Optional, Tuple

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def calculate_health_score(parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates an aggregate health indicator score out of 100 based on test results.
    """
    if not parameters:
        return {"score": 100, "status": "No Tests Detected", "color": "#7f8c8d"}

    total = len(parameters)
    normal_count = sum(1 for p in parameters if p["status"] == "Normal")
    abnormal_count = total - normal_count

    # Base calculation
    score = int(max(30, 100 - (abnormal_count * 18)))

    if abnormal_count == 0:
        status_label = "Optimal / All Parameters Normal (उत्कृष्ट)"
        color = "#27ae60"
    elif abnormal_count <= 2:
        status_label = "Mild Attention Needed (हल्की सावधानी अपेक्षित)"
        color = "#f39c12"
    else:
        status_label = "Consultation Recommended (चिकित्सीय परामर्श आवश्यक)"
        color = "#e74c3c"

    return {
        "score": score,
        "status": status_label,
        "color": color,
        "normal_count": normal_count,
        "abnormal_count": abnormal_count,
        "total_count": total
    }


def generate_rule_based_summary(patient_info: Dict[str, str], parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministic clinical rule engine that generates rich Hindi and English summaries.
    Guarantees 100% availability even without an internet connection or API key.
    """
    high_items = [p for p in parameters if p["status"] == "High"]
    low_items = [p for p in parameters if p["status"] == "Low"]
    normal_items = [p for p in parameters if p["status"] == "Normal"]

    # English Summary Highlights
    en_highlights = []
    if high_items:
        en_highlights.append(f"Elevated levels noted in {len(high_items)} parameter(s): " + ", ".join([f"<b>{p['name']}</b> ({p['value']} {p['unit']})" for p in high_items]))
    if low_items:
        en_highlights.append(f"Sub-optimal / low levels found in {len(low_items)} parameter(s): " + ", ".join([f"<b>{p['name']}</b> ({p['value']} {p['unit']})" for p in low_items]))
    if normal_items:
        en_highlights.append(f"{len(normal_items)} parameter(s) within normal clinical limits: " + ", ".join([p['name'] for p in normal_items]))

    # Hindi Summary Highlights
    hi_highlights = []
    if high_items:
        hi_highlights.append(f"<b>{len(high_items)} टेस्ट में वैल्यू सामान्य से अधिक (High) पाई गई:</b> " + ", ".join([f"{p['name']} ({p['value']} {p['unit']})" for p in high_items]))
    if low_items:
        hi_highlights.append(f"<b>{len(low_items)} टेस्ट में वैल्यू सामान्य से कम (Low) पाई गई:</b> " + ", ".join([f"{p['name']} ({p['value']} {p['unit']})" for p in low_items]))
    if normal_items:
        hi_highlights.append(f"<b>{len(normal_items)} टेस्ट पूरी तरह सामान्य (Normal) रेंज में हैं।</b>")

    # Specific organ insights
    organ_insights_en = []
    organ_insights_hi = []

    # CBC insights
    cbc_abnormal = [p for p in parameters if p.get("category") == "Complete Blood Count (CBC)" and p["status"] != "Normal"]
    if cbc_abnormal:
        hb_item = next((p for p in parameters if p["key"] == "hemoglobin"), None)
        wbc_item = next((p for p in parameters if p["key"] == "wbc"), None)
        if hb_item and hb_item["status"] == "Low":
            organ_insights_en.append("• <b>Anemia Detected:</b> Low hemoglobin indicates your tissues may receive less oxygen, leading to weakness and fatigue.")
            organ_insights_hi.append("• <b>एनीमिया (खून की कमी):</b> हीमोग्लोबिन कम होने से शरीर के अंगों तक पर्याप्त ऑक्सीजन नहीं पहुंचती, जिससे जल्दी थकान और कमजोरी महसूस होती है।")
        if wbc_item and wbc_item["status"] == "High":
            organ_insights_en.append("• <b>Immune Activation:</b> High white blood cell count reflects your immune system fighting an ongoing infection or inflammatory trigger.")
            organ_insights_hi.append("• <b>इन्फेक्शन / सूजन:</b> WBC बढ़ने का अर्थ है कि शरीर की रोग प्रतिरोधक प्रणाली किसी संक्रमण से लड़ रही है।")

    # Lipid insights
    lipid_abnormal = [p for p in parameters if p.get("category") == "Lipid Profile (Fat/Heart)" and p["status"] != "Normal"]
    if lipid_abnormal:
        organ_insights_en.append("• <b>Lipid Imbalance (Dyslipidemia):</b> High cholesterol/triglycerides can lead to plaque buildup in coronary arteries, requiring dietary control and regular cardio exercise.")
        organ_insights_hi.append("• <b>कोलेस्ट्रॉल का असंतुलन:</b> खून में फैट बढ़ने से दिल की धमनियों में रुकावट का खतरा बढ़ सकता है। चिकनाई वाला भोजन कम करना आवश्यक है।")

    # Diabetes insights
    sugar_abnormal = [p for p in parameters if p.get("category") == "Diabetes / Blood Sugar" and p["status"] != "Normal"]
    if sugar_abnormal:
        organ_insights_en.append("• <b>Blood Sugar Dysregulation:</b> Elevated glucose or HbA1c suggests insulin resistance or diabetic tendency. Strict carbohydrate restriction recommended.")
        organ_insights_hi.append("• <b>शुगर नियंत्रण में कमी:</b> ग्लूकोज या HbA1c का बढ़ा होना डायबिटीज की संभावना दर्शाता है। मीठा और मैदा तुरंत बंद करें।")

    # Kidney / Liver insights
    kft_lft_abnormal = [p for p in parameters if ("Kidney" in p.get("category", "") or "Liver" in p.get("category", "")) and p["status"] != "Normal"]
    if kft_lft_abnormal:
        organ_insights_en.append("• <b>Hepato-Renal Indicators:</b> Altered creatinine or liver enzymes warrant hydration, avoiding nephrotoxic medications, and specialist consultation.")
        organ_insights_hi.append("• <b>लिवर या गुर्दे का संकेत:</b> क्रीटिनिन या लिवर एंजाइम बढ़ना अंगों पर दबाव दर्शाता है। पर्याप्त पानी पिएं और बिना डॉक्टर दर्द की दवा न लें।")

    # Doctor questions
    doctor_questions = [
        "What is the most likely root cause for the out-of-range parameters observed?",
        "Do I need any confirmatory imaging (Ultrasound, ECG, Repeat Lab in 4 weeks)?",
        "Should I begin medication, or can these values be managed through structured diet and exercise?",
        "Are any of my current daily medications or supplements affecting these laboratory numbers?"
    ]

    doctor_questions_hi = [
        "इन असामान्‍य (High/Low) नतीजों का मुख्य कारण क्या हो सकता है?",
        "क्या मुझे 4 हफ्ते बाद दोबारा टेस्ट या अल्ट्रासाउंड कराने की जरूरत है?",
        "क्या इसके लिए दवा शुरू करनी होगी या केवल खान-पान और कसरत से नियंत्रण संभव है?",
        "क्या मेरी कोई वर्तमान दवा इन नतीजों पर असर डाल रही है?"
    ]

    return {
        "engine": "Clinical Rule-Based Engine",
        "en_highlights": en_highlights,
        "hi_highlights": hi_highlights,
        "organ_insights_en": organ_insights_en,
        "organ_insights_hi": organ_insights_hi,
        "doctor_questions": doctor_questions,
        "doctor_questions_hi": doctor_questions_hi,
        "health_score": calculate_health_score(parameters)
    }


LANG_MODES = ("bilingual", "hindi", "english")

LANG_INSTRUCTIONS = {
    "bilingual": (
        "Write every section twice: first in simple everyday Hindi (Devanagari script), "
        "then in plain English. Keep test names and units in English."
    ),
    "hindi": (
        "Write the ENTIRE response ONLY in simple, everyday Hindi (Devanagari script). "
        "Do not write English sentences. Test names and units may stay in English."
    ),
    "english": (
        "Write the ENTIRE response ONLY in plain, simple English. Do not use Hindi."
    ),
}

SECTION_HEADINGS = {
    "bilingual": [
        "### 1. मुख्य निष्कर्ष / Key Takeaways",
        "### 2. सभी नतीजों का मतलब / What the results mean together",
        "### 3. खान-पान और दिनचर्या / Diet & Lifestyle",
        "### 4. डॉक्टर से क्या पूछें / Questions for your doctor",
    ],
    "hindi": [
        "### 1. मुख्य निष्कर्ष",
        "### 2. सभी नतीजों का मतलब",
        "### 3. खान-पान और दिनचर्या में सुधार",
        "### 4. डॉक्टर से क्या पूछें",
    ],
    "english": [
        "### 1. Key Takeaways",
        "### 2. What the Results Mean Together",
        "### 3. Diet & Lifestyle Guidance",
        "### 4. Questions to Ask Your Doctor",
    ],
}

# Models are tried in order; override the first with the GEMINI_MODEL env var / secret.
DEFAULT_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]


def _model_candidates() -> List[str]:
    custom = os.getenv("GEMINI_MODEL")
    models = ([custom] if custom else []) + DEFAULT_MODELS
    seen, out = set(), []
    for m in models:
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _call_gemini(prompt: str, api_key: str, temperature: float = 0.6) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Calls Gemini, trying each candidate model. Returns (text, model_used, error).
    """
    if not GEMINI_AVAILABLE:
        return None, None, "google-genai package is not installed."
    last_err = None
    client = genai.Client(api_key=api_key)
    for model in _model_candidates():
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temperature),
            )
            text = (response.text or "").strip()
            if text:
                return text, model, None
            last_err = f"{model} returned an empty response."
        except Exception as e:  # bad key, quota, model not found, offline...
            last_err = f"{model}: {str(e)[:200]}"
    return None, None, last_err


def _findings_text(parameters: List[Dict[str, Any]]) -> str:
    lines = [
        f"- {p['name']}: {p['value']} {p['unit']} "
        f"(Reference: {p['min_ref']} - {p['max_ref']} {p['unit']}) -> {p['status']}"
        for p in parameters
    ]
    return "\n".join(lines) if lines else "No numeric parameters were parsed automatically."


def build_summary_prompt(
    raw_text: str,
    parameters: List[Dict[str, Any]],
    patient_info: Dict[str, str],
    language: str = "bilingual",
) -> str:
    """Builds the Gemini prompt. The output language is controlled by `language`."""
    language = language if language in LANG_MODES else "bilingual"
    headings = "\n".join(SECTION_HEADINGS[language])
    return f"""You are a compassionate medical communicator explaining a laboratory report to a patient with no medical background.

LANGUAGE RULE (very important): {LANG_INSTRUCTIONS[language]}

PATIENT:
Name: {patient_info.get('name', 'Patient')}
Age / Gender: {patient_info.get('age_gender', 'Not specified')}
Report date: {patient_info.get('date', 'Recent')}

EXTRACTED PARAMETERS:
{_findings_text(parameters)}

RAW REPORT TEXT (for extra context):
{raw_text[:3000]}

Write clean Markdown using exactly these four sections:
{headings}

Rules:
- Base everything on the numbers above; mention specific test names and values.
- Be calm and reassuring, never alarming. Say whether follow-up is routine or should be prompt.
- Section 3 must give 3-4 practical diet/lifestyle tips tailored to the abnormal values.
- Section 4 must give exactly 3 questions to ask the doctor.
- Do not diagnose, and do not suggest medicine names or doses.
- End with one short line saying this is educational and not a substitute for a doctor.
"""


def generate_llm_summary(
    raw_text: str,
    parameters: List[Dict[str, Any]],
    patient_info: Dict[str, str],
    api_key: Optional[str] = None,
    language: str = "bilingual",
) -> Dict[str, Any]:
    """
    Generates a personalised summary with Google Gemini in the requested language.
    Falls back to the rule-based engine (with a visible note explaining why).
    """
    key_to_use = api_key or os.getenv("GEMINI_API_KEY")
    base_res = generate_rule_based_summary(patient_info, parameters)

    if not key_to_use:
        base_res["llm_note"] = "no_key"
        return base_res

    prompt = build_summary_prompt(raw_text, parameters, patient_info, language)
    text, model, err = _call_gemini(prompt, key_to_use)
    if text:
        base_res["engine"] = f"Google {model} + Clinical Engine"
        base_res["ai_narrative"] = text
        base_res["language"] = language
    else:
        base_res["engine"] = "Clinical Rule-Based Engine (LLM Fallback)"
        base_res["llm_note"] = f"error: {err}"
    return base_res


# ------------------------------------------------------------------
# Question answering ("Ask about your report")
# ------------------------------------------------------------------
def answer_question_llm(
    question: str,
    history: List[Dict[str, str]],
    parameters: List[Dict[str, Any]],
    patient_info: Dict[str, str],
    raw_text: str,
    api_key: str,
    language: str = "bilingual",
) -> Tuple[Optional[str], Optional[str]]:
    """Answers a free-form question about the loaded report. Returns (answer, error)."""
    language = language if language in LANG_MODES else "bilingual"
    convo = "\n".join(
        f"{'Patient' if m['role'] == 'user' else 'Assistant'}: {m['content']}" for m in history[-6:]
    )
    prompt = f"""You are a careful, friendly assistant helping a patient understand their lab report.

LANGUAGE RULE: {LANG_INSTRUCTIONS[language]}
If the patient writes in Hindi or Hinglish, reply in simple Hindi even in English mode only if they clearly wrote in Hindi.

PATIENT: {patient_info.get('name', 'Patient')} ({patient_info.get('age_gender', 'n/a')})

LAB RESULTS:
{_findings_text(parameters)}

RAW REPORT TEXT:
{raw_text[:2500]}

CONVERSATION SO FAR:
{convo or '(none)'}

PATIENT QUESTION: {question}

Answer using only the report above. Keep it short (under 150 words), simple and calm.
If the question is not answerable from the report, say so and suggest asking the doctor.
Never diagnose or recommend medicines or doses. Mention seeing a doctor for anything serious.
"""
    text, _model, err = _call_gemini(prompt, api_key, temperature=0.4)
    return text, err


def answer_question_offline(
    question: str,
    parameters: List[Dict[str, Any]],
    language: str = "bilingual",
) -> str:
    """Keyword-based answer used when no Gemini key is available."""
    q = question.lower()
    hits = []
    for p in parameters:
        tokens = {p["key"].lower(), p["name"].lower()}
        tokens.update(t.strip("()") for t in p["name"].lower().split())
        if any(len(t) > 2 and t in q for t in tokens):
            hits.append(p)

    use_hi = language in ("hindi", "bilingual")
    use_en = language in ("english", "bilingual")

    if not hits:
        msgs = []
        if use_en:
            msgs.append("I couldn't match your question to a test in this report. Try naming a test (e.g. 'What is hemoglobin?'), or add a Gemini API key in the sidebar to ask anything.")
        if use_hi:
            msgs.append("आपका सवाल रिपोर्ट के किसी टेस्ट से मेल नहीं खाया। किसी टेस्ट का नाम लिखकर पूछें (जैसे 'हीमोग्लोबिन क्या है?'), या साइडबार में Gemini API Key डालकर कुछ भी पूछें।")
        return "\n\n".join(msgs)

    parts = []
    for p in hits[:3]:
        if use_en:
            detail = {"High": p["high_en"], "Low": p["low_en"]}.get(p["status"], "This value is within the normal range.")
            parts.append(f"**{p['name']}** = {p['value']} {p['unit']} ({p['status']}; normal {p['min_ref']}-{p['max_ref']}).  \n{p['meaning_en']} {detail}")
        if use_hi:
            detail = {"High": p["high_hi"], "Low": p["low_hi"]}.get(p["status"], "यह वैल्यू सामान्य सीमा में है।")
            parts.append(f"**{p['name']}** = {p['value']} {p['unit']} ({p['status_hi']}).  \n{p['meaning_hi']} {detail}")
    return "\n\n".join(parts)
