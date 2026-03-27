#!/usr/bin/env python3
"""Quick test to verify real Google Meet link generation works"""

import asyncio
from datetime import datetime, timedelta, timezone

async def test_google_meet():
    """Test if Google Meet service can create a real meeting"""
    from app.services.google_meet_service import google_meet_service
    
    print("\n" + "="*60)
    print("Testing Real Google Meet Link Generation")
    print("="*60 + "\n")
    
    # Check if credentials are available
    if not google_meet_service._available:
        print("❌ Google API services not available")
        print("   Add credentials to .env:")
        print("   - GOOGLE_CLIENT_ID")
        print("   - GOOGLE_CLIENT_SECRET")  
        print("   - GOOGLE_REFRESH_TOKEN")
        return False
    
    print("✅ Google API services available\n")
    
    # Try creating a test meeting
    try:
        test_time = datetime.now(timezone.utc) + timedelta(hours=1)
        event_id, meet_link = await google_meet_service.create_meeting(
            start_time=test_time,
            duration_minutes=30,
            summary="Test Consultation",
            description="Testing Google Meet integration",
            attendees=[]
        )
        
        print(f"✅ Meeting created successfully!")
        print(f"   Event ID: {event_id}")
        print(f"   Meet Link: {meet_link}\n")
        
        # Verify it's a real link
        if "mock" in meet_link.lower():
            print(f"❌ ERROR: Generated mock link instead of real link!")
            return False
        
        if "meet.google.com" not in meet_link:
            print(f"❌ ERROR: Invalid meet link format")
            return False
        
        print("✅ Link format is valid (real Google Meet link)\n")
        print("="*60)
        print("SUCCESS! Real Google Meet integration is working!")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create meeting: {e}\n")
        print("Ensure your .env has valid Google credentials:")
        print("  - GOOGLE_CLIENT_ID")
        print("  - GOOGLE_CLIENT_SECRET")
        print("  - GOOGLE_REFRESH_TOKEN")
        return False

if __name__ == "__main__":
    import sys
    success = asyncio.run(test_google_meet())
    sys.exit(0 if success else 1)
