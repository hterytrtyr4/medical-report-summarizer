"""
summarizer.py - Bilingual AI & Clinical Rule-Based Medical Summarization Engine
Generates patient-friendly explanations in Hindi, English, and Hinglish.
Integrates Google Gemini LLM with robust deterministic fallback.
"""
import os
from typing import Dict, List, Any, Optional

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


def generate_llm_summary(
    raw_text: str,
    parameters: List[Dict[str, Any]],
    patient_info: Dict[str, str],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates an advanced bilingual summary using Google Gemini (via google-genai SDK).
    Falls back gracefully to the rule-based engine if the API key is absent or invalid.
    """
    key_to_use = api_key or os.getenv("GEMINI_API_KEY")
    
    # If no LLM available or key not configured, use rule-based fallback
    if not GEMINI_AVAILABLE or not key_to_use:
        res = generate_rule_based_summary(patient_info, parameters)
        res["llm_note"] = "Rule-based synthesis active. (Enter a Gemini API Key in the sidebar for personalized LLM reasoning)."
        return res

    # Construct prompt with clinical findings
    findings_summary = []
    for p in parameters:
        findings_summary.append(
            f"- {p['name']}: {p['value']} {p['unit']} (Standard Range: {p['min_ref']} - {p['max_ref']} {p['unit']}) -> Status: {p['status']}"
        )
    findings_text = "\n".join(findings_summary) if findings_summary else "No exact numerical parameters parsed automatically."

    prompt = f"""
You are an expert, compassionate bilingual medical communicator and clinical educator.
Your task is to analyze the following laboratory diagnostic report and explain it in extremely simple, empathetic terms for a non-medical patient and their family.

PATIENT METADATA:
Name: {patient_info.get('name', 'Patient')}
Age / Gender: {patient_info.get('age_gender', 'Not Specified')}
Report Date: {patient_info.get('date', 'Recent')}

EXTRACTED PARAMETERS:
{findings_text}

RAW TEXT SNIPPET:
{raw_text[:1200]}

Please provide your response in cleanly formatted Markdown with the following specific sections:

### 1. 🇮🇳 सरल हिंदी में मुख्य निष्कर्ष (Key Takeaways in Simple Hindi)
- समझाएं कि रिपोर्ट में क्या सामान्य है और क्या चिंताजनक (High / Low).
- बिना डराए, सहज और रोजमर्रा की हिंदी में मरीज को उनकी सेहत का हाल बताएं।

### 2. 🇬🇧 Clinical Overview in Plain English
- High-level clinical synthesis of what these results mean together (e.g. anemia, metabolic risk, inflammation, renal strain).
- Categorize urgency: Routine review / Prompt doctor consultation.

### 3. 🥗 खान-पान और दिनचर्या में क्या सुधार करें? (Diet & Lifestyle Guidance)
- 3-4 practical dietary dos and don'ts in Hindi & English tailored specifically to these test numbers.

### 4. 🩺 डॉक्टर से परामर्श लेते समय क्या पूछें? (Questions for Doctor)
- 3 crucial questions the patient should ask their consulting doctor.

### ⚠️ Medical Disclaimer
- Clear standard disclaimer that this AI summary is for educational empowerment and not a substitute for clinical diagnosis or prescription.
"""

    try:
        client = genai.Client(api_key=key_to_use)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        llm_text = response.text

        base_res = generate_rule_based_summary(patient_info, parameters)
        base_res["engine"] = "Google Gemini 2.5 Flash + Clinical Engine"
        base_res["ai_narrative"] = llm_text
        return base_res

    except Exception as e:
        # Graceful fallback on quota error, bad key, or offline
        fallback_res = generate_rule_based_summary(patient_info, parameters)
        fallback_res["engine"] = "Clinical Rule-Based Engine (LLM Fallback)"
        fallback_res["llm_note"] = f"LLM temporarily unavailable ({str(e)[:80]}...). Using trusted clinical rule engine."
        return fallback_res
