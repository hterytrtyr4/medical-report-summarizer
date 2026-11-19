"""
parser.py - Medical Parameter Extraction and Clinical Knowledge Base
Extracts laboratory test parameters, values, units, and reference ranges from medical text.
Performs Normal / High / Low status evaluation and provides rich clinical context.
Supports both single-line tabular rows and multi-line cell-by-cell PDF table layouts.
"""
import re
from typing import Dict, List, Optional, Any

# Clinical Reference Knowledge Base with Hindi and English Context
PARAM_KNOWLEDGE_BASE = {
    "hemoglobin": {
        "display_name": "Hemoglobin (Hb)",
        "aliases": ["hemoglobin", "haemoglobin", "hb", "hgb"],
        "min_ref": 13.0,
        "max_ref": 17.0,
        "unit": "g/dL",
        "category": "Complete Blood Count (CBC)",
        "meaning_en": "Protein in red blood cells that carries oxygen from your lungs throughout the body.",
        "meaning_hi": "लाल रक्त कोशिकाओं (RBC) में पाया जाने वाला प्रोटीन जो पूरे शरीर में ऑक्सीजन पहुंचाने का काम करता है।",
        "high_en": "High levels may suggest dehydration, smoking, lung disease, or polycythemia.",
        "high_hi": "हीमोग्लोबिन ज्यादा होना शरीर में पानी की कमी (dehydration), स्मोकिंग या फेफड़ों की समस्या का संकेत हो सकता है।",
        "low_en": "Low levels indicate Anemia. Can cause fatigue, weakness, pale skin, and shortness of breath.",
        "low_hi": "कम स्तर एनीमिया (खून की कमी) दर्शाता है। इससे थकान, कमजोरी, चक्कर और सांस फूलने की शिकायत हो सकती है।",
        "diet_en": "Eat iron-rich foods: spinach, beetroots, pomegranate, apples, jaggery, eggs, and lean meats.",
        "diet_hi": "आयरन युक्त आहार लें: पालक, चुकंदर, अनार, सेब, गुड़, चना, दालें और हरी पत्तेदार सब्जियां।"
    },
    "wbc": {
        "display_name": "Total Leukocyte Count (WBC)",
        "aliases": ["total leukocyte count", "total leucocyte count", "white blood cells", "white blood cell count", "wbc", "tlc"],
        "min_ref": 4000.0,
        "max_ref": 11000.0,
        "unit": "/cumm",
        "category": "Complete Blood Count (CBC)",
        "meaning_en": "White blood cells act as your body's immune defense system against infections.",
        "meaning_hi": "श्वेत रक्त कोशिकाएं शरीर की रोग प्रतिरोधक (immunity) सेना हैं जो इन्फेक्शन से लड़ती हैं।",
        "high_en": "High WBC count usually indicates active bacterial or viral infection, inflammation, or acute stress.",
        "high_hi": "WBC बढ़ना शरीर में किसी इन्फेक्शन, सूजन (inflammation) या बैक्टीरियल हमले का संकेत है।",
        "low_en": "Low WBC count suggests weakened immune system, viral illness, or bone marrow suppression.",
        "low_hi": "WBC कम होना कमजोर इम्यूनिटी का संकेत है, जिससे संक्रमण का खतरा बढ़ जाता है।",
        "diet_en": "Consume immunity boosters: citrus fruits (Vitamin C), amla, garlic, ginger, and turmeric.",
        "diet_hi": "इम्यूनिटी बढ़ाने वाली चीजें लें: आंवला, संतरा, गिलोय, अदरक, लहसुन और हल्दी वाला दूध।"
    },
    "rbc": {
        "display_name": "Red Blood Cell Count (RBC)",
        "aliases": ["red blood cell count", "red blood cell", "total rbc", "rbc count", "rbc"],
        "min_ref": 4.5,
        "max_ref": 5.9,
        "unit": "mil/cumm",
        "category": "Complete Blood Count (CBC)",
        "meaning_en": "Cells that transport oxygen and carbon dioxide throughout your bloodstream.",
        "meaning_hi": "लाल रक्त कोशिकाएं जो शरीर के हर अंग तक ऑक्सीजन पहुंचाने का काम करती हैं।",
        "high_en": "High RBC can indicate congenital heart trouble, dehydration, or renal problems.",
        "high_hi": "RBC ज्यादा होना डिहाइड्रेशन या हृदय/गुर्दे की किसी परेशानी का संकेत हो सकता है।",
        "low_en": "Low RBC indicates anemia, blood loss, or nutritional deficiency.",
        "low_hi": "RBC कम होना खून की कमी या कुपोषण की ओर इशारा करता है।",
        "diet_en": "Increase Vitamin B12, folic acid, and iron intake.",
        "diet_hi": "विटामिन बी12, फोलिक एसिड और आयरन से भरपूर भोजन करें।"
    },
    "platelets": {
        "display_name": "Platelet Count",
        "aliases": ["platelet count", "total platelets", "platelets", "plt"],
        "min_ref": 150000.0,
        "max_ref": 450000.0,
        "unit": "/cumm",
        "category": "Complete Blood Count (CBC)",
        "meaning_en": "Tiny blood cells that help blood clot to stop excessive bleeding from wounds.",
        "meaning_hi": "रक्त में पाए जाने वाले सेल्स जो चोट लगने पर खून का थक्का (clot) जमाकर खून बहने से रोकते हैं।",
        "high_en": "High platelets (Thrombocytosis) increase the risk of blood clots.",
        "high_hi": "प्लेटलेट्स बहुत ज्यादा होने पर खून में क्लॉट (थक्का) बनने का खतरा रहता है।",
        "low_en": "Low platelets (Thrombocytopenia) seen in viral fevers (Dengue, Malaria); risk of bleeding.",
        "low_hi": "प्लेटलेट्स कम होना (जैसे डेंगू/मलेरिया में) ब्लीडिंग और अत्यधिक कमजोरी का कारण बन सकता है।",
        "diet_en": "Papaya leaf extract, kiwi fruit, coconut water, and pumpkin seeds support recovery.",
        "diet_hi": "पपीते के पत्ते का रस, कीवी, नारियल पानी, अनार और कद्दू के बीज प्लेटलेट्स रिकवरी में मदद करते हैं।"
    },
    "esr": {
        "display_name": "Erythrocyte Sedimentation Rate (ESR)",
        "aliases": ["erythrocyte sedimentation rate", "erythrocyte sedimentation", "sed rate", "esr"],
        "min_ref": 0.0,
        "max_ref": 20.0,
        "unit": "mm/hr",
        "category": "Inflammation Marker",
        "meaning_en": "Measures how quickly red blood cells settle, indicating non-specific inflammation.",
        "meaning_hi": "यह टेस्ट शरीर के अंदर किसी भी तरह की सूजन या लंबे समय से चल रहे इन्फेक्शन को जांचता है।",
        "high_en": "High ESR points to inflammation, autoimmune disorders, or persistent infections.",
        "high_hi": "ESR बढ़ना शरीर में सूजन, गठिया, या किसी पुराने संक्रमण का संकेत देता है।",
        "low_en": "Generally normal and has little clinical significance.",
        "low_hi": "कम ESR सामान्य माना जाता है और चिंता का विषय नहीं है।",
        "diet_en": "Anti-inflammatory diet: turmeric, green leafy vegetables, fatty fish, and walnuts.",
        "diet_hi": "सूजन घटाने वाले खाद्य पदार्थ: हल्दी, अदरक, मेथी, अखरोट और ताजे फल।"
    },
    "pcv": {
        "display_name": "Packed Cell Volume (PCV / HCT)",
        "aliases": ["packed cell volume", "hematocrit", "pcv", "hct"],
        "min_ref": 36.0,
        "max_ref": 50.0,
        "unit": "%",
        "category": "Complete Blood Count (CBC)",
        "meaning_en": "Percentage of total blood volume made up of red blood cells.",
        "meaning_hi": "खून के कुल आयतन में लाल रक्त कोशिकाओं का प्रतिशत हिस्सा।",
        "high_en": "Elevated hematocrit suggests dehydration or polycythemia.",
        "high_hi": "PCV बढ़ना शरीर में पानी की भारी कमी (डिहाइड्रेशन) का संकेत देता है।",
        "low_en": "Reduced hematocrit indicates anemia or recent blood loss.",
        "low_hi": "PCV घटना खून की कमी या हाल ही में हुए रक्तस्राव को दर्शाता है।",
        "diet_en": "Hydrate adequately and consume iron-rich diet.",
        "diet_hi": "खूब पानी पिएं और आयरन से भरपूर संतुलित भोजन लें।"
    },
    "mcv": {
        "display_name": "Mean Corpuscular Volume (MCV)",
        "aliases": ["mean corpuscular volume", "mcv"],
        "min_ref": 80.0,
        "max_ref": 100.0,
        "unit": "fL",
        "category": "Complete Blood Count (CBC)",
        "meaning_en": "Average size and volume of your red blood cells.",
        "meaning_hi": "आपकी लाल रक्त कोशिकाओं (RBC) का औसत आकार और माप।",
        "high_en": "High MCV points to macrocytic anemia (Vitamin B12 or Folate deficiency).",
        "high_hi": "MCV ज्यादा होना विटामिन बी12 या फोलिक एसिड की कमी की ओर इशारा करता है।",
        "low_en": "Low MCV indicates microcytic anemia, commonly iron deficiency or thalassemia trait.",
        "low_hi": "MCV कम होना आयरन की कमी से होने वाले एनीमिया का मुख्य लक्षण है।",
        "diet_en": "Vitamin B12 supplements, dairy, leafy greens, and whole grains.",
        "diet_hi": "दूध, दही, पनीर, हरी सब्जियां और अंकुरित अनाज डाइट में शामिल करें।"
    },
    "fasting_glucose": {
        "display_name": "Fasting Blood Glucose (FBS)",
        "aliases": ["fasting blood glucose", "fasting blood sugar", "blood glucose fasting", "blood sugar fasting", "glucose fasting", "fbs"],
        "min_ref": 70.0,
        "max_ref": 100.0,
        "unit": "mg/dL",
        "category": "Diabetes / Blood Sugar",
        "meaning_en": "Blood sugar concentration measured after an 8 to 12 hour overnight fast.",
        "meaning_hi": "रातभर (8-10 घंटे) भूखे पेट रहने के बाद खून में ग्लूकोज (शुगर) की मात्रा।",
        "high_en": "Levels >= 126 mg/dL suggest Diabetes Mellitus; 100-125 indicates Pre-diabetes.",
        "high_hi": "100 से अधिक होना प्रीडायबिटीज और 126 से अधिक होना डायबिटीज (मधुमेह) की पुष्टि करता है।",
        "low_en": "Hypoglycemia (< 70 mg/dL) causes dizziness, shakiness, sweating, and confusion.",
        "low_hi": "70 से कम होना लो-शुगर (हाइपोग्लाइसीमिया) है, जिससे कंपकंपी और चक्कर आ सकते हैं।",
        "diet_en": "Avoid refined sugar, maida, potatoes, and sweets. Prefer methi, oats, and bitter gourd (karela).",
        "diet_hi": "मीठा, मैदा, आलू और चावल कम करें। करेला, मेथी दाना, जामुन और ओट्स का सेवन करें।"
    },
    "pp_glucose": {
        "display_name": "Post Prandial Blood Glucose (PPBS)",
        "aliases": ["post prandial glucose", "post prandial blood glucose", "post prandial blood sugar", "glucose pp", "ppbs"],
        "min_ref": 70.0,
        "max_ref": 140.0,
        "unit": "mg/dL",
        "category": "Diabetes / Blood Sugar",
        "meaning_en": "Blood sugar concentration measured exactly 2 hours after a meal.",
        "meaning_hi": "खाना खाने के ठीक 2 घंटे बाद खून में शुगर की मात्रा की जांच।",
        "high_en": "Levels >= 200 mg/dL indicate uncontrolled diabetes. Increases heart and kidney risk.",
        "high_hi": "200 से अधिक स्तर अनियंत्रित शुगर दिखाता है जिससे दिल और गुर्दों पर असर पड़ सकता है।",
        "low_en": "May be caused by excess diabetes medication or skipping meals.",
        "low_hi": "दवा की ज्यादा खुराक या खाना न खाने से शुगर गिर सकती है।",
        "diet_en": "Portion control, 30-minute post-meal brisk walking, and high-fiber foods.",
        "diet_hi": "कम मात्रा में बार-बार खाएं, खाने के बाद 20-30 मिनट टहलें और फाइबर ज्यादा लें।"
    },
    "hba1c": {
        "display_name": "HbA1c (Glycated Hemoglobin)",
        "aliases": ["glycated hemoglobin", "glycosylated hemoglobin", "hemoglobin a1c", "hba1c"],
        "min_ref": 4.0,
        "max_ref": 5.6,
        "unit": "%",
        "category": "Diabetes / Blood Sugar",
        "meaning_en": "Gold-standard test representing your average 3-month blood sugar control.",
        "meaning_hi": "पिछले 90 दिनों (3 महीने) के शुगर नियंत्रण का सबसे सटीक और प्रमाणित टेस्ट।",
        "high_en": "5.7-6.4% is Prediabetes; >= 6.5% confirms Diabetes. Higher values increase organ damage risk.",
        "high_hi": "5.7 से 6.4% प्रीडायबिटीज और 6.5% या अधिक शुगर की बीमारी दिखाता है।",
        "low_en": "Rare; can occur with hemolytic anemia or chronic liver condition.",
        "low_hi": "यह बहुत कम पाया जाता है, सामान्यतः चिंताजनक नहीं होता।",
        "diet_en": "Strict low-carb, Mediterranean diet, daily aerobic exercise, and physician guidance.",
        "diet_hi": "कार्बोहाइड्रेट कम करें, रोजाना 40 मिनट व्यायाम करें और डॉक्टर की सलाह से दवा लें।"
    },
    "cholesterol": {
        "display_name": "Total Cholesterol",
        "aliases": ["total cholesterol", "cholesterol total", "serum cholesterol", "cholesterol"],
        "min_ref": 125.0,
        "max_ref": 200.0,
        "unit": "mg/dL",
        "category": "Lipid Profile (Fat/Heart)",
        "meaning_en": "Waxy, fat-like substance found in all cells; essential for hormones but harmful in excess.",
        "meaning_hi": "खून में पाया जाने वाला मोम जैसा वसा (fat) जो ज्यादा होने पर धमनियों में जमने लगता है।",
        "high_en": "High cholesterol forms arterial plaques, raising heart attack and stroke risk.",
        "high_hi": "कोलेस्ट्रॉल बढ़ने से नसों में ब्लॉकेज, हाई बीपी और दिल के दौरे (heart attack) का खतरा बढ़ता है।",
        "low_en": "Very low values are uncommon, seen in severe malnutrition or liver failure.",
        "low_hi": "बहुत कम कोलेस्ट्रॉल कुपोषण या लिवर की खराबी में देखा जाता है।",
        "diet_en": "Cut down on deep-fried food, butter, ghee, trans-fats. Use olive/mustard oil and eat garlic.",
        "diet_hi": "तली-भुनी चीजें, डालडा, मक्खन बंद करें। लहसुन, अलसी (flaxseed), और हरी सब्जियां खाएं।"
    },
    "triglycerides": {
        "display_name": "Triglycerides",
        "aliases": ["serum triglycerides", "triglycerides", "triglyceride", "tg"],
        "min_ref": 50.0,
        "max_ref": 150.0,
        "unit": "mg/dL",
        "category": "Lipid Profile (Fat/Heart)",
        "meaning_en": "Most common type of fat stored in your body from unused calories.",
        "meaning_hi": "शरीर में बची हुई अतिरिक्त कैलोरी से बनने वाला फैट (चरबी)।",
        "high_en": "High levels contribute to fatty liver disease, pancreatitis, and heart disease.",
        "high_hi": "ट्राइग्लिसराइड्स बढ़ना फैटी लिवर (Fatty Liver) और दिल की बीमारियों का प्रमुख कारण है।",
        "low_en": "Rare; occurs in hyperthyroidism, malnutrition, or low-fat diets.",
        "low_hi": "बहुत कम होना साधारणतः कोई समस्या नहीं है।",
        "diet_en": "Eliminate sugary sodas, alcohol, sweets, and refined carbohydrates. Exercise regularly.",
        "diet_hi": "शराब, कोल्ड ड्रिंक, मिठाई और जंक फूड तुरंत बंद करें। रोजाना पसीना बहाएं।"
    },
    "hdl": {
        "display_name": "HDL Cholesterol (Good)",
        "aliases": ["hdl cholesterol", "high density lipoprotein", "hdl"],
        "min_ref": 40.0,
        "max_ref": 60.0,
        "unit": "mg/dL",
        "category": "Lipid Profile (Fat/Heart)",
        "meaning_en": "'Good' cholesterol that scrubs bad fats from arteries and transports them back to the liver.",
        "meaning_hi": "'अच्छा कोलेस्ट्रॉल' जो नसों में जमी गंदगी को साफ करके लिवर तक पहुंचाता है।",
        "high_en": "Protective for cardiovascular health; higher is generally beneficial.",
        "high_hi": "यह जितना अच्छा और पर्याप्त रहे, दिल की सुरक्षा उतनी ही मजबूत रहती है।",
        "low_en": "Low HDL (< 40 mg/dL) increases cardiovascular and coronary heart disease risk.",
        "low_hi": "HDL कम होना दिल के लिए खतरे की घंटी है।",
        "diet_en": "Omega-3 rich foods: walnuts, chia seeds, flaxseeds, fish, and regular cardio exercise.",
        "diet_hi": "अखरोट, चिया सीड्स, अलसी, सरसों का तेल और रोजाना 30 मिनट दौड़ना/चलना।"
    },
    "ldl": {
        "display_name": "LDL Cholesterol (Bad)",
        "aliases": ["ldl cholesterol", "low density lipoprotein", "ldl"],
        "min_ref": 50.0,
        "max_ref": 100.0,
        "unit": "mg/dL",
        "category": "Lipid Profile (Fat/Heart)",
        "meaning_en": "'Bad' cholesterol that deposits fatty plaques inside arterial walls.",
        "meaning_hi": "'खराब कोलेस्ट्रॉल' जो नसों की दीवारों में जम जाता है और खून के बहाव को रोकता है।",
        "high_en": "Major driver of atherosclerosis, arterial narrowing, angina, and heart attacks.",
        "high_hi": "LDL ज्यादा होने से दिल का दौरा और नसों के ब्लॉक होने का खतरा सबसे ज्यादा होता है।",
        "low_en": "Generally desirable and protects coronary blood flow.",
        "low_hi": "कम स्तर दिल की सेहत के लिए उत्तम माना जाता है।",
        "diet_en": "Soluble fiber: oats, kidney beans (rajma), apples, pears, and psyllium husk (isabgol).",
        "diet_hi": "ओट्स, राजमा, सेब, संतरा, और ईसबगोल की भूसी का सेवन LDL घटाने में मददगार है।"
    },
    "vldl": {
        "display_name": "VLDL Cholesterol",
        "aliases": ["vldl cholesterol", "very low density lipoprotein", "vldl"],
        "min_ref": 5.0,
        "max_ref": 30.0,
        "unit": "mg/dL",
        "category": "Lipid Profile (Fat/Heart)",
        "meaning_en": "Very low density lipoprotein carrying triglycerides in circulation.",
        "meaning_hi": "अत्यंत कम घनत्व वाला लिपोप्रोटीन जो नसों में ट्राइग्लिसराइड्स ले जाता है।",
        "high_en": "Increases cardiovascular plaque buildup.",
        "high_hi": "ज्यादा होना नसों में ब्लॉकेज का जोखिम बढ़ाता है।",
        "low_en": "Normal and clinically safe.",
        "low_hi": "सामान्य और सुरक्षित स्थिति।",
        "diet_en": "Cut refined carbohydrates and fats.",
        "diet_hi": "मीठा और तेल-मसाला कम करें।"
    },
    "creatinine": {
        "display_name": "Serum Creatinine",
        "aliases": ["serum creatinine", "creatinine", "creat"],
        "min_ref": 0.6,
        "max_ref": 1.2,
        "unit": "mg/dL",
        "category": "Kidney Function Test (KFT)",
        "meaning_en": "Waste byproduct of muscle metabolism filtered out of the blood exclusively by kidneys.",
        "meaning_hi": "मांसपेशियों से निकलने वाला अपशिष्ट पदार्थ (waste) जिसे गुर्दे (kidneys) छानकर पेशाब से निकालते हैं।",
        "high_en": "Elevated creatinine indicates impaired kidney filtration or renal insufficiency.",
        "high_hi": "क्रीटिनिन बढ़ना गुर्दों (Kidneys) के खराब होने या उनकी फिल्टर करने की क्षमता घटने का संकेत है।",
        "low_en": "Low values can be due to reduced muscle mass or severe liver disease.",
        "low_hi": "मांसपेशियों की कमजोरी या कम वजन में स्तर कम हो सकता है।",
        "diet_en": "Drink plenty of water (unless on fluid restriction). Limit excess protein/red meat and painkiller usage.",
        "diet_hi": "पर्याप्त पानी पिएं, दर्द निवारक दवाइयां (painkillers) बिना डॉक्टर के न खाएं, नमक कम करें।"
    },
    "blood_urea": {
        "display_name": "Blood Urea",
        "aliases": ["blood urea", "urea", "serum urea"],
        "min_ref": 15.0,
        "max_ref": 40.0,
        "unit": "mg/dL",
        "category": "Kidney Function Test (KFT)",
        "meaning_en": "Waste product created when the liver breaks down dietary proteins.",
        "meaning_hi": "लिवर द्वारा प्रोटीन पचाने के बाद बनने वाला अपशिष्ट पदार्थ, जो किडनी द्वारा बाहर निकाला जाता है।",
        "high_en": "Suggests kidney dysfunction, dehydration, high protein diet, or gastrointestinal bleeding.",
        "high_hi": "यूरिया बढ़ना गुर्दे की कमजोरी या शरीर में पानी की भारी कमी को दर्शाता है।",
        "low_en": "Seen in severe liver disease, low protein intake, or overhydration.",
        "low_hi": "प्रोटीन की कमी या लिवर रोग में कम देखा जा सकता है।",
        "diet_en": "Moderate protein intake, stay hydrated, and monitor kidney function.",
        "diet_hi": "उचित मात्रा में पानी पिएं और खाने में अत्यधिक प्रोटीन व नमक से परहेज करें।"
    },
    "uric_acid": {
        "display_name": "Serum Uric Acid",
        "aliases": ["serum uric acid", "uric acid"],
        "min_ref": 3.5,
        "max_ref": 7.2,
        "unit": "mg/dL",
        "category": "Kidney & Joint Health",
        "meaning_en": "Compound produced by the breakdown of purines in foods.",
        "meaning_hi": "शरीर में प्यूरिन नामक तत्व के टूटने से बनने वाला एसिड।",
        "high_en": "High levels form needle-like crystals in joints causing Gout (severe joint pain) and kidney stones.",
        "high_hi": "यूरिक एसिड बढ़ने से जोड़ों में दर्द, गठिया (Gout) और गुर्दे की पथरी (Kidney Stone) बन सकती है।",
        "low_en": "Rare and generally not clinically concerning.",
        "low_hi": "कम स्तर आमतौर पर कोई नुकसान नहीं पहुंचाता।",
        "diet_en": "Avoid purine-heavy foods: red meat, organ meats, alcohol/beer, spinach in excess, and sugary drinks.",
        "diet_hi": "लाल मांस, शराब/बीयर, मशरूम, टमाटर और दालों की अधिकता से बचें। नींबू पानी और चेरी फायदेमंद हैं।"
    },
    "bilirubin_total": {
        "display_name": "Bilirubin (Total)",
        "aliases": ["total bilirubin", "bilirubin total", "serum bilirubin"],
        "min_ref": 0.2,
        "max_ref": 1.2,
        "unit": "mg/dL",
        "category": "Liver Function Test (LFT)",
        "meaning_en": "Yellowish pigment made during the normal breakdown of red blood cells.",
        "meaning_hi": "पीला पदार्थ जो खून के सेल्स के टूटने पर बनता है और लिवर द्वारा प्रोसेस होता है।",
        "high_en": "Elevated bilirubin causes Jaundice (Piliya): yellowish eyes, skin, dark urine, and liver inflammation.",
        "high_hi": "बिलीरुबिन बढ़ने से पीलिया (Jaundice) होता है - आंखें और पेशाब पीला पड़ना, लिवर में सूजन।",
        "low_en": "Low levels are completely normal and safe.",
        "low_hi": "कम स्तर सामान्य और सुरक्षित माना जाता है।",
        "diet_en": "Easily digestible bland food, sugarcane juice, radish, papaya, and plenty of fluids. Zero alcohol.",
        "diet_hi": "उबला हुआ सादा खाना, गन्ने का रस, मूली, पपीता और नारियल पानी लें। तेल-मसाले और शराब से दूर रहें।"
    },
    "sgpt": {
        "display_name": "SGPT / ALT (Alanine Aminotransferase)",
        "aliases": ["sgpt / alt", "sgpt", "alanine aminotransferase", "alanine transaminase", "alt"],
        "min_ref": 10.0,
        "max_ref": 45.0,
        "unit": "U/L",
        "category": "Liver Function Test (LFT)",
        "meaning_en": "Key enzyme found mainly in liver cells, released into blood upon liver stress or injury.",
        "meaning_hi": "लिवर सेल्स में पाया जाने वाला प्रमुख एंजाइम, जो लिवर में सूजन या नुकसान होने पर खून में बढ़ जाता है।",
        "high_en": "Sign of liver injury: viral hepatitis, fatty liver, alcohol damage, or medication toxicity.",
        "high_hi": "SGPT बढ़ना फैटी लिवर, हेपेटाइटिस, शराब का असर या लिवर इन्फेक्शन दर्शाता है।",
        "low_en": "Normal and expected in healthy individuals.",
        "low_hi": "कम होना सामान्य और स्वस्थ लिवर का संकेत है।",
        "diet_en": "Avoid alcohol, fatty fast food, and unprescribed drugs. Drink warm water and eat leafy greens.",
        "diet_hi": "शराब और तली-भुनी चीजें छोड़ें। ग्रीन टी, आंवला, पपीता और हल्के सुपाच्य भोजन को प्राथमिकता दें।"
    },
    "sgot": {
        "display_name": "SGOT / AST (Aspartate Aminotransferase)",
        "aliases": ["sgot / ast", "sgot", "aspartate aminotransferase", "aspartate transaminase", "ast"],
        "min_ref": 10.0,
        "max_ref": 40.0,
        "unit": "U/L",
        "category": "Liver Function Test (LFT)",
        "meaning_en": "Enzyme present in liver, heart, and muscle tissue.",
        "meaning_hi": "एंजाइम जो लिवर, दिल और मांसपेशियों के ऊतकों में मौजूद होता है।",
        "high_en": "Indicates acute liver damage, strenuous muscle injury, or cardiac stress.",
        "high_hi": "SGOT बढ़ना लिवर या मांसपेशियों में खिंचाव/सूजन का संकेत हो सकता है।",
        "low_en": "Normal and clinically insignificant.",
        "low_hi": "कम होना सामान्य माना जाता है।",
        "diet_en": "Maintain a clean liver-friendly diet, avoid self-medicating with painkillers.",
        "diet_hi": "लिवर को डिटॉक्स करने वाले फल खाएं और दर्द निवारक दवाओं का अनावश्यक उपयोग न करें।"
    },
    "tsh": {
        "display_name": "Thyroid Stimulating Hormone (TSH)",
        "aliases": ["thyroid stimulating hormone", "serum tsh", "tsh"],
        "min_ref": 0.45,
        "max_ref": 4.5,
        "unit": "uIU/mL",
        "category": "Thyroid Profile",
        "meaning_en": "Pituitary hormone that regulates thyroid gland hormone production and metabolism.",
        "meaning_hi": "पिट्यूटरी ग्रंथि का हार्मोन जो थायरॉइड को नियंत्रित करता है और मेटाबॉलिज्म (पाचन/ऊर्जा) चलाता है।",
        "high_en": "High TSH indicates Hypothyroidism (underactive thyroid): weight gain, fatigue, hair fall, depression.",
        "high_hi": "TSH बढ़ना हाइपोथायरॉइडिज्म (थायरॉइड कम काम करना) दिखाता है: वजन बढ़ना, थकान, बाल झड़ना, सुस्ती।",
        "low_en": "Low TSH indicates Hyperthyroidism (overactive thyroid): rapid heartbeat, weight loss, tremors, anxiety.",
        "low_hi": "TSH कम होना हाइपरथायरॉइडिज्म (थायरॉइड ज्यादा काम करना) है: दिल की धड़कन तेज होना, वजन घटना, घबराहट।",
        "diet_en": "For Hypo: iodized salt, brazil nuts (selenium), eggs. Avoid raw cabbage, cauliflower, and soy.",
        "diet_hi": "आयोडीन युक्त नमक लें। पत्तागोभी, फूलगोभी और सोयाबीन को कच्चा खाने से परहेज करें।"
    },
    "t3": {
        "display_name": "Triiodothyronine (Total T3)",
        "aliases": ["triiodothyronine", "total t3", "t3"],
        "min_ref": 80.0,
        "max_ref": 200.0,
        "unit": "ng/dL",
        "category": "Thyroid Profile",
        "meaning_en": "Active thyroid hormone regulating heart rate, body temperature, and energy burn.",
        "meaning_hi": "सक्रिय थायरॉइड हार्मोन जो शरीर के तापमान, दिल की धड़कन और ऊर्जा को नियंत्रित करता है।",
        "high_en": "Suggests Hyperthyroidism or thyroiditis.",
        "high_hi": "ज्यादा होना थायरॉइड के अति-सक्रिय होने का संकेत है।",
        "low_en": "Suggests Hypothyroidism or severe chronic non-thyroidal illness.",
        "low_hi": "कम होना सुस्त मेटाबॉलिज्म और थायरॉइड की सुस्ती दर्शाता है।",
        "diet_en": "Balanced nutrition rich in zinc, selenium, and iron.",
        "diet_hi": "जिंक और सेलेनियम से भरपूर आहार लें।"
    },
    "t4": {
        "display_name": "Thyroxine (Total T4)",
        "aliases": ["thyroxine", "total t4", "t4"],
        "min_ref": 5.0,
        "max_ref": 12.0,
        "unit": "ug/dL",
        "category": "Thyroid Profile",
        "meaning_en": "Primary hormone produced by thyroid gland, converted into active T3.",
        "meaning_hi": "थायरॉइड ग्रंथि द्वारा बनाया जाने वाला मुख्य हार्मोन।",
        "high_en": "Overactive thyroid gland (Hyperthyroidism).",
        "high_hi": "हाइपरथायरॉइडिज्म (थायरॉइड ज्यादा बनना)।",
        "low_en": "Underactive thyroid gland (Hypothyroidism).",
        "low_hi": "हाइपोथायरॉइडिज्म (थायरॉइड हार्मोन की कमी)।",
        "diet_en": "Ensure proper endocrinologist consultation for hormone replacement.",
        "diet_hi": "डॉक्टर की सलाह से सही खुराक में दवा का सेवन करें।"
    }
}


