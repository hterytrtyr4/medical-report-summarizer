"""
Generate a sample medical report image (PNG) for OCR testing.
"""
import os
from PIL import Image, ImageDraw, ImageFont

SAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(SAMPLES_DIR, "sample_report_image.png")

# Create a clean white receipt / lab report image
img = Image.new("RGB", (900, 700), color=(255, 255, 255))
draw = ImageDraw.Draw(img)

# Use default font
lines = [
    "HEALTHCARE PATH LABS - DIAGNOSTIC REPORT",
    "Patient: Sunita Verma | Age: 48 Female | Date: 17-Nov-2026",
    "-------------------------------------------------------------------------",
    "TEST NAME                     RESULT     UNITS       REFERENCE RANGE",
    "-------------------------------------------------------------------------",
    "Hemoglobin (Hb)               10.5       g/dL        12.0 - 15.5",
    "Total Cholesterol             240.0      mg/dL       125.0 - 200.0",
    "Triglycerides                 210.0      mg/dL       50.0 - 150.0",
    "Fasting Blood Sugar           142.0      mg/dL       70.0 - 100.0",
    "Serum Creatinine              1.1        mg/dL       0.6 - 1.2",
    "TSH (Thyroid Stimulating)     6.2        uIU/mL      0.45 - 4.5",
    "-------------------------------------------------------------------------",
    "Remarks: High Cholesterol and Elevated Fasting Sugar observed.",
    "Please consult your general physician for clinical evaluation."
]

y = 40
for line in lines:
    draw.text((40, y), line, fill=(20, 20, 20))
    y += 40

img.save(IMAGE_PATH)
print(f"Created sample report image at {IMAGE_PATH}")
