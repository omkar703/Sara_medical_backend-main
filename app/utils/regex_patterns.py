"""
Medical Entity Regex Patterns

Comprehensive collection of regex patterns for extracting medical entities
from OCR text, including medications, dosages, vitals, lab values, and patient information.
"""
import re
from typing import Dict, List, Pattern

# ============================================================================
# PATIENT INFORMATION PATTERNS
# ============================================================================

PATIENT_NAME_PATTERNS: List[Pattern] = [
    re.compile(r"(?:Patient\s*Name|Name|Patient):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", re.IGNORECASE),
    re.compile(r"Mr\.|Mrs\.|Ms\.|Dr\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", re.IGNORECASE),
]

PATIENT_AGE_PATTERNS: List[Pattern] = [
    re.compile(r"(?:Age|age):\s*(\d{1,3})\s*(?:years|yrs|y)?", re.IGNORECASE),
    re.compile(r"(\d{1,3})\s*(?:years old|yrs old|y\.o\.)", re.IGNORECASE),
]

PATIENT_GENDER_PATTERNS: List[Pattern] = [
    re.compile(r"(?:Gender|Sex):\s*(Male|Female|M|F)", re.IGNORECASE),
]

PATIENT_ID_PATTERNS: List[Pattern] = [
    re.compile(r"(?:MRN|Medical Record Number|Patient ID|ID):\s*([A-Z0-9-]+)", re.IGNORECASE),
    re.compile(r"(?:Patient\s*#|ID\s*#):\s*(\d+)", re.IGNORECASE),
]

# ============================================================================
# MEDICATION PATTERNS
# ============================================================================

# Common medication names (extensible list)
COMMON_MEDICATIONS = [
    "Metformin", "Insulin", "Aspirin", "Lisinopril", "Atorvastatin",
    "Levothyroxine", "Amlodipine", "Omeprazole", "Losartan", "Simvastatin",
    "Gabapentin", "Hydrochlorothiazide", "Sertraline", "Ibuprofen",
    "Paracetamol", "Acetaminophen", "Amoxicillin", "Ciprofloxacin"
]

MEDICATION_PATTERNS: List[Pattern] = [
    # Medication name followed by dosage
    re.compile(r"\b(" + "|".join(COMMON_MEDICATIONS) + r")\b\s*\d+\s*(?:mg|ml|mcg|g|IU)", re.IGNORECASE),
    # Generic medication pattern with dosage
    re.compile(r"\b([A-Z][a-z]+(?:cillin|mycin|statin|pril|sartan|olol))\s*\d+\s*(?:mg|ml|mcg)", re.IGNORECASE),
]

# ============================================================================
# DOSAGE PATTERNS
# ============================================================================

DOSAGE_PATTERNS: List[Pattern] = [
    re.compile(r"\b(\d+(?:\.\d+)?)\s*(mg|ml|mcg|g|IU|units?)\b", re.IGNORECASE),
    re.compile(r"\b(\d+(?:\.\d+)?)\s*(milligram|milliliter|microgram|gram|international unit)s?\b", re.IGNORECASE),
]

# ============================================================================
# FREQUENCY PATTERNS
# ============================================================================

FREQUENCY_PATTERNS: List[Pattern] = [
    # Standard medical abbreviations
    re.compile(r"\b(QD|BID|TID|QID|Q\d+H)\b", re.IGNORECASE),
    re.compile(r"\b(once|twice|three times|four times)\s*(?:a\s*)?(?:day|daily)\b", re.IGNORECASE),
    re.compile(r"\b(?:every|q)\s*(\d+)\s*(?:hours?|hrs?|h)\b", re.IGNORECASE),
    re.compile(r"\b(daily|weekly|monthly)\b", re.IGNORECASE),
]

# ============================================================================
# VITAL SIGNS PATTERNS
# ============================================================================

BLOOD_PRESSURE_PATTERNS: List[Pattern] = [
    re.compile(r"(?:BP|Blood Pressure):\s*(\d{2,3})/(\d{2,3})\s*(?:mmHg)?", re.IGNORECASE),
    re.compile(r"\b(\d{2,3})/(\d{2,3})\s*mmHg\b", re.IGNORECASE),
]

HEART_RATE_PATTERNS: List[Pattern] = [
    re.compile(r"(?:HR|Heart Rate|Pulse):\s*(\d{2,3})\s*(?:bpm)?", re.IGNORECASE),
    re.compile(r"\b(\d{2,3})\s*bpm\b", re.IGNORECASE),
]

TEMPERATURE_PATTERNS: List[Pattern] = [
    re.compile(r"(?:Temp|Temperature):\s*(\d{2,3}(?:\.\d+)?)\s*°?([CF])", re.IGNORECASE),
    re.compile(r"\b(\d{2,3}(?:\.\d+)?)\s*°([CF])\b", re.IGNORECASE),
]

SPO2_PATTERNS: List[Pattern] = [
    re.compile(r"(?:SpO2|Oxygen Saturation|O2 Sat):\s*(\d{2,3})\s*%?", re.IGNORECASE),
    re.compile(r"\b(\d{2,3})%\s*(?:SpO2|O2)\b", re.IGNORECASE),
]

WEIGHT_PATTERNS: List[Pattern] = [
    re.compile(r"(?:Weight|Wt):\s*(\d+(?:\.\d+)?)\s*(kg|lb|lbs)", re.IGNORECASE),
]

HEIGHT_PATTERNS: List[Pattern] = [
    re.compile(r"(?:Height|Ht):\s*(\d+(?:\.\d+)?)\s*(cm|m|ft|in|inches)", re.IGNORECASE),
]

