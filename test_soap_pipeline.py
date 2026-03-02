"""
Standalone test script for SOAP Note generation pipeline.
Run: python test_soap_pipeline.py

Does NOT require Docker, MinIO, or any running services.
Uses mocked AWS Bedrock so it works fully offline.
"""

import asyncio
import json
import sys
import os
from unittest.mock import MagicMock, patch

# ── Ensure project root is on the path ─────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
INFO = "\033[94mℹ\033[0m"

results = {"passed": 0, "failed": 0}

def check(name: str, condition: bool, detail: str = ""):
    if condition:
        print(f"  {PASS}  {name}")
        results["passed"] += 1
    else:
        print(f"  {FAIL}  {name}" + (f"\n       → {detail}" if detail else ""))
        results["failed"] += 1


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — MockTranscriptService
# ═══════════════════════════════════════════════════════════════════════════════
def test_mock_transcript_service():
    print("\n📄 MockTranscriptService Tests")
    print("─" * 50)

    from app.services.mock_transcript_service import mock_transcript_service, SCENARIOS

    # 1a. All 5 scenarios present
    expected = {"chest_pain", "diabetes", "pediatric_fever", "hypertension", "anxiety"}
    check("Exactly 5 scenarios registered", set(SCENARIOS.keys()) == expected)

    # 1b. Each scenario returns a non-empty transcript with speaker labels
    for key in expected:
        t = mock_transcript_service.get_mock_transcript(key)
        check(
            f"Scenario '{key}' has transcript with speaker labels",
            isinstance(t, str) and len(t) > 100 and ("Dr." in t or "Patient" in t),
            f"Length={len(t)}"
        )

    # 1c. Random selection works
    t_random = mock_transcript_service.get_mock_transcript()
    check("Random transcript is non-empty string", isinstance(t_random, str) and len(t_random) > 100)

    # 1d. Unknown scenario key falls back to a random valid transcript
    t_unknown = mock_transcript_service.get_mock_transcript("not_a_real_scenario")
    check(
        "Unknown scenario falls back gracefully",
        isinstance(t_unknown, str) and len(t_unknown) > 100
    )

    # 1e. Print sample snippet
    snippet = mock_transcript_service.get_mock_transcript("diabetes")
    print(f"\n  {INFO} Sample (diabetes, first 200 chars):")
    print(f"     {snippet[:200].strip()}...")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — AWSService.generate_soap_note (with mocked Bedrock)
