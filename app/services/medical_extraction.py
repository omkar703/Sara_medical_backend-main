"""
Medical Entity Extraction Service

Regex-based medical entity extraction from OCR text
"""
import re
from typing import Dict, List, Optional, Tuple

from app.models.schemas import MedicalEntity, EntityType
from app.utils import regex_patterns as patterns
from app.utils.confidence import calculate_entity_confidence, validate_medical_value, validate_blood_pressure


class MedicalExtractionService:
    """Service for extracting medical entities from text"""
    
    def __init__(self):
        pass
    
    def extract_patient_info(self, text: str) -> List[MedicalEntity]:
        """Extract patient demographics and identifiers"""
        entities = []
        
        # Extract patient name
        for pattern in patterns.PATIENT_NAME_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                name = match.group(1)
                if name and len(name) > 2:
                    entities.append(MedicalEntity(
                        entity_type=EntityType.PATIENT_NAME,
                        value=name,
                        confidence=calculate_entity_confidence(name, 0.9),
                        normalized_value=name.title()
                    ))
        
        # Extract age
        for pattern in patterns.PATIENT_AGE_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                age_str = match.group(1)
                try:
                    age = int(age_str)
                    if 0 < age < 120:  # Reasonable age range
                        entities.append(MedicalEntity(
                            entity_type=EntityType.PATIENT_AGE,
                            value=age_str,
                            confidence=calculate_entity_confidence(age_str, 0.95),
                            normalized_value=str(age),
                            unit="years"
                        ))
                except ValueError:
                    continue
        
        # Extract gender
        for pattern in patterns.PATIENT_GENDER_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                gender_raw = match.group(1)
                gender_normalized = gender_raw.upper()
                if gender_normalized in ['M', 'MALE']:
                    gender_normalized = 'Male'
                elif gender_normalized in ['F', 'FEMALE']:
                    gender_normalized = 'Female'
                
                entities.append(MedicalEntity(
                    entity_type=EntityType.PATIENT_GENDER,
                    value=gender_raw,
                    confidence=calculate_entity_confidence(gender_raw, 0.95),
                    normalized_value=gender_normalized
                ))
        
        # Extract patient ID/MRN
        for pattern in patterns.PATIENT_ID_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                patient_id = match.group(1)
                entities.append(MedicalEntity(
                    entity_type=EntityType.PATIENT_ID,
                    value=patient_id,
                    confidence=calculate_entity_confidence(patient_id, 0.9),
                    normalized_value=patient_id.upper()
                ))
        
        return entities
    
    def extract_medications(self, text: str) -> List[MedicalEntity]:
        """Extract medication names, dosages, and frequencies"""
        entities = []
        
        # Extract medication names with dosages
        for pattern in patterns.MEDICATION_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                medication = match.group(0)
                entities.append(MedicalEntity(
                    entity_type=EntityType.MEDICATION,
                    value=medication,
                    confidence=calculate_entity_confidence(medication, 0.85),
                    normalized_value=medication.lower()
                ))
        
        # Extract dosages
        for pattern in patterns.DOSAGE_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                amount = match.group(1)
                unit = match.group(2)
                dosage = f"{amount} {unit}"
                normalized_unit = patterns.normalize_unit(unit)
                
                entities.append(MedicalEntity(
                    entity_type=EntityType.DOSAGE,
                    value=dosage,
                    confidence=calculate_entity_confidence(dosage, 0.9),
                    normalized_value=f"{amount} {normalized_unit}",
                    unit=normalized_unit
                ))
        
        # Extract frequencies
        for pattern in patterns.FREQUENCY_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                frequency = match.group(0)
                normalized_freq = patterns.normalize_frequency(frequency)
                
                entities.append(MedicalEntity(
                    entity_type=EntityType.FREQUENCY,
                    value=frequency,
                    confidence=calculate_entity_confidence(frequency, 0.85),
                    normalized_value=normalized_freq
                ))
        
        return entities
    
    def extract_vitals(self, text: str) -> List[MedicalEntity]:
        """Extract vital signs"""
        entities = []
        
        # Blood pressure
        for pattern in patterns.BLOOD_PRESSURE_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                systolic = match.group(1)
                diastolic = match.group(2)
                bp_value = f"{systolic}/{diastolic}"
                
                # Validate BP values
                try:
                    sys_val = float(systolic)
                    dia_val = float(diastolic)
                    is_valid, msg = validate_blood_pressure(sys_val, dia_val)
                    confidence = 0.9 if is_valid else 0.6
                except ValueError:
                    confidence = 0.5
                
                entities.append(MedicalEntity(
                    entity_type=EntityType.VITAL_SIGN,
                    value=bp_value,
                    confidence=confidence,
                    normalized_value=f"{systolic}/{diastolic} mmHg",
                    unit="mmHg"
                ))
        
        # Heart rate
        for pattern in patterns.HEART_RATE_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                hr = match.group(1)
                try:
                    hr_val = float(hr)
                    is_valid, _ = validate_medical_value(hr_val, "heart_rate")
                    confidence = 0.9 if is_valid else 0.6
                except ValueError:
                    confidence = 0.5
                
                entities.append(MedicalEntity(
                    entity_type=EntityType.VITAL_SIGN,
                    value=hr,
                    confidence=confidence,
                    normalized_value=f"{hr} bpm",
                    unit="bpm"
                ))
        
        # Temperature
        for pattern in patterns.TEMPERATURE_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                temp = match.group(1)
                unit = match.group(2)
                
                entities.append(MedicalEntity(
                    entity_type=EntityType.VITAL_SIGN,
                    value=f"{temp}°{unit}",
                    confidence=0.9,
                    normalized_value=f"{temp} {unit}",
                    unit=unit.upper()
                ))
        
        # SpO2
        for pattern in patterns.SPO2_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                spo2 = match.group(1)
                try:
                    spo2_val = float(spo2)
                    is_valid, _ = validate_medical_value(spo2_val, "spo2")
                    confidence = 0.9 if is_valid else 0.6
                except ValueError:
                    confidence = 0.5
                
                entities.append(MedicalEntity(
                    entity_type=EntityType.VITAL_SIGN,
                    value=f"{spo2}%",
                    confidence=confidence,
                    normalized_value=f"{spo2}%",
                    unit="%"
                ))
        
        return entities
    
    def extract_lab_values(self, text: str) -> List[MedicalEntity]:
        """Extract laboratory values"""
        entities = []
        
        # Glucose
        for pattern in patterns.GLUCOSE_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                glucose = match.group(1)
                try:
                    glucose_val = float(glucose)
                    is_valid, _ = validate_medical_value(glucose_val, "glucose")
                    confidence = 0.9 if is_valid else 0.6
                except ValueError:
                    confidence = 0.5
                
                entities.append(MedicalEntity(
                    entity_type=EntityType.LAB_VALUE,
                    value=glucose,
                    confidence=confidence,
                    normalized_value=f"{glucose} mg/dL",
                    unit="mg/dL"
                ))
        
        # HbA1c
        for pattern in patterns.HBA1C_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                hba1c = match.group(1)
                try:
                    hba1c_val = float(hba1c)
                    is_valid, _ = validate_medical_value(hba1c_val, "hba1c")
                    confidence = 0.9 if is_valid else 0.6
                except ValueError:
                    confidence = 0.5
                
                entities.append(MedicalEntity(
                    entity_type=EntityType.LAB_VALUE,
                    value=f"{hba1c}%",
                    confidence=confidence,
                    normalized_value=f"{hba1c}%",
                    unit="%"
                ))
        
        # Additional lab values (cholesterol, creatinine, hemoglobin, WBC)
        # Similar pattern - omitted for brevity, but would follow same structure
        
        return entities
    
    def extract_dates(self, text: str) -> List[MedicalEntity]:
        """Extract dates from text"""
        entities = []
        
        for pattern in patterns.DATE_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                date_str = match.group(0)
                entities.append(MedicalEntity(
                    entity_type=EntityType.DATE,
                    value=date_str,
                    confidence=0.85,
                    normalized_value=date_str
                ))
        
        return entities
    
    def extract_all_entities(self, text: str) -> List[MedicalEntity]:
        """
        Extract all medical entities from text
        
        Args:
            text: OCR extracted text
            
        Returns:
            List of extracted medical entities
        """
        all_entities = []
        
        all_entities.extend(self.extract_patient_info(text))
        all_entities.extend(self.extract_medications(text))
        all_entities.extend(self.extract_vitals(text))
        all_entities.extend(self.extract_lab_values(text))
        all_entities.extend(self.extract_dates(text))
        
        # Remove duplicates based on value and type
        unique_entities = []
        seen = set()
        for entity in all_entities:
            key = (entity.entity_type, entity.normalized_value or entity.value)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities


# Singleton instance
_medical_extraction_service: Optional[MedicalExtractionService] = None


def get_medical_extraction_service() -> MedicalExtractionService:
    """Get or create medical extraction service instance"""
    global _medical_extraction_service
    if _medical_extraction_service is None:
        _medical_extraction_service = MedicalExtractionService()
    return _medical_extraction_service
