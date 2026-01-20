"""
FHIR R4 Resource Mapper

Convert extracted medical data to FHIR R4 compliant resources
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.observation import Observation, ObservationComponent
from fhir.resources.patient import Patient
from fhir.resources.medicationstatement import MedicationStatement
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference
from fhir.resources.diagnosticreport import DiagnosticReport

from app.models.schemas import MedicalEntity, EntityType
from app.config import get_settings

settings = get_settings()


class FHIRMapper:
    """Service for converting extracted medical data to FHIR resources"""
    
    def __init__(self):
        self.base_url = settings.fhir_base_url or "https://api.healthcare.example.com/fhir"
    
    def generate_id(self, prefix: str = "resource") -> str:
        """Generate a unique FHIR resource ID"""
        return f"{prefix}-{uuid.uuid4()}"
    
    def create_patient_resource(
        self,
        entities: List[MedicalEntity],
        patient_id: Optional[str] = None
    ) -> Patient:
        """
        Create FHIR Patient resource from extracted entities
        
        Args:
            entities: List of extracted medical entities
            patient_id: Optional patient identifier
            
        Returns:
            FHIR Patient resource
        """
        # Extract patient information
        patient_name = None
        patient_gender = None
        patient_mrn = patient_id
        
        for entity in entities:
            if entity.entity_type == EntityType.PATIENT_NAME:
                patient_name = entity.value
            elif entity.entity_type == EntityType.PATIENT_GENDER:
                patient_gender = entity.normalized_value.lower() if entity.normalized_value else None
            elif entity.entity_type == EntityType.PATIENT_ID and not patient_mrn:
                patient_mrn = entity.value
        
        # Create Patient resource
        patient_data = {
            "resourceType": "Patient",
            "id": self.generate_id("patient"),
        }
        
        # Add identifier (MRN)
        if patient_mrn:
            patient_data["identifier"] = [{
                "system": f"{self.base_url}/identifier/mrn",
                "value": patient_mrn
            }]
        
        # Add name
        if patient_name:
            name_parts = patient_name.split()
            patient_data["name"] = [{
                "use": "official",
                "family": name_parts[-1] if name_parts else patient_name,
                "given": name_parts[:-1] if len(name_parts) > 1 else []
            }]
        
        # Add gender
        if patient_gender and patient_gender in ['male', 'female', 'other', 'unknown']:
            patient_data["gender"] = patient_gender
        
        return Patient(**patient_data)
    
    def create_observation_resource(
        self,
        entity: MedicalEntity,
        patient_reference: str,
        observation_id: Optional[str] = None
    ) -> Observation:
        """
        Create FHIR Observation resource for vitals or lab values
        
        Args:
            entity: Medical entity (vital sign or lab value)
            patient_reference: Reference to patient resource
            observation_id: Optional observation identifier
            
        Returns:
            FHIR Observation resource
        """
        obs_id = observation_id or self.generate_id("observation")
        
        # Determine observation code based on entity type
        code_system = "http://loinc.org"
        code_value = "UNKNOWN"
        display = entity.value
        
        # Map entity values to LOINC codes (simplified mapping)
        if "bp" in entity.value.lower() or "/" in entity.value:
            code_value = "85354-9"  # Blood pressure
            display = "Blood pressure"
        elif "bpm" in (entity.unit or ""):
            code_value = "8867-4"  # Heart rate
            display = "Heart rate"
        elif entity.entity_type == EntityType.LAB_VALUE:
            if "glucose" in entity.value.lower():
                code_value = "2339-0"  # Glucose
                display = "Glucose"
            elif "hba1c" in entity.value.lower() or "a1c" in entity.value.lower():
                code_value = "4548-4"  # HbA1c
                display = "Hemoglobin A1c"
        
        # Create observation resource
        observation_data = {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "code": {
                "coding": [{
                    "system": code_system,
                    "code": code_value,
                    "display": display
                }]
            },
            "subject": {
                "reference": patient_reference
            },
            "effectiveDateTime": datetime.utcnow().isoformat() + "Z"
        }
        
        # Add value
        if "/" in entity.value:  # Blood pressure
            # Split systolic/diastolic
            parts = entity.value.split("/")
            if len(parts) == 2:
                observation_data["component"] = [
                    {
                        "code": {
                            "coding": [{
                                "system": "http://loinc.org",
                                "code": "8480-6",
                                "display": "Systolic blood pressure"
                            }]
                        },
                        "valueQuantity": {
                            "value": float(parts[0]),
                            "unit": "mmHg",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]"
                        }
                    },
                    {
                        "code": {
                            "coding": [{
                                "system": "http://loinc.org",
                                "code": "8462-4",
                                "display": "Diastolic blood pressure"
                            }]
                        },
                        "valueQuantity": {
                            "value": float(parts[1]),
                            "unit": "mmHg",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]"
                        }
                    }
                ]
        else:
            # Simple numeric value
            try:
                value_str = entity.value.replace("%", "").replace("bpm", "").strip()
                numeric_value = float(value_str)
                observation_data["valueQuantity"] = {
                    "value": numeric_value,
                    "unit": entity.unit or "",
                    "system": "http://unitsofmeasure.org"
                }
            except (ValueError, AttributeError):
                observation_data["valueString"] = entity.value
        
        return Observation(**observation_data)
    
    def create_medication_statement(
        self,
        entities: List[MedicalEntity],
        patient_reference: str
    ) -> List[MedicationStatement]:
        """
        Create FHIR MedicationStatement resources
        
        Args:
            entities: List of medication entities
            patient_reference: Reference to patient resource
            
        Returns:
            List of FHIR MedicationStatement resources
        """
        statements = []
        
        # Group medications with their dosages and frequencies
        medications = [e for e in entities if e.entity_type == EntityType.MEDICATION]
        
        for med_entity in medications:
            statement_data = {
                "resourceType": "MedicationStatement",
                "id": self.generate_id("medstatement"),
                "status": "active",
                "medicationCodeableConcept": {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "display": med_entity.value
                    }],
                    "text": med_entity.value
                },
                "subject": {
                    "reference": patient_reference
                },
                "effectiveDateTime": datetime.utcnow().isoformat() + "Z"
            }
            
            statements.append(MedicationStatement(**statement_data))
        
        return statements
    
    def create_diagnostic_report(
        self,
        text: str,
        entities: List[MedicalEntity],
        patient_reference: str
    ) -> DiagnosticReport:
        """
        Create FHIR DiagnosticReport wrapping OCR results
        
        Args:
            text: Extracted OCR text
            entities: Extracted medical entities
            patient_reference: Reference to patient resource
            
        Returns:
            FHIR DiagnosticReport resource
        """
        report_data = {
            "resourceType": "DiagnosticReport",
            "id": self.generate_id("report"),
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "11488-4",
                    "display": "Consultation note"
                }]
            },
            "subject": {
                "reference": patient_reference
            },
            "effectiveDateTime": datetime.utcnow().isoformat() + "Z",
            "issued": datetime.utcnow().isoformat() + "Z",
            "conclusion": text[:1000]  # First 1000 chars
        }
        
        return DiagnosticReport(**report_data)
    
    def generate_fhir_bundle(
        self,
        text: str,
        entities: List[MedicalEntity]
    ) -> Dict[str, Any]:
        """
        Generate complete FHIR Bundle with all resources
        
        Args:
            text: Extracted OCR text
            entities: Extracted medical entities
            
        Returns:
            FHIR Bundle as dictionary
        """
        # Create patient resource
        patient = self.create_patient_resource(entities)
        patient_ref = f"Patient/{patient.id}"
        
        # Create entries list
        entries = [
            {
                "fullUrl": f"{self.base_url}/{patient_ref}",
                "resource": patient.dict()
            }
        ]
        
        # Create observation resources for vitals and labs
        vitals_and_labs = [
            e for e in entities 
            if e.entity_type in [EntityType.VITAL_SIGN, EntityType.LAB_VALUE]
        ]
        
        for entity in vitals_and_labs:
            obs = self.create_observation_resource(entity, patient_ref)
            entries.append({
                "fullUrl": f"{self.base_url}/Observation/{obs.id}",
                "resource": obs.dict()
            })
        
        # Create medication statements
        med_statements = self.create_medication_statement(entities, patient_ref)
        for med_stmt in med_statements:
            entries.append({
                "fullUrl": f"{self.base_url}/MedicationStatement/{med_stmt.id}",
                "resource": med_stmt.dict()
            })
        
        # Create diagnostic report
        diagnostic_report = self.create_diagnostic_report(text, entities, patient_ref)
        entries.append({
            "fullUrl": f"{self.base_url}/DiagnosticReport/{diagnostic_report.id}",
            "resource": diagnostic_report.dict()
        })
        
        # Create bundle
        bundle_data = {
            "resourceType": "Bundle",
            "id": self.generate_id("bundle"),
            "type": "collection",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entry": entries
        }
        
        return bundle_data


# Singleton instance
_fhir_mapper_instance: Optional[FHIRMapper] = None


def get_fhir_mapper() -> FHIRMapper:
    """Get or create FHIR mapper instance"""
    global _fhir_mapper_instance
    if _fhir_mapper_instance is None:
        _fhir_mapper_instance = FHIRMapper()
    return _fhir_mapper_instance