def parse_reference_range(range_str: str) -> tuple[Optional[float], Optional[float]]:
    """
    Parses strings like '13.0 - 17.0', '< 200', '> 40', '0 to 15'
    """
    if not range_str:
        return None, None
    s = range_str.strip().lower()

    # Range: '13.0 - 17.0' or '13.0 to 17.0'
    m_between = re.search(r'(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)', s)
    if m_between:
        try:
            return float(m_between.group(1)), float(m_between.group(2))
        except ValueError:
            pass

    # Less than: '< 200'
    m_lt = re.search(r'(?:<|less\s+than|upto|up\s+to)\s*(\d+(?:\.\d+)?)', s)
    if m_lt:
        try:
            return 0.0, float(m_lt.group(1))
        except ValueError:
            pass

    # Greater than: '> 40'
    m_gt = re.search(r'(?:>|greater\s+than|more\s+than)\s*(\d+(?:\.\d+)?)', s)
    if m_gt:
        try:
            return float(m_gt.group(1)), 999999.0
        except ValueError:
            pass

    return None, None


def extract_patient_info(text: str) -> Dict[str, str]:
    """
    Extracts patient demographic metadata like Name, Age, Gender, Date, Doctor, Lab Name.
    """
    info = {
        "name": "Not Detected",
        "age_gender": "Not Detected",
        "date": "Not Detected",
        "doctor": "Not Detected",
        "lab_name": "Diagnostic Laboratory"
    }
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        for line in lines[:5]:
            if any(term in line.lower() for term in ["lab", "hospital", "pathology", "clinic", "diagnostic"]):
                info["lab_name"] = re.sub(r'^[=\-\*#\s]+|[=\-\*#\s]+$', '', line).strip()
                break

    # Patient Name
    m_name = re.search(r'(?:Patient(?:\s+Name)?|Name)\s*[:\-]\s*([A-Za-z\s\.]+?)(?:\s{2,}|Age|\t|\n|$)', text, re.IGNORECASE)
    if m_name:
        cand = m_name.group(1).strip()
        if len(cand) > 2 and not any(term in cand.lower() for term in ["info", "detail", "report", "test", "investigation"]):
            info["name"] = cand

    # Age / Gender
    m_age_gender = re.search(r'(?:Age\s*(?:/|&)?\s*Gender|Age)\s*[:\-]\s*([0-9A-Za-z\s/]+?)(?:\s{2,}|Date|Ref|\t|\n|$)', text, re.IGNORECASE)
    if m_age_gender:
        cand_ag = m_age_gender.group(1).strip()
        if len(cand_ag) > 1 and not cand_ag.lower().startswith("of"):
            info["age_gender"] = cand_ag

    # Date
    m_date = re.search(r'(?:Date|Date\s*of\s*Collection|Report\s*Date)\s*[:\-]\s*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4}|[0-9]{1,2}-[A-Za-z]{3}-[0-9]{2,4})', text, re.IGNORECASE)
    if m_date:
        info["date"] = m_date.group(1).strip()

    # Doctor
    m_doc = re.search(r'(?:Referral\s*Doctor|Doctor|Ref\s*Doctor|Dr\.)\s*[:\-]?\s*([A-Za-z\s\.,]+?)(?:\s{2,}|Date|\t|\n|$)', text, re.IGNORECASE)
    if m_doc:
        cand_doc = m_doc.group(1).strip()
        if len(cand_doc) > 2 and "date" not in cand_doc.lower():
            if not cand_doc.lower().startswith("dr"):
                cand_doc = "Dr. " + cand_doc
            info["doctor"] = cand_doc

    return info


