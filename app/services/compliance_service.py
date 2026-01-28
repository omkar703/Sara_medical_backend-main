"""Compliance Service"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import pii_encryption
from app.models.audit import AuditLog
from app.models.consultation import Consultation
from app.models.document import Document
from app.models.patient import Patient
from app.models.user import User


class ComplianceService:
    """Service for GDPR/HIPAA compliance requests"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def export_my_data(self, user_id: UUID) -> dict:
        """
        Export all personal data associated with the user.
        Return as dictionary structure.
        """
        # 1. User Profile
        user = await self.db.get(User, user_id)
        if not user:
            return {}
            
        # Decrypt PII with safety
        def safe_decrypt(ciphertext, field_name):
            if not ciphertext:
                return None
            try:
                return pii_encryption.decrypt(ciphertext)
            except Exception as e:
                print(f"ERROR: Decryption failed for {field_name}: {e}")
                print(f"TEXT: {ciphertext[:10]}...")
                return f"[DECRYPTION_ERROR: {field_name}]"

        user_data = {
            "full_name": safe_decrypt(user.full_name, "full_name"),
            "email": user.email,
            "role": str(user.role).split('.')[-1] if hasattr(user.role, 'value') else str(user.role),
            "phone_number": safe_decrypt(user.phone_number, "phone_number"),
            "specialty": user.specialty,
            "license_number": safe_decrypt(user.license_number, "license_number"),
            "created_at": user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat(),
        }
        
        # 2. Activity (Consultations) - if Doctor
        consultations_data = []
        if user.role == "doctor":
            result = await self.db.execute(select(Consultation).where(Consultation.doctor_id == user_id))
            consultations = result.scalars().all()
            for c in consultations:
                consultations_data.append({
                    "id": str(c.id),
                    "scheduled_at": c.scheduled_at.isoformat(),
                    "status": c.status,
                    "notes": c.notes
                })
        
        # 3. Documents - if Doctor (uploaded by) ??? 
        # Actually document doesn't track 'uploaded_by' on the model explicitly in Phase 4 code,
        # but AuditLog tracks it.
        # For 'Right to Portability', usually it's "Data provided by the user".
        
        return {
            "profile": user_data,
            "consultations": consultations_data,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def delete_account(self, user_id: UUID):
        """
        Request account deletion (Right to be Forgotten).
        Soft delete user, anonymize PII, but KEEP Audit Logs.
        """
        user = await self.db.get(User, user_id)
        if not user:
            return
            
        # 1. Anonymize PII in User table
        user.full_name = pii_encryption.encrypt("Deleted User")
        user.email = f"deleted-{user_id}@deleted.local" 
        user.phone_number = None
        user.mfa_secret = None
        user.password_hash = "deleted"
        
        # 2. Soft Delete
        user.deleted_at = datetime.utcnow()
        
        # 3. Handle specific role data
        # If Patient, we might keep medical records but unlink? 
        # HIPAA says medical records must be kept for 6+ years. 
        # So usually "Delete Account" for a patient means "Revoke Access + Soft Delete", not "Purge Data".
        # We implemented Soft Delete on User model.
        
        # 4. Audit Log
        # We ensure audit logs remain linked to the UUID, even if User is "Deleted".
        # We do NOT delete audit logs.
        
        await self.db.flush()
        return True
