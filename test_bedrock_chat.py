"""
AWS Bedrock Chat Tester
Tests if AWS Bedrock (Claude) is reachable using the project's AWSService.

Run: python test_bedrock_chat.py

You will need AWS credentials in your .env:
    AWS_ACCESS_KEY_ID=AKIAxxxxx
    AWS_SECRET_ACCESS_KEY=xxxxx
    AWS_REGION=us-east-1           (optional, defaults to us-east-1)
"""

import asyncio
import os
import sys

# ── Load .env before importing anything from the project ───────────────────
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Colour helpers ──────────────────────────────────────────────────────────
def green(t):  return f"\033[92m{t}\033[0m"
def red(t):    return f"\033[91m{t}\033[0m"
def cyan(t):   return f"\033[96m{t}\033[0m"
def yellow(t): return f"\033[93m{t}\033[0m"
def bold(t):   return f"\033[1m{t}\033[0m"

# ── Check credentials before going further ──────────────────────────────────
def check_credentials():
    key    = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    region = os.getenv("AWS_REGION", "us-east-1")

    print(bold("\n🔑  AWS Credential Check"))
    print("─" * 45)

    if not key or key.startswith("AKIAxxx") or key == "":
        print(red("  ✗ AWS_ACCESS_KEY_ID  → NOT SET"))
        print(red("  ✗ AWS_SECRET_ACCESS_KEY  → NOT SET"))
        print(yellow("\n  ⚠  Add your AWS credentials to .env:"))
        print(yellow("     AWS_ACCESS_KEY_ID=AKIAxxxxx"))
        print(yellow("     AWS_SECRET_ACCESS_KEY=your_secret"))
        print(yellow("     AWS_REGION=us-east-1\n"))
        sys.exit(1)

    masked_key = key[:6] + "..." + key[-4:]
    print(green(f"  ✓ AWS_ACCESS_KEY_ID     = {masked_key}"))
    print(green(f"  ✓ AWS_SECRET_ACCESS_KEY = ****"))
    print(green(f"  ✓ AWS_REGION            = {region}"))
    return region


# ── Test 1: Simple text generation (generate_text) ──────────────────────────
async def test_simple_text(service):
    print(bold("\n\n📝  Test 1: Simple Text Generation"))
    print("─" * 45)
    prompt = "In one sentence, what is a SOAP note in medical documentation?"

    print(f"  Prompt: {cyan(prompt)}")
    print("  Calling aws_service.generate_text() ...", end=" ", flush=True)

    try:
        response = await service.generate_text(prompt)
        if response and len(response) > 10:
            print(green("✅ SUCCESS"))
            print(f"\n  Response:\n  {response.strip()}")
            return True
        else:
            print(red("❌ EMPTY RESPONSE"))
            return False
    except Exception as e:
        print(red(f"❌ ERROR"))
        print(red(f"  {e}"))
        return False


# ── Test 2: SOAP note from a transcript (generate_soap_note) ────────────────
async def test_soap_note(service):
    print(bold("\n\n🩺  Test 2: SOAP Note Generation from Transcript"))
    print("─" * 45)

    from app.services.mock_transcript_service import mock_transcript_service

    # Use the diabetes scenario for a clean, well-structured test
    scenario = "diabetes"
    transcript = mock_transcript_service.get_mock_transcript(scenario)

    print(f"  Scenario : {cyan(scenario)}")
    print(f"  Transcript length: {len(transcript)} chars")
    print("  Calling aws_service.generate_soap_note() ...", end=" ", flush=True)

    try:
        soap = await service.generate_soap_note(
            transcript=transcript,
            patient_info={"mrn": "BEDROCK-TEST", "scenario": scenario}
        )

        if "[MOCK" in soap.get("subjective", ""):
            print(yellow("⚠  FALLBACK (Bedrock unreachable — mock SOAP returned)"))
            print(yellow("  ↳ Check credentials and model access in AWS Console"))
        else:
            print(green("✅ SUCCESS — Real Bedrock response"))

        print("\n  ── SOAP Note ──────────────────────────────────")
        for section in ["subjective", "objective", "assessment", "plan"]:
            text = soap.get(section, "(missing)")
            print(f"\n  {bold(section.upper())}:")
            # Word-wrap at ~80 chars for readability
            words = text.split()
            line = "  "
            for word in words:
                if len(line) + len(word) > 82:
                    print(line)
                    line = "    " + word + " "
                else:
                    line += word + " "
            if line.strip():
                print(line)

        return "[MOCK" not in soap.get("subjective", "")

    except Exception as e:
        print(red(f"❌ ERROR"))
        print(red(f"  {e}"))
        return False


# ── Test 3: Interactive chat (generate_chat_stream) ─────────────────────────
async def test_chat_stream(service):
    print(bold("\n\n💬  Test 3: Streaming Chat"))
    print("─" * 45)

    messages = [
        {"role": "user", "content": "What are the four sections of a SOAP note?"}
    ]
    context = "You are assisting a medical team using the Sara Medical platform."

    print(f"  User: {cyan(messages[0]['content'])}")
    print("  Claude: ", end="", flush=True)

    full_response = ""
    try:
        async for chunk in service.generate_chat_stream(messages, context):
            print(chunk, end="", flush=True)
            full_response += chunk

        print()  # newline after stream ends

        if full_response and len(full_response) > 20:
            print(green("\n  ✅ Stream completed successfully"))
            return True
        else:
            print(yellow("\n  ⚠  Very short or empty response"))
            return False

    except Exception as e:
        print()
        print(red(f"  ❌ ERROR: {e}"))
        return False


# ── Main ─────────────────────────────────────────────────────────────────────
async def main():
    print("=" * 50)
    print(bold("  AWS Bedrock Connectivity Test"))
    print(bold("  Using: app.services.aws_service.AWSService"))
    print("=" * 50)

    region = check_credentials()

    # Import AFTER env is loaded
    from app.services.aws_service import AWSService
    service = AWSService()

    print(f"\n  Model  : anthropic.claude-3-sonnet-20240229-v1:0")
    print(f"  Region : {region}")

    results = {}
    results["Simple Text"]   = await test_simple_text(service)
    results["SOAP Note"]     = await test_soap_note(service)
    results["Chat Stream"]   = await test_chat_stream(service)

    # Summary
    print("\n\n" + "=" * 50)
    print(bold("  Results Summary"))
    print("─" * 50)
    for test_name, passed in results.items():
        status = green("PASS ✅") if passed else red("FAIL ❌")
        print(f"  {test_name:<20} {status}")

    all_passed = all(results.values())
    print("─" * 50)
    if all_passed:
        print(green("  ✅ Bedrock is working correctly!\n"))
    else:
        print(yellow("  ⚠  Some tests failed — check credentials and model access.\n"))
        print(yellow("  Ensure claude-3-sonnet is enabled in your AWS Bedrock console:"))
        print(yellow("  → https://console.aws.amazon.com/bedrock/home#/model-access\n"))

    print("=" * 50)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
