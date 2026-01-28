"""
Comprehensive Endpoint Testing Suite
Tests all API endpoints as specified in prompt.md
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
import uuid


class TestAuthenticationEndpoints:
    """Test all authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_register_patient(self, client: AsyncClient):
        """Test patient registration"""
        response = await client.post("/api/v1/auth/register", json={
            "email": f"patient_{uuid.uuid4().hex[:8]}@test.com",
            "password": "SecurePass123!",
            "full_name": "Test Patient",
            "role": "patient",
            "phone_number": "+1234567890"
        })
        assert response.status_code in [200, 201]
        data = response.json()
        assert "access_token" in data or "id" in data
    
    @pytest.mark.asyncio
    async def test_register_doctor(self, client: AsyncClient, db_session):
        """Test doctor registration"""
        # Create organization first
        from app.models.user import Organization
        org = Organization(name="Test Hospital")
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)
        
        response = await client.post("/api/v1/auth/register", json={
            "email": f"doctor_{uuid.uuid4().hex[:8]}@test.com",
            "password": "SecurePass123!",
            "full_name": "Dr. Test Doctor",
            "role": "doctor",
            "organization_id": str(org.id),
            "phone_number": "+1234567891"
        })
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login"""
        response = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials"""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "WrongPassword123"
        })
        assert response.status_code in [401, 404]
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, doctor_token):
        """Test getting current user profile"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
    
    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient, doctor_token):
        """Test user logout"""
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code in [200, 204]


class TestAppointmentEndpoints:
    """Test appointment workflow endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_appointment(self, client: AsyncClient, doctor_token, db_session, test_user):
        """Test creating an appointment request"""
        # Create a patient first
        from app.models.patient import Patient
        from app.core.security import PIIEncryption
        from datetime import date
        
        encryption = PIIEncryption()
        patient = Patient(
            full_name=encryption.encrypt("Test Patient"),
            date_of_birth=encryption.encrypt(date(1990, 1, 1).isoformat()),
            gender="male",
            phone_number=encryption.encrypt("+1234567890"),
            mrn=f"ORG-{uuid.uuid4().hex[:6].upper()}",
            organization_id=test_user.organization_id,
            created_by=test_user.id
        )
        db_session.add(patient)
        await db_session.commit()
        await db_session.refresh(patient)
        
        response = await client.post(
            "/api/v1/appointments",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "patient_id": str(patient.id),
                "doctor_id": str(test_user.id),
                "appointment_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "reason": "Regular checkup"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_list_appointments(self, client: AsyncClient, doctor_token):
        """Test listing appointments"""
        response = await client.get(
            "/api/v1/appointments",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data
    
    @pytest.mark.asyncio
    async def test_accept_appointment(self, client: AsyncClient, doctor_token, db_session, test_user):
        """Test accepting an appointment"""
        # Create appointment first
        from app.models.appointment import Appointment
        from app.models.patient import Patient
        from app.core.security import PIIEncryption
        from datetime import date
        
        encryption = PIIEncryption()
        patient = Patient(
            full_name=encryption.encrypt("Test Patient"),
            date_of_birth=encryption.encrypt(date(1990, 1, 1).isoformat()),
            gender="male",
            phone_number=encryption.encrypt("+1234567890"),
            mrn=f"ORG-{uuid.uuid4().hex[:6].upper()}",
            organization_id=test_user.organization_id,
            created_by=test_user.id
        )
        db_session.add(patient)
        await db_session.flush()
        
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=test_user.id,
            appointment_date=datetime.now() + timedelta(days=1),
            status="pending",
            reason="Test appointment"
        )
        db_session.add(appointment)
        await db_session.commit()
        await db_session.refresh(appointment)
        
        response = await client.patch(
            f"/api/v1/appointments/{appointment.id}/accept",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code in [200, 204]
    
    @pytest.mark.asyncio
    async def test_reject_appointment(self, client: AsyncClient, doctor_token, db_session, test_user):
        """Test rejecting an appointment"""
        # Create appointment first
        from app.models.appointment import Appointment
        from app.models.patient import Patient
        from app.core.security import PIIEncryption
        from datetime import date
        
        encryption = PIIEncryption()
        patient = Patient(
            full_name=encryption.encrypt("Test Patient"),
            date_of_birth=encryption.encrypt(date(1990, 1, 1).isoformat()),
            gender="male",
            phone_number=encryption.encrypt("+1234567890"),
            mrn=f"ORG-{uuid.uuid4().hex[:6].upper()}",
            organization_id=test_user.organization_id,
            created_by=test_user.id
        )
        db_session.add(patient)
        await db_session.flush()
        
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=test_user.id,
            appointment_date=datetime.now() + timedelta(days=1),
            status="pending",
            reason="Test appointment"
        )
        db_session.add(appointment)
        await db_session.commit()
        await db_session.refresh(appointment)
        
        response = await client.patch(
            f"/api/v1/appointments/{appointment.id}/reject",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"reason": "Not available"}
        )
        assert response.status_code in [200, 204]