# ═══════════════════════════════════════════════════════════════════════════════
async def test_soap_generation_with_mock_bedrock():
    print("\n\n🤖 AWSService SOAP Generation Tests (Mocked Bedrock)")
    print("─" * 50)

    from app.services.aws_service import AWSService

    # ── 2a. Happy path: Bedrock returns valid JSON ───────────────────────────
    mock_soap_response = {
        "subjective": (
            "Patient is a 52-year-old male presenting with 3-day history of central chest "
            "tightness radiating to the left shoulder, worse on exertion, associated with "
            "dyspnea. Family history of MI at age 58. Former smoker, quit 5 years ago."
        ),
        "objective": (
            "Vital signs: BP 148/92 mmHg, HR 78 bpm. Heart: RRR, no murmur. Lungs: CTA "
            "bilaterally. No peripheral edema. Troponin and EKG pending."
        ),
        "assessment": (
            "Exertional chest tightness with radiation to left shoulder in a patient with "
            "family history of CAD and elevated blood pressure. Differential includes stable "
            "angina vs. ACS. Hypertension confirmed."
        ),
        "plan": (
            "1. EKG stat. 2. Troponin I and BMP. 3. Lipid panel. 4. Stress test this week. "
            "5. Start ASA 81 mg daily. 6. Avoid strenuous activity pending results. "
            "7. Return to ER if pain becomes constant or severe. Follow-up in 48 hours."
        ),
    }

    mock_bedrock_body = json.dumps({
        "content": [{"text": json.dumps(mock_soap_response)}]
    }).encode()

    with patch.object(AWSService, '_get_client') as mock_factory:
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = {
            "body": MagicMock(read=MagicMock(return_value=mock_bedrock_body))
        }
        mock_factory.return_value = mock_client

        service = AWSService()
        from app.services.mock_transcript_service import mock_transcript_service
        transcript = mock_transcript_service.get_mock_transcript("chest_pain")
        soap = await service.generate_soap_note(
            transcript=transcript,
            patient_info={"mrn": "TEST001", "age": 52}
        )

    check("Returns dict", isinstance(soap, dict))
    check("Has 'subjective' key", "subjective" in soap)
    check("Has 'objective' key",  "objective" in soap)
    check("Has 'assessment' key", "assessment" in soap)
    check("Has 'plan' key",       "plan" in soap)
    check("Subjective is non-empty", len(soap.get("subjective", "")) > 10)
    check("Plan is non-empty",       len(soap.get("plan", "")) > 10)

    print(f"\n  {INFO} Generated SOAP Note:")
    for section, text in soap.items():
        print(f"\n  [{section.upper()}]")
        print(f"  {text[:180].strip()}{'...' if len(text) > 180 else ''}")

    # ── 2b. Fallback when Bedrock is unavailable ─────────────────────────────
    print("\n\n  Testing fallback (Bedrock unavailable)...")
    from botocore.exceptions import ClientError

    with patch.object(AWSService, '_get_client') as mock_factory:
        mock_client = MagicMock()
        mock_client.invoke_model.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailableException", "Message": "Service down"}},
            "InvokeModel"
        )
        mock_factory.return_value = mock_client

        service = AWSService()
        fallback_soap = await service.generate_soap_note(
            transcript="Dr. Test: How are you?\nPatient: I have a headache."
        )

    check("Fallback returns dict",                isinstance(fallback_soap, dict))
    check("Fallback has all 4 SOAP keys",
          {"subjective", "objective", "assessment", "plan"}.issubset(fallback_soap.keys()))
    check("Fallback subjective is non-empty",     len(fallback_soap.get("subjective", "")) > 5)
    check("Fallback marked as mock",
          "[MOCK" in fallback_soap.get("subjective", ""))

    print(f"\n  {INFO} Fallback SOAP Subjective:")
    print(f"  {fallback_soap['subjective'][:200]}")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Full Pipeline (transcript → Bedrock → SOAP) end-to-end
# ═══════════════════════════════════════════════════════════════════════════════
async def test_full_pipeline_all_scenarios():
    print("\n\n🔗 Full Pipeline: All 5 Scenarios × Mocked Bedrock")
    print("─" * 50)

    from app.services.aws_service import AWSService
    from app.services.mock_transcript_service import mock_transcript_service, SCENARIOS

    for scenario_key in SCENARIOS:
        # Build a plausible Bedrock response based on scenario transcript
        transcript = mock_transcript_service.get_mock_transcript(scenario_key)
        mock_soap = {
            "subjective": f"Patient presents with symptoms relevant to {scenario_key.replace('_', ' ')} scenario.",
            "objective":  "Physical examination findings and vital signs as documented.",
            "assessment": f"Clinical assessment for {scenario_key.replace('_', ' ')} scenario.",
            "plan":       "Treatment plan, medications, and follow-up as discussed.",
        }
        mock_body = json.dumps({"content": [{"text": json.dumps(mock_soap)}]}).encode()

        with patch.object(AWSService, '_get_client') as mock_factory:
            mock_client = MagicMock()
            mock_client.invoke_model.return_value = {
                "body": MagicMock(read=MagicMock(return_value=mock_body))
            }
            mock_factory.return_value = mock_client

            service = AWSService()
            soap = await service.generate_soap_note(transcript=transcript)

        check(
            f"Scenario '{scenario_key}': full pipeline produces SOAP with 4 keys",
            isinstance(soap, dict) and
            {"subjective", "objective", "assessment", "plan"}.issubset(soap.keys())
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════════════
async def main():
    print("=" * 60)
    print("  SOAP Note Pipeline — Standalone Test Runner")
    print("=" * 60)

    test_mock_transcript_service()
    await test_soap_generation_with_mock_bedrock()
    await test_full_pipeline_all_scenarios()

    print("\n" + "=" * 60)
    total = results["passed"] + results["failed"]
    print(f"  Results: {results['passed']}/{total} tests passed", end="  ")
    if results["failed"] == 0:
        print("\033[92m— All tests passed! 🎉\033[0m")
    else:
        print(f"\033[91m— {results['failed']} test(s) failed.\033[0m")
    print("=" * 60)

    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
