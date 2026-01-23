import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

@pytest.mark.asyncio
async def test_request_upload_url(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str
):
    """Test generating a presigned upload URL"""
    response = await async_client.post(
        "/api/v1/documents/upload-url",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "fileName": "test_report.pdf",
            "fileType": "application/pdf",
            "fileSize": 1024 * 1024,  # 1MB
            "patientId": patient_id
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "uploadUrl" in data
    assert "documentId" in data
    assert "expiresIn" in data
    return data["documentId"]

@pytest.mark.asyncio
async def test_confirm_upload(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str
):
    """Test confirming a document upload"""
    # First get an upload URL to create the document
    upload_response = await async_client.post(
        "/api/v1/documents/upload-url",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "fileName": "lab_results.pdf",
            "fileType": "application/pdf",
            "fileSize": 500000,
            "patientId": patient_id
        }
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["documentId"]
    
    # Confirm the upload
    response = await async_client.post(
        f"/api/v1/documents/{document_id}/confirm",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "metadata": {
                "title": "Blood Test Results",
                "category": "lab-result",
                "notes": "Normal levels"
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document_id
    assert data["title"] == "Blood Test Results"
    assert data["category"] == "lab-result"
    assert data["virusScanned"] is False  # Should be false initially

@pytest.mark.asyncio
async def test_list_documents(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str
):
    """Test listing documents with filters"""
    # Create two documents
    for category in ["lab-result", "prescription"]:
        # 1. Upload URL
        upload_resp = await async_client.post(
            "/api/v1/documents/upload-url",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "fileName": f"{category}.pdf",
                "fileType": "application/pdf",
                "fileSize": 1000,
                "patientId": patient_id
            }
        )
        doc_id = upload_resp.json()["documentId"]
        
        # 2. Confirm
        await async_client.post(
            f"/api/v1/documents/{doc_id}/confirm",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"metadata": {"category": category}}
        )

    # Test listing all
    response = await async_client.get(
        f"/api/v1/documents?patient_id={patient_id}",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) >= 2
    
    # Test filtering by category
    response = await async_client.get(
        f"/api/v1/documents?patient_id={patient_id}&category=prescription",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    # Should check that at least one is returned and all match category
    assert len(data["documents"]) > 0
    assert all(d["category"] == "prescription" for d in data["documents"])

@pytest.mark.asyncio
async def test_get_document(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str
):
    """Test retrieving single document details"""
    # Create document
    upload_resp = await async_client.post(
        "/api/v1/documents/upload-url",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "fileName": "scan.jpg",
            "fileType": "image/jpeg",
            "fileSize": 2048,
            "patientId": patient_id
        }
    )
    doc_id = upload_resp.json()["documentId"]
    
    # Get document
    response = await async_client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert "downloadUrl" in data

@pytest.mark.asyncio
async def test_delete_document(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str
):
    """Test soft deleting a document"""
    # Create document
    upload_resp = await async_client.post(
        "/api/v1/documents/upload-url",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "fileName": "todelete.pdf",
            "fileType": "application/pdf",
            "fileSize": 1000,
            "patientId": patient_id
        }
    )
    doc_id = upload_resp.json()["documentId"]
    
    # Delete
    response = await async_client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = await async_client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_invalid_upload_request(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str
):
    """Test validation errors for upload request"""
    # Invalid file type
    response = await async_client.post(
        "/api/v1/documents/upload-url",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "fileName": "malware.exe",
            "fileType": "application/x-msdownload", 
            "fileSize": 1000,
            "patientId": patient_id
        }
    )
    assert response.status_code == 422
    
    # File too large
    response = await async_client.post(
        "/api/v1/documents/upload-url",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "fileName": "large.pdf",
            "fileType": "application/pdf",
            "fileSize": 200 * 1024 * 1024, # 200MB
            "patientId": patient_id
        }
    )
    assert response.status_code == 422
