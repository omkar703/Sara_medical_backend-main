"""Tests for Patient Management"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, PIIEncryption
from app.models.patient import Patient
from app.models.audit import AuditLog
from sqlalchemy import select


@pytest_asyncio.fixture
async def doctor_token(db_session: AsyncSession, test_user):
    """Create a token for a doctor user"""
    # Ensure user is doctor
    test_user.role = "doctor"
    await db_session.commit()
    return create_access_token({"sub": str(test_user.id), "role": "doctor"})


@pytest_asyncio.fixture
async def patient_payload():
    return {
        "fullName": "John Doe",
        "dateOfBirth": "1980-05-15",
        "gender": "male",
        "phoneNumber": "+1234567890",
        "email": "john@example.com",
        "address": {
            "street": "123 Main St",
            "city": "Boston",
            "state": "MA",
            "zipCode": "02101"
        },
        "medicalHistory": "Hypertension"
    }


@pytest.mark.asyncio
async def test_create_patient(
    client: AsyncClient, doctor_token: str, patient_payload: dict, db_session: AsyncSession
):
    """Test creating a patient with encrypted data"""
    response = await client.post(
        "/api/v1/patients",
        json=patient_payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["fullName"] == patient_payload["fullName"]
    assert data["mrn"].startswith("ORG-")
    assert "id" in data
    
    # Verify encryption in DB
    patient_id = data["id"]
    result = await db_session.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one()
    
    # Should NOT match plain text
    assert patient.full_name != patient_payload["fullName"]
    assert patient.medical_history != patient_payload["medicalHistory"]
    
    # Decrypt to verify
    encryption = PIIEncryption()
    assert encryption.decrypt(patient.full_name) == patient_payload["fullName"]


@pytest.mark.asyncio
async def test_list_patients(
    client: AsyncClient, doctor_token: str, patient_payload: dict
):
    """Test listing patients with pagination"""
    # Create one patient first
    await client.post(
        "/api/v1/patients",
        json=patient_payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    
    response = await client.get(
        "/api/v1/patients",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["patients"]) >= 1
    assert data["patients"][0]["fullName"] == patient_payload["fullName"]


@pytest.mark.asyncio
async def test_get_patient(
    client: AsyncClient, doctor_token: str, patient_payload: dict
):
    """Test retrieving a single patient"""
    # Create
    create_res = await client.post(
        "/api/v1/patients",
        json=patient_payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    patient_id = create_res.json()["id"]
    
    # Get
    response = await client.get(
        f"/api/v1/patients/{patient_id}",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == patient_id
    assert data["fullName"] == patient_payload["fullName"]


@pytest.mark.asyncio
async def test_update_patient(
    client: AsyncClient, doctor_token: str, patient_payload: dict
):
    """Test updating patient details"""
    # Create
    create_res = await client.post(
        "/api/v1/patients",
        json=patient_payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    patient_id = create_res.json()["id"]
    
    # Update
    update_payload = {"fullName": "Jane Doe"}
    response = await client.put(
        f"/api/v1/patients/{patient_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["fullName"] == "Jane Doe"
    
    # Verify other fields remain
    assert data["gender"] == patient_payload["gender"]


@pytest.mark.asyncio
async def test_audit_logging(
    client: AsyncClient, doctor_token: str, patient_payload: dict, db_session: AsyncSession
):
    """Test that actions generate audit logs"""
    # Create action
    response = await client.post(
        "/api/v1/patients",
        json=patient_payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    patient_id = response.json()["id"]
    
    # Verify log exists
    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.resource_id == patient_id,
            AuditLog.action == "create"
        )
    )
    log_entry = result.scalar_one_or_none()
    assert log_entry is not None


@pytest.mark.asyncio
async def test_search_patients(
    client: AsyncClient, doctor_token: str, patient_payload: dict
):
    """Test searching patients by MRN"""
    # Create two patients
    res1 = await client.post(
        "/api/v1/patients",
        json=patient_payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    data1 = res1.json()
    mrn1 = data1["mrn"]
    
    payload2 = patient_payload.copy()
    payload2["fullName"] = "Another Patient"
    res2 = await client.post(
        "/api/v1/patients",
        json=payload2,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    data2 = res2.json()
    mrn2 = data2["mrn"]
    
    # Search for first patient
    response = await client.get(
        f"/api/v1/patients?search={mrn1}",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["patients"]) == 1
    assert data["patients"][0]["id"] == data1["id"]
    assert data["patients"][0]["mrn"] == mrn1
    
    # Search for second patient
    response = await client.get(
        f"/api/v1/patients?search={mrn2}",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["patients"]) == 1
    assert data["patients"][0]["mrn"] == mrn2
