"""
Confidence Scoring and Validation Utilities
"""
from typing import Dict, List, Optional, Tuple

from app.utils.regex_patterns import NORMAL_RANGES


def calculate_ocr_confidence(ocr_data: str) -> float:
    """
    Calculate overall OCR confidence from Tesseract output
    
    Args:
        ocr_data: TSV output from Tesseract with confidence scores
        
    Returns:
        Average confidence score (0.0 to 1.0)
    """
    if not ocr_data or ocr_data.strip() == "":
        return 0.0
    
    lines = ocr_data.strip().split('\n')
    if len(lines) <= 1:  # Only header
        return 0.0
    
    confidences = []
    for line in lines[1:]:  # Skip header
        parts = line.split('\t')
        if len(parts) >= 12:  # Tesseract TSV format
            try:
                conf = float(parts[10])  # Confidence is in column 11 (index 10)
                if conf >= 0:  # Ignore -1 values
                    confidences.append(conf)
            except (ValueError, IndexError):
                continue
    
    if not confidences:
        return 0.5  # Default moderate confidence
    
    # Return average confidence normalized to 0-1
    return sum(confidences) / len(confidences) / 100.0


def calculate_word_confidence(ocr_data: str) -> List[Tuple[str, float]]:
    """
    Extract word-level confidence scores
    
    Args:
        ocr_data: TSV output from Tesseract
        
    Returns:
        List of (word, confidence) tuples
    """
    word_confidences = []
    
    if not ocr_data:
        return word_confidences
    
    lines = ocr_data.strip().split('\n')
    for line in lines[1:]:  # Skip header
        parts = line.split('\t')
        if len(parts) >= 12:
            word = parts[11].strip()
            try:
                conf = float(parts[10]) / 100.0
                if word and conf >= 0:
                    word_confidences.append((word, conf))
            except (ValueError, IndexError):
                continue
    
    return word_confidences


def calculate_entity_confidence(
    extracted_value: str,
    pattern_match_quality: float = 1.0,
    context_score: float = 1.0
) -> float:
    """
    Calculate confidence score for extracted medical entity
    
    Args:
        extracted_value: The extracted value
        pattern_match_quality: Quality of regex match (0.0 to 1.0)
        context_score: Contextual confidence based on surrounding text (0.0 to 1.0)
        
    Returns:
        Overall entity confidence (0.0 to 1.0)
    """
    # Base confidence from pattern match
    confidence = pattern_match_quality
    
    # Adjust based on value completeness
    if not extracted_value or extracted_value.strip() == "":
        return 0.0
    
    # Boost confidence if value looks complete and well-formed
    if len(extracted_value) >= 3:
        confidence *= 1.0
    else:
        confidence *= 0.8
    
    # Apply context score
    confidence *= context_score
    
    # Ensure within bounds
    return max(0.0, min(1.0, confidence))


def validate_medical_value(
    value: float,
    value_type: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate if medical value falls within expected ranges
    
    Args:
        value: Numeric value to validate
        value_type: Type of medical value (e.g., 'systolic_bp', 'glucose')
        
    Returns:
        Tuple of (is_valid, warning_message)
    """
    if value_type not in NORMAL_RANGES:
        return True, None  # No range defined, assume valid
    
    min_val, max_val = NORMAL_RANGES[value_type]
    
    if value < min_val:
        return False, f"Value {value} is below normal range ({min_val}-{max_val})"
    elif value > max_val:
        return False, f"Value {value} is above normal range ({min_val}-{max_val})"
    
    return True, None


def validate_blood_pressure(systolic: float, diastolic: float) -> Tuple[bool, Optional[str]]:
    """
    Validate blood pressure reading
    
    Args:
        systolic: Systolic BP value
        diastolic: Diastolic BP value
        
    Returns:
        Tuple of (is_valid, warning_message)
    """
    # Check individual values
    sys_valid, sys_msg = validate_medical_value(systolic, "systolic_bp")
    dia_valid, dia_msg = validate_medical_value(diastolic, "diastolic_bp")
    
    if not sys_valid:
        return False, sys_msg
    if not dia_valid:
        return False, dia_msg
    
    # Systolic should be higher than diastolic
    if systolic <= diastolic:
        return False, f"Systolic ({systolic}) should be higher than diastolic ({diastolic})"
    
    # Check pulse pressure (difference should be reasonable)
    pulse_pressure = systolic - diastolic
    if pulse_pressure < 20:
        return False, f"Pulse pressure ({pulse_pressure}) is too narrow"
    elif pulse_pressure > 100:
        return False, f"Pulse pressure ({pulse_pressure}) is too wide"
    
    return True, None


def validate_temperature(value: float, unit: str) -> Tuple[bool, Optional[str]]:
    """
    Validate temperature reading
    
    Args:
        value: Temperature value
        unit: Unit ('C' or 'F')
        
    Returns:
        Tuple of (is_valid, warning_message)
    """
    if unit.upper() == 'C':
        return validate_medical_value(value, "temperature_c")
    elif unit.upper() == 'F':
        return validate_medical_value(value, "temperature_f")
    else:
        return False, f"Unknown temperature unit: {unit}"


def calculate_page_confidence(
    ocr_confidence: float,
    entity_confidences: List[float]
) -> float:
    """
    Calculate overall confidence for a page
    
    Args:
        ocr_confidence: Base OCR confidence
        entity_confidences: List of entity extraction confidences
        
    Returns:
        Overall page confidence
    """
    if not entity_confidences:
        return ocr_confidence
    
    # Weighted average: 60% OCR, 40% entity extraction
    avg_entity_confidence = sum(entity_confidences) / len(entity_confidences)
    overall = (ocr_confidence * 0.6) + (avg_entity_confidence * 0.4)
    
    return max(0.0, min(1.0, overall))


def assess_extraction_quality(
    num_entities: int,
    avg_confidence: float,
    num_validation_errors: int
) -> Dict[str, any]:
    """
    Assess overall quality of medical data extraction
    
    Args:
        num_entities: Number of entities extracted
        avg_confidence: Average confidence score
        num_validation_errors: Number of validation errors
        
    Returns:
        Quality assessment dictionary
    """
    quality_score = 0.0
    quality_level = "poor"
    recommendations = []
    
    # Score based on number of entities
    if num_entities >= 10:
        entity_score = 1.0
    elif num_entities >= 5:
        entity_score = 0.7
    elif num_entities >= 1:
        entity_score = 0.4
    else:
        entity_score = 0.0
        recommendations.append("Very few entities extracted. Document may be unclear or not medical.")
    
    # Score based on confidence
    confidence_score = avg_confidence
    if avg_confidence < 0.5:
        recommendations.append("Low OCR confidence. Consider rescanning at higher quality.")
    
    # Penalty for validation errors
    error_penalty = min(num_validation_errors * 0.1, 0.5)
    
    # Calculate overall quality
    quality_score = (entity_score * 0.5 + confidence_score * 0.5) - error_penalty
    quality_score = max(0.0, min(1.0, quality_score))
    
    # Determine quality level
    if quality_score >= 0.8:
        quality_level = "excellent"
    elif quality_score >= 0.6:
        quality_level = "good"
    elif quality_score >= 0.4:
        quality_level = "fair"
    else:
        quality_level = "poor"
        recommendations.append("Consider manual review of extracted data.")
    
    return {
        "quality_score": round(quality_score, 2),
        "quality_level": quality_level,
        "num_entities": num_entities,
        "average_confidence": round(avg_confidence, 2),
        "validation_errors": num_validation_errors,
        "recommendations": recommendations
    }
