"""Patient Management Service"""

import json
from datetime import date, datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import PIIEncryption
from app.models.patient import Patient


class PatientService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.encryption = PIIEncryption()

    async def generate_mrn(self, organization_id: UUID) -> str:
        """
        Generate sequential MRN for an organization
        Format: ORG-{YEAR}-{SEQUENCE}
        Example: ORG-2024-000001
        """
        # Get count of patients for this org to determine sequence
        # Note: This is a simple implementation. In high concurrency, 
        # use a dedicated sequence or Redis counter.
        stmt = select(func.count()).select_from(Patient).where(
            Patient.organization_id == organization_id
        )
        count = await self.db.scalar(stmt)
        sequence = (count or 0) + 1
        year = datetime.now().year
        
        # In a real app, you might want a custom prefix per org
        return f"ORG-{year}-{sequence:06d}"

    def encrypt_patient_data(self, data: Dict) -> Dict:
        """Encrypt PII fields in patient data dictionary"""
        encrypted_data = data.copy()
        
        # String fields
        for field in ['full_name', 'phone_number', 'email', 'medical_history']:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encryption.encrypt(encrypted_data[field])

        # Date field
        if 'date_of_birth' in encrypted_data and encrypted_data['date_of_birth']:
            # Convert date to ISO format string before encryption
            dob = encrypted_data['date_of_birth']
            if isinstance(dob, (date, datetime)):
                dob = dob.isoformat()
            encrypted_data['date_of_birth'] = self.encryption.encrypt(str(dob))
            
        # JSON fields - keep as dict but might want to encrypt values internally
        # OR encrypt the whole JSON dump as a string if the DB col was String.
        # But we defined them as JSONB in model (except medical history), 
        # so for high security we should actually encrypt the sensitive values inside the JSON,
        # or encrypt the whole blob and store as text.
        # Given the model definition:
        # address: JSONB
        # emergency_contact: JSONB
        # allergies: JSONB
        # medications: JSONB
        
        # Current strategy: Encrypt specific PII values inside the JSON structures 
        # OR implementation plan said "Encrypt PII fields... address: JSON (encrypted)".
        # To strictly follow "Encrypted", we should probably change schema to store encrypted strings 
        # or encypt leaf nodes. 
        # Let's encrypt the entire JSON structure and store as a JSON string containing ciphertext, start simple.
        # Actually my model definition says `address: Mapped[dict] = mapped_column(JSONB, nullable=True)`.
        # Postgres JSONB expects valid JSON. I cannot store a raw encrypted string there unless it's `{"data": "ciphertext"}`.
        
        # Let's stick to encrypting the whole dictionary and storing it in a wrapper for now, 
        # OR encrypting leaf values. Encrypting leaf values preserves structure.
        
        if 'address' in encrypted_data and encrypted_data['address']:
            # Encrypt values inside address
            addr = encrypted_data['address']
            encrypted_addr = {
                k: self.encryption.encrypt(str(v)) if v else v 
                for k, v in addr.items()
            }
            encrypted_data['address'] = encrypted_addr

        if 'emergency_contact' in encrypted_data and encrypted_data['emergency_contact']:
            contact = encrypted_data['emergency_contact']
            encrypted_contact = {
                k: self.encryption.encrypt(str(v)) if v else v
                for k, v in contact.items()
            }
            encrypted_data['emergency_contact'] = encrypted_contact
            
        # Lists (Allergies, Medications) - Encrypt each item
        if 'allergies' in encrypted_data and encrypted_data['allergies']:
            encrypted_data['allergies'] = [
                self.encryption.encrypt(item) for item in encrypted_data['allergies']
            ]
            
        if 'medications' in encrypted_data and encrypted_data['medications']:
            encrypted_data['medications'] = [
                self.encryption.encrypt(item) for item in encrypted_data['medications']
            ]
            
        return encrypted_data

    def decrypt_patient_data(self, patient: Patient) -> Dict:
        """Decrypt PII fields for API response"""
        # Convert SQLAlchemy model to dict
        data = {
            "id": patient.id,
            "mrn": patient.mrn,
            "organization_id": patient.organization_id,
            "gender": patient.gender,
            "created_at": patient.created_at,
            "updated_at": patient.updated_at
        }
        
        # Decrypt String fields
        if patient.full_name:
            data['full_name'] = self.encryption.decrypt(patient.full_name)
            
        if patient.phone_number:
            data['phone_number'] = self.encryption.decrypt(patient.phone_number)
            
        if patient.email:
            data['email'] = self.encryption.decrypt(patient.email)
            
        if patient.medical_history:
            data['medical_history'] = self.encryption.decrypt(patient.medical_history)
            
        # Decrypt Date
        if patient.date_of_birth:
            dob_str = self.encryption.decrypt(patient.date_of_birth)
            try:
                data['date_of_birth'] = date.fromisoformat(dob_str)
            except ValueError:
                data['date_of_birth'] = dob_str

        # Decrypt JSON fields
        if patient.address:
            data['address'] = {
                k: self.encryption.decrypt(v) if v else v 
                for k, v in patient.address.items()
            }
        else:
            data['address'] = None
            
        if patient.emergency_contact:
            data['emergency_contact'] = {
                k: self.encryption.decrypt(v) if v else v
                for k, v in patient.emergency_contact.items()
            }
        else:
            data['emergency_contact'] = None

        # Decrypt Lists
        if patient.allergies:
            data['allergies'] = [self.encryption.decrypt(i) for i in patient.allergies]
        else:
            data['allergies'] = []
            
        if patient.medications:
            data['medications'] = [self.encryption.decrypt(i) for i in patient.medications]
        else:
            data['medications'] = []
            
        return data

    async def create_patient(
        self, patient_data: Dict, organization_id: UUID, created_by: UUID
    ) -> Dict:
        """Create new patient"""
        mrn = await self.generate_mrn(organization_id)
        
        # Prepare data
        encrypted_data = self.encrypt_patient_data(patient_data)
        
        patient = Patient(
            mrn=mrn,
            organization_id=organization_id,
            created_by=created_by,
            **encrypted_data
        )
        
        self.db.add(patient)
        await self.db.flush() # Get ID
        
        return self.decrypt_patient_data(patient)

    async def get_patient(self, patient_id: UUID, organization_id: UUID) -> Optional[Dict]:
        """Get patient by ID"""
        result = await self.db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.organization_id == organization_id,
                Patient.deleted_at.is_(None)
            )
        )
        patient = result.scalar_one_or_none()
        
        if patient:
            return self.decrypt_patient_data(patient)
        return None

    async def list_patients(
        self, 
        organization_id: UUID, 
        page: int = 1, 
        limit: int = 20, 
        search: Optional[str] = None
    ) -> Dict:
        """List patients with pagination"""
        # Base query
        query = select(Patient).where(
            Patient.organization_id == organization_id,
            Patient.deleted_at.is_(None)
        )
        
        # TODO: Search implementation
        # Searching encrypted data is hard. 
        # Options:
        # 1. Fetch all and filter in memory (BAD for scale)
        # 2. Add blind index (deterministic encryption hash) for exact match
        # 3. Store search vector (unencrypted or partially masked) if allowed
        # For now, we will handle search by MRN (unencrypted) and skip name search
        # or implement in-memory filtering for small result sets (MVP approach).
        # Given "HIPAA compliant", let's search only MRN for now to be safe and fast.
        
        if search:
            query = query.where(Patient.mrn.ilike(f"%{search}%"))
            
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Pagination
        query = query.order_by(desc(Patient.created_at))
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        patients = result.scalars().all()
        
        return {
            "items": [self.decrypt_patient_data(p) for p in patients],
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }

    async def update_patient(
        self, patient_id: UUID, organization_id: UUID, patient_data: Dict
    ) -> Optional[Dict]:
        """Update patient"""
        result = await self.db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.organization_id == organization_id,
                Patient.deleted_at.is_(None)
            )
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            return None
            
        # Encrypt new data
        encrypted_updates = self.encrypt_patient_data(patient_data)
        
        for key, value in encrypted_updates.items():
            setattr(patient, key, value)
            
        return self.decrypt_patient_data(patient)

    async def delete_patient(
        self, patient_id: UUID, organization_id: UUID
    ) -> bool:
        """Soft delete patient"""
        result = await self.db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.organization_id == organization_id,
                Patient.deleted_at.is_(None)
            )
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            return False
            
        patient.deleted_at = datetime.utcnow()
        return True
