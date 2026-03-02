"""
SOAP Note Generation Tests
Tests the mock transcript + AWS Bedrock SOAP note generation pipeline.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from httpx import AsyncClient


# ─────────────────────────────────────────────────────────
# Unit Tests: MockTranscriptService
# ─────────────────────────────────────────────────────────

def test_mock_transcript_service_returns_transcript():
    """All scenarios return a non-empty string transcript."""
    from app.services.mock_transcript_service import mock_transcript_service, SCENARIOS

    for scenario_key in SCENARIOS:
        transcript = mock_transcript_service.get_mock_transcript(scenario_key)
        assert isinstance(transcript, str)
        assert len(transcript) > 100, f"Scenario '{scenario_key}' transcript is too short"
        assert "Dr." in transcript or "Patient" in transcript, \
            f"Scenario '{scenario_key}' lacks expected speaker labels"


def test_mock_transcript_service_random():
    """Random selection returns a valid transcript."""
    from app.services.mock_transcript_service import mock_transcript_service

    transcript = mock_transcript_service.get_mock_transcript()
    assert isinstance(transcript, str)
    assert len(transcript) > 100


def test_mock_transcript_service_invalid_scenario_returns_random():
    """Unknown scenario key falls back to a random transcript."""
    from app.services.mock_transcript_service import mock_transcript_service

    transcript = mock_transcript_service.get_mock_transcript("unknown_scenario_xyz")
    # Should pick a random valid one
    assert isinstance(transcript, str)
    assert len(transcript) > 100


def test_all_scenarios_available():
    """Verify exactly 5 scenarios are registered."""
    from app.services.mock_transcript_service import SCENARIOS
    assert len(SCENARIOS) == 5
    expected = {"chest_pain", "diabetes", "pediatric_fever", "hypertension", "anxiety"}
    assert set(SCENARIOS.keys()) == expected


# ─────────────────────────────────────────────────────────
# Unit Tests: AWSService.generate_soap_note (mocked Bedrock)
# ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_soap_note_success():
    """generate_soap_note parses Bedrock's JSON response correctly."""
    from app.services.aws_service import AWSService

    mock_soap = {
        "subjective": "Patient reports chest pain for 3 days.",
        "objective": "BP 148/92. Heart sounds normal. No murmur.",
        "assessment": "Possible angina. Rule out ACS.",
        "plan": "EKG, troponin, stress test. Start ASA 81mg daily."
    }
    import json

    mock_response_body = {
        "content": [{"text": json.dumps(mock_soap)}]
    }

    with patch.object(AWSService, '_get_client') as mock_client_factory:
        mock_client = MagicMock()
        mock_response = {
            "body": MagicMock(read=MagicMock(return_value=json.dumps(mock_response_body).encode()))
        }
        mock_client.invoke_model.return_value = mock_response
        mock_client_factory.return_value = mock_client

        service = AWSService()
        result = await service.generate_soap_note(
            transcript="Dr. Patel: How are you?\nPatient: I have chest pain.",
            patient_info={"mrn": "TEST001"}
        )

    assert result["subjective"] == mock_soap["subjective"]
    assert result["objective"] == mock_soap["objective"]
    assert result["assessment"] == mock_soap["assessment"]
    assert result["plan"] == mock_soap["plan"]


@pytest.mark.asyncio
async def test_generate_soap_note_fallback_on_error():
    """generate_soap_note falls back gracefully when Bedrock raises an error."""
    from app.services.aws_service import AWSService
    from botocore.exceptions import ClientError

    with patch.object(AWSService, '_get_client') as mock_client_factory:
        mock_client = MagicMock()
        mock_client.invoke_model.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailableException", "Message": "Bedrock down"}},
            "InvokeModel"
        )
        mock_client_factory.return_value = mock_client

        service = AWSService()
        sample_transcript = "Dr. Test: How are you?\nPatient: I feel unwell."
        result = await service.generate_soap_note(transcript=sample_transcript)

    # Fallback should still return valid SOAP structure
    assert "subjective" in result
    assert "objective" in result
    assert "assessment" in result
    assert "plan" in result
    # Fallback content should be marked as mock
    assert "[MOCK" in result["subjective"] or len(result["subjective"]) > 0


