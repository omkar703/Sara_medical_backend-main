#!/usr/bin/env python3
"""
Verify Google Meet Credentials Setup
=====================================

This script checks if your Google Meet credentials are properly configured
and attempts to create a test meeting.

Usage:
    python3 verify_google_meet.py
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone

async def main():
    print("\n" + "="*60)
    print("🔍 GOOGLE MEET CREDENTIALS VERIFICATION")
    print("="*60 + "\n")
    
    # Step 1: Check environment variables
    print("[1/3] Checking environment variables...")
    from app.config import settings
    
    has_client_id = bool(settings.GOOGLE_CLIENT_ID)
    has_client_secret = bool(settings.GOOGLE_CLIENT_SECRET)
    has_refresh_token = bool(settings.GOOGLE_REFRESH_TOKEN)
    
    print(f"  ✓ GOOGLE_CLIENT_ID: {'SET' if has_client_id else '❌ NOT SET'}")
    print(f"  ✓ GOOGLE_CLIENT_SECRET: {'SET' if has_client_secret else '❌ NOT SET'}")
    print(f"  ✓ GOOGLE_REFRESH_TOKEN: {'SET' if has_refresh_token else '❌ NOT SET'}")
    
    if not all([has_client_id, has_client_secret, has_refresh_token]):
        print("\n❌ FAILED: Missing Google credentials in .env file")
        print("\nSetup instructions: See GOOGLE_MEET_SETUP.md")
        return False
    
    # Step 2: Check Google API availability
    print("\n[2/3] Checking Google API services...")
    from app.services.google_meet_service import google_meet_service
    
    if not google_meet_service._available:
        print("  ❌ Google API services unavailable")
        print("     This usually means credentials are invalid or misconfigured")
        print("\nTroubleshooting:")
        print("  - Check that refresh token is valid (not expired)")
        print("  - Verify Google Calendar API is enabled in Cloud Console")
        print("  - Ensure credentials haven't been regenerated")
        return False
    
    print("  ✓ Google API services initialized successfully")
    print("  ✓ Calendar service: Available")
    print("  ✓ Drive service: Available")
    
    # Step 3: Test creating a meeting
    print("\n[3/3] Creating test meeting...")
    try:
        test_time = datetime.now(timezone.utc) + timedelta(hours=1)
        event_id, meet_link = await google_meet_service.create_meeting(
            start_time=test_time,
            duration_minutes=30,
            summary="Saramedico: Google Meet Verification Test",
            description="This is a test meeting to verify Google Meet integration",
            attendees=[]
        )
        
        print(f"  ✓ Test meeting created successfully!")
        print(f"    Event ID: {event_id}")
        print(f"    Meet Link: {meet_link}")
        
        # Verify it's a real link
        if "mock" in meet_link.lower():
            print(f"\n  ⚠️  WARNING: Generated link appears to be a mock link!")
            print(f"     Expected real link format: https://meet.google.com/xxx-yyyy-zzz")
            print(f"     Got: {meet_link}")
            return False
        
        if "meet.google.com" not in meet_link:
            print(f"\n  ❌ Invalid meet link format: {meet_link}")
            return False
        
        print(f"\n✅ SUCCESS! Google Meet is properly configured!")
        print(f"\nYou can now:")
        print(f"  - Schedule consultations and get real Google Meet links")
        print(f"  - Doctor and patient will receive calendar invites")
        print(f"  - Meetings can be recorded and transcribed")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED to create test meeting")
        print(f"   Error: {e}")
        print(f"\nPossible causes:")
        print(f"  - Refresh token is expired")
        print(f"  - Google Calendar API is not enabled")
        print(f"  - Account doesn't have proper permissions")
        print(f"\nTo fix:")
        print(f"  1. Check your Google Cloud Console")
        print(f"  2. Verify Google Calendar API is enabled")
        print(f"  3. Generate a new refresh token")
        print(f"  4. Update .env file")
        print(f"  5. Restart the backend")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print("\n" + "="*60 + "\n")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        print("\nMake sure you:")
        print("  1. Have app dependencies installed (google-auth-oauthlib, google-api-python-client)")
        print("  2. Have a .env file in the project root")
        print("  3. Have Google credentials configured")
        sys.exit(1)