def extract_parameters(text: str) -> List[Dict[str, Any]]:
    """
    Universal parameter extractor:
    Handles:
    1. Single-line tabular row:
       'Hemoglobin (Hb) 10.2 g/dL 13.0 - 17.0'
    2. Multi-line table cell-by-cell format (common in PDF text extraction):
       'Total Cholesterol' -> line i
       '245.0'             -> line i+1
       'mg/dL'             -> line i+2
       '125.0 - 200.0'     -> line i+3
    """
    found_params: List[Dict[str, Any]] = []
    seen_keys = set()
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for key, meta in PARAM_KNOWLEDGE_BASE.items():
        if key in seen_keys:
            continue

        matched = False
        for alias in meta["aliases"]:
            alias_pattern = re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE)

            for i, line in enumerate(lines):
                m_alias = alias_pattern.search(line)
                if not m_alias:
                    continue

                # Everything on the line after the alias
                rest = line[m_alias.end():]
                rest_clean = re.sub(r'^\s*\([^\)]*\)', '', rest).strip()

                val = None
                unit_cand = None
                range_cand = None

                # MODE 1: Check if the number is on the same line
                m_num = re.search(r'(?:^|[:\s\-\.\t]+)(\d+(?:\.\d+)?)\s*([a-zA-Z/%]+)?(?:\s+([\d\.\s\-to<>]+))?', rest_clean)
                if m_num:
                    try:
                        v = float(m_num.group(1))
                        if not (v > 1000000 or (v == 2026 and "date" in line.lower())):
                            val = v
                            unit_cand = m_num.group(2)
                            range_cand = m_num.group(3)
                    except ValueError:
                        pass

                # MODE 2: Multi-line look-ahead (cell-by-cell PDF output)
                if val is None:
                    for offset in range(1, 4):
                        if i + offset < len(lines):
                            cand_line = lines[i + offset]
                            m_next = re.search(r'^(\d+(?:\.\d+)?)(?:\s*([a-zA-Z/%]+))?', cand_line)
                            if m_next:
                                try:
                                    v = float(m_next.group(1))
                                    if not (v > 1000000 or v == 2026):
                                        val = v
                                        unit_cand = m_next.group(2)
                                        # Check line after value for unit or range
                                        if i + offset + 1 < len(lines):
                                            after_val = lines[i + offset + 1]
                                            if not unit_cand and re.match(r'^[a-zA-Z/%]+$', after_val):
                                                unit_cand = after_val
                                            elif re.search(r'[\d\.\s\-to<>]+', after_val):
                                                range_cand = after_val
                                        if i + offset + 2 < len(lines) and not range_cand:
                                            after_val2 = lines[i + offset + 2]
                                            if re.search(r'[\d\.\s\-to<>]+', after_val2):
                                                range_cand = after_val2
                                        break
                                except ValueError:
                                    pass

                if val is None:
                    continue

                # Determine reference bounds
                min_r, max_r = meta["min_ref"], meta["max_ref"]
                if range_cand:
                    c_min, c_max = parse_reference_range(range_cand)
                    if c_min is not None and c_max is not None:
                        min_r, max_r = c_min, c_max

                # Status determination
                if val < min_r:
                    status = "Low"
                    badge_color = "#f39c12"
                    status_hi = "कम (Low)"
                elif val > max_r:
                    status = "High"
                    badge_color = "#e74c3c"
                    status_hi = "अधिक (High)"
                else:
                    status = "Normal"
                    badge_color = "#27ae60"
                    status_hi = "सामान्य (Normal)"

                found_params.append({
                    "key": key,
                    "name": meta["display_name"],
                    "category": meta["category"],
                    "value": val,
                    "unit": unit_cand if unit_cand else meta["unit"],
                    "min_ref": min_r,
                    "max_ref": max_r,
                    "status": status,
                    "status_hi": status_hi,
                    "badge_color": badge_color,
                    "meaning_en": meta["meaning_en"],
                    "meaning_hi": meta["meaning_hi"],
                    "high_en": meta["high_en"],
                    "high_hi": meta["high_hi"],
                    "low_en": meta["low_en"],
                    "low_hi": meta["low_hi"],
                    "diet_en": meta["diet_en"],
                    "diet_hi": meta["diet_hi"]
                })
                seen_keys.add(key)
                matched = True
                break

            if matched:
                break

    return found_params