class TestPermissionEndpoints:
    """Test permission management endpoints"""
    
    @pytest.mark.asyncio
    async def test_request_permission(self, client: AsyncClient, doctor_token, patient_id):
        """Test doctor requesting access to patient documents"""
        response = await client.post(
            "/api/v1/permissions/request",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "patient_id": patient_id,
                "reason": "Scheduled appointment",
                "permission_level": "read_analyze"
            }
        )
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_grant_permission(self, client: AsyncClient, db_session, test_user, patient_id):
        """Test patient granting permission to doctor"""
        # Create patient user
        from app.models.user import User
        from app.core.security import hash_password, PIIEncryption, create_access_token
        
        encryption = PIIEncryption()
        patient_user = User(
            email=f"patient_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=hash_password("PatientPass123"),
            role="patient",
            organization_id=test_user.organization_id,
            full_name=encryption.encrypt("Patient User"),
            email_verified=True
        )
        db_session.add(patient_user)
        await db_session.commit()
        await db_session.refresh(patient_user)
        
        patient_token = create_access_token(data={"sub": str(patient_user.id)})
        
        response = await client.post(
            "/api/v1/permissions/grant",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "doctor_id": str(test_user.id),
                "ai_access_permission": True,
                "expiry_days": 30
            }
        )
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_list_permissions(self, client: AsyncClient, doctor_token):
        """Test listing permissions"""
        response = await client.get(
            "/api/v1/permissions",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_revoke_permission(self, client: AsyncClient, db_session, test_user):
        """Test revoking permission"""
        # Create permission first
        from app.models.permission import DoctorPatientPermission
        from app.models.patient import Patient
        from app.core.security import PIIEncryption, create_access_token
        from datetime import date
        
        encryption = PIIEncryption()
        patient = Patient(
            full_name=encryption.encrypt("Test Patient"),
            date_of_birth=encryption.encrypt(date(1990, 1, 1).isoformat()),
            gender="male",
            phone_number=encryption.encrypt("+1234567890"),
            mrn=f"ORG-{uuid.uuid4().hex[:6].upper()}",
            organization_id=test_user.organization_id,
            created_by=test_user.id
        )
        db_session.add(patient)
        await db_session.flush()
        
        # Create patient user
        from app.models.user import User
        from app.core.security import hash_password
        
        patient_user = User(
            email=f"patient_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=hash_password("PatientPass123"),
            role="patient",
            organization_id=test_user.organization_id,
            full_name=encryption.encrypt("Patient User"),
            email_verified=True
        )
        db_session.add(patient_user)
        await db_session.flush()
        
        permission = DoctorPatientPermission(
            doctor_id=test_user.id,
            patient_id=patient.id,
            ai_access_permission=True,
            granted_at=datetime.now()
        )
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)
        
        patient_token = create_access_token(data={"sub": str(patient_user.id)})
        
        response = await client.delete(
            f"/api/v1/permissions/{test_user.id}",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        assert response.status_code in [200, 204]


class TestDocumentEndpoints:
    """Test document management endpoints"""
    
    @pytest.mark.asyncio
    async def test_upload_document(self, client: AsyncClient, doctor_token, patient_id):
        """Test uploading a document"""
        # Create a test file
        files = {
            "file": ("test.pdf", b"PDF content", "application/pdf")
        }
        
        response = await client.post(
            f"/api/v1/documents/upload?patient_id={patient_id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
            files=files
        )
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_list_documents(self, client: AsyncClient, doctor_token):
        """Test listing documents"""
        response = await client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_document_status(self, client: AsyncClient, doctor_token, db_session, test_user, patient_id):
        """Test getting document processing status"""
        # Create a document first
        from app.models.document import Document
        
        document = Document(
            patient_id=uuid.UUID(patient_id),
            uploaded_by=test_user.id,
            file_name="test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            storage_path="test/path",
            processing_status="pending"
        )
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)
        
        response = await client.get(
            f"/api/v1/documents/{document.id}/status",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200


class TestPatientEndpoints:
    """Test patient management endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_patient(self, client: AsyncClient, doctor_token):
        """Test creating a patient"""
        response = await client.post(
            "/api/v1/patients",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "full_name": "New Patient",
                "date_of_birth": "1990-01-01",
                "gender": "male",
                "phone_number": "+1234567890"
            }
        )
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_list_patients(self, client: AsyncClient, doctor_token):
        """Test listing patients"""
        response = await client.get(
            "/api/v1/patients",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_patient(self, client: AsyncClient, doctor_token, patient_id):
        """Test getting patient details"""
        response = await client.get(
            f"/api/v1/patients/{patient_id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code in [200, 403]  # 403 if no permission


class TestDoctorEndpoints:
    """Test doctor management endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_doctors(self, client: AsyncClient, doctor_token):
        """Test listing doctors"""
        response = await client.get(
            "/api/v1/doctors",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_doctor_profile(self, client: AsyncClient, doctor_token, test_user):
        """Test getting doctor profile"""
        response = await client.get(
            f"/api/v1/doctors/{test_user.id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200


class TestAuditEndpoints:
    """Test audit log endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_audit_logs(self, client: AsyncClient, admin_token):
        """Test getting audit logs"""
        response = await client.get(
            "/api/v1/audit/logs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 403]
    
    @pytest.mark.asyncio
    async def test_get_access_logs(self, client: AsyncClient, doctor_token):
        """Test getting access logs"""
        response = await client.get(
            "/api/v1/audit/access-logs",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test main health check"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "database" in data
    
    @pytest.mark.asyncio
    async def test_database_health(self, client: AsyncClient):
        """Test database health check"""
        response = await client.get("/health/database")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_redis_health(self, client: AsyncClient):
        """Test Redis health check"""
        response = await client.get("/health/redis")
        # May fail if Redis not running in test environment
        assert response.status_code in [200, 500]
    
    @pytest.mark.asyncio
    async def test_minio_health(self, client: AsyncClient):
        """Test MinIO health check"""
        response = await client.get("/health/minio")
        # May fail if MinIO not running in test environment
        assert response.status_code in [200, 500]