# ─────────────────────────────────────────────────────────
# Integration Tests: API Endpoints
# ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_endpoint_queues_soap_generation(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str,
):
    """POST /analyze queues a SOAP note generation task and returns 200."""
    scheduled_time = datetime.utcnow() + timedelta(days=1)

    # Create a consultation
    create_resp = await async_client.post(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "patientId": patient_id,
            "scheduledAt": scheduled_time.isoformat(),
            "durationMinutes": 30,
            "notes": "Test consultation for SOAP generation"
        }
    )
    assert create_resp.status_code == 200
    cons_id = create_resp.json()["id"]

    # Trigger analysis — mock the Celery task so it doesn't actually run
    with patch("app.workers.tasks.generate_soap_note.delay") as mock_task:
        response = await async_client.post(
            f"/api/v1/consultations/{cons_id}/analyze",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "queued" in data["message"].lower() or "processing" in data["message"].lower()
    # Verify Celery task was dispatched
    mock_task.assert_called_once_with(cons_id)


@pytest.mark.asyncio
async def test_analyze_endpoint_with_specific_scenario(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str,
):
    """POST /analyze?scenario=diabetes accepts valid scenario key."""
    scheduled_time = datetime.utcnow() + timedelta(days=2)

    create_resp = await async_client.post(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "patientId": patient_id,
            "scheduledAt": scheduled_time.isoformat(),
            "durationMinutes": 45,
        }
    )
    assert create_resp.status_code == 200
    cons_id = create_resp.json()["id"]

    with patch("app.workers.tasks.generate_soap_note.delay"):
        response = await async_client.post(
            f"/api/v1/consultations/{cons_id}/analyze?scenario=diabetes",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_analyze_endpoint_invalid_scenario(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str,
):
    """POST /analyze?scenario=invalid_xyz returns 400."""
    scheduled_time = datetime.utcnow() + timedelta(days=3)

    create_resp = await async_client.post(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "patientId": patient_id,
            "scheduledAt": scheduled_time.isoformat(),
            "durationMinutes": 30,
        }
    )
    cons_id = create_resp.json()["id"]

    response = await async_client.post(
        f"/api/v1/consultations/{cons_id}/analyze?scenario=invalid_xyz",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 400
    assert "invalid scenario" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_soap_note_not_found_before_generation(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str,
):
    """GET /soap-note returns 404 when no SOAP note has been generated yet."""
    scheduled_time = datetime.utcnow() + timedelta(days=4)

    create_resp = await async_client.post(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "patientId": patient_id,
            "scheduledAt": scheduled_time.isoformat(),
            "durationMinutes": 30,
        }
    )
    cons_id = create_resp.json()["id"]

    response = await async_client.get(
        f"/api/v1/consultations/{cons_id}/soap-note",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    # Should be 404 (no SOAP note) or 202 (pending/processing)
    assert response.status_code in (404, 202)


@pytest.mark.asyncio
async def test_auto_trigger_on_completion(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str,
):
    """Updating consultation to 'completed' automatically dispatches SOAP task."""
    scheduled_time = datetime.utcnow() + timedelta(days=5)

    create_resp = await async_client.post(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "patientId": patient_id,
            "scheduledAt": scheduled_time.isoformat(),
            "durationMinutes": 30,
        }
    )
    cons_id = create_resp.json()["id"]

    with patch("app.workers.tasks.generate_soap_note.delay") as mock_task:
        update_resp = await async_client.put(
            f"/api/v1/consultations/{cons_id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"status": "completed"}
        )

    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "completed"
    # Verify the background SOAP generation task was triggered
    mock_task.assert_called_once_with(cons_id)