# ============================================================================
# LABORATORY VALUES PATTERNS
# ============================================================================

GLUCOSE_PATTERNS: List[Pattern] = [
    re.compile(r"(?:Glucose|Blood Sugar|BS):\s*(\d+(?:\.\d+)?)\s*(?:mg/dL|mmol/L)?", re.IGNORECASE),
    re.compile(r"\b(\d+(?:\.\d+)?)\s*mg/dL\s*(?:glucose)?", re.IGNORECASE),
]

HBA1C_PATTERNS: List[Pattern] = [
    re.compile(r"(?:HbA1c|A1C|Hemoglobin A1c):\s*(\d+(?:\.\d+)?)\s*%?", re.IGNORECASE),
]

CHOLESTEROL_PATTERNS: List[Pattern] = [
    re.compile(r"(?:Total Cholesterol|Cholesterol):\s*(\d+)\s*(?:mg/dL)?", re.IGNORECASE),
    re.compile(r"(?:LDL|HDL):\s*(\d+)\s*(?:mg/dL)?", re.IGNORECASE),
]

CREATININE_PATTERNS: List[Pattern] = [
    re.compile(r"(?:Creatinine|Cr):\s*(\d+(?:\.\d+)?)\s*(?:mg/dL)?", re.IGNORECASE),
]

HEMOGLOBIN_PATTERNS: List[Pattern] = [
    re.compile(r"(?:Hemoglobin|Hb|Hgb):\s*(\d+(?:\.\d+)?)\s*(?:g/dL)?", re.IGNORECASE),
]

WBC_PATTERNS: List[Pattern] = [
    re.compile(r"(?:WBC|White Blood Cell):\s*(\d+(?:\.\d+)?)\s*(?:×10\^9/L|K/μL)?", re.IGNORECASE),
]

# ============================================================================
# DATE PATTERNS
# ============================================================================

DATE_PATTERNS: List[Pattern] = [
    # MM/DD/YYYY or DD/MM/YYYY
    re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b"),
    # YYYY-MM-DD (ISO format)
    re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"),
    # Month DD, YYYY
    re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})\b", re.IGNORECASE),
    # DD Month YYYY
    re.compile(r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b", re.IGNORECASE),
]

# ============================================================================
# DIAGNOSIS PATTERNS
# ============================================================================

DIAGNOSIS_PATTERNS: List[Pattern] = [
    re.compile(r"(?:Diagnosis|Dx|Impression):\s*([A-Za-z\s,]+)", re.IGNORECASE),
    re.compile(r"(?:ICD-10|ICD):\s*([A-Z]\d{2}(?:\.\d+)?)", re.IGNORECASE),
]

# ============================================================================
# UNIT NORMALIZATION
# ============================================================================

UNIT_NORMALIZATIONS: Dict[str, str] = {
    # Dosage units
    "milligram": "mg",
    "milligrams": "mg",
    "milliliter": "ml",
    "milliliters": "ml",
    "microgram": "mcg",
    "micrograms": "mcg",
    "gram": "g",
    "grams": "g",
    "international unit": "IU",
    "units": "IU",
    
    # Temperature
    "celsius": "C",
    "fahrenheit": "F",
    
    # Weight
    "kilogram": "kg",
    "kilograms": "kg",
    "pound": "lb",
    "pounds": "lb",
    "lbs": "lb",
    
    # Height
    "centimeter": "cm",
    "centimeters": "cm",
    "meter": "m",
    "meters": "m",
    "foot": "ft",
    "feet": "ft",
    "inch": "in",
    "inches": "in",
}

# ============================================================================
# FREQUENCY NORMALIZATIONS
# ============================================================================

FREQUENCY_NORMALIZATIONS: Dict[str, str] = {
    "qd": "once daily",
    "bid": "twice daily",
    "tid": "three times daily",
    "qid": "four times daily",
    "once a day": "once daily",
    "twice a day": "twice daily",
    "three times a day": "three times daily",
    "four times a day": "four times daily",
}

# ============================================================================
# MEDICAL VALUE RANGES (for validation)
# ============================================================================

NORMAL_RANGES: Dict[str, tuple] = {
    "systolic_bp": (90, 180),      # mmHg
    "diastolic_bp": (60, 120),     # mmHg
    "heart_rate": (40, 200),       # bpm
    "temperature_c": (35.0, 42.0), # Celsius
    "temperature_f": (95.0, 107.6),# Fahrenheit
    "spo2": (70, 100),             # %
    "glucose": (50, 500),          # mg/dL
    "hba1c": (4.0, 15.0),          # %
    "cholesterol": (100, 400),     # mg/dL
    "creatinine": (0.5, 5.0),      # mg/dL
    "hemoglobin": (8.0, 20.0),     # g/dL
    "wbc": (2.0, 30.0),            # K/μL
    "weight_kg": (2, 300),         # kg
    "height_cm": (40, 250),        # cm
}


def normalize_unit(unit: str) -> str:
    """
    Normalize medical unit to standard abbreviation
    
    Args:
        unit: Unit string
        
    Returns:
        Normalized unit
    """
    return UNIT_NORMALIZATIONS.get(unit.lower(), unit)


def normalize_frequency(frequency: str) -> str:
    """
    Normalize medication frequency to readable format
    
    Args:
        frequency: Frequency string
        
    Returns:
        Normalized frequency
    """
    return FREQUENCY_NORMALIZATIONS.get(frequency.lower(), frequency)
