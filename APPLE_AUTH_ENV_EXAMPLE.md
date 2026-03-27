# =====================================================
# APPLE SIGN IN CONFIGURATION EXAMPLE
# =====================================================
# This file shows how to configure Apple Sign In for your application.
# Copy these variables to your .env file with actual values.

# Apple Developer Team ID
# Find at: https://developer.apple.com/account/#!/membership/
APPLE_TEAM_ID=XXXXXXXXXX

# Apple Sign In Service ID (the identifier created for this app)
# Created in: https://developer.apple.com/account/resources/identifiers/list
APPLE_CLIENT_ID=com.yourcompany.yourapp.service

# Apple Private Key ID
# Created in: https://developer.apple.com/account/resources/authkeys/list
APPLE_KEY_ID=YYYYYYYYYY

# Apple Private Key (from .p8 file)
# IMPORTANT: Replace actual newlines with \n (literal backslash-n)
# Downloaded from Apple Developer console
# Format: -----BEGIN PRIVATE KEY-----\n...content...\n-----END PRIVATE KEY-----
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgbJbX...\n-----END PRIVATE KEY-----

# Apple Redirect URI
# Must match exactly what's configured in Apple Developer console
# Local development:
APPLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/apple/callback

# Production:
# APPLE_REDIRECT_URI=https://api.yourdomain.com/api/v1/auth/apple/callback


# =====================================================
# HOW TO GET THESE VALUES:
# =====================================================

# 1. APPLE_TEAM_ID:
#    - Go to https://developer.apple.com/account/
#    - Click "Membership"
#    - Find "Team ID" (10 characters)

# 2. APPLE_CLIENT_ID:
#    - Go to https://developer.apple.com/account/resources/identifiers/list
#    - Create a new Service ID
#    - Use the Bundle ID/Identifier (e.g., com.saramedico.web.service)

# 3. APPLE_KEY_ID:
#    - Go to https://developer.apple.com/account/resources/authkeys/list
#    - Create a new key or find existing one
#    - Key ID is shown next to the key name (10 characters)

# 4. APPLE_PRIVATE_KEY:
#    - Download the .p8 file from Apple Developer console
#    - Open the file in a text editor
#    - Copy the entire content
#    - Replace newlines with literal \n:
#      * Find: actual newline character
#      * Replace with: \n (backslash + n)
#    - Or use this Python snippet:
#      with open('key.p8', 'r') as f:
#          key = f.read().replace('\n', '\\n')
#          print(key)

# =====================================================
# EXAMPLE .env ENTRY:
# =====================================================

# Development Setup
APPLE_TEAM_ID=ABCD123456
APPLE_CLIENT_ID=com.saramedico.web.service
APPLE_KEY_ID=EFGH789012
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgQ7PvDhVmAV7tQ9vU\nBb8zzMEVhKSCGxg91fvYmIZ6PvKhRANCAARJdHjdKCVKpWO7uxSXKnFrQXwlnFRb\nIhI5L0z8dWpKlVjZUBLRoXPvk8Sl8hZXtRWaQKhUdqe6KDMhPK9bGkRq\n-----END PRIVATE KEY-----
APPLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/apple/callback

# =====================================================
# TESTING THE CONFIGURATION:
# =====================================================

# 1. Start the backend:
#    docker-compose up -d
#    or: python -m uvicorn app.main:app --reload

# 2. Test the login endpoint:
#    curl -X GET http://localhost:8000/api/v1/auth/apple/login

# 3. Should redirect to: https://appleid.apple.com/auth/authorize?...

# 4. Test in browser:
#    - Paste the login URL in browser
#    - Should redirect to Apple's OAuth page
#    - Complete sign-in flow
#    - Should redirect back to APPLE_REDIRECT_URI

# =====================================================
# SECURITY NOTES:
# =====================================================

# - NEVER commit APPLE_PRIVATE_KEY to git/version control
# - Use .env files that are .gitignored
# - In production, use environment secrets management
# - Rotate keys periodically (yearly recommended)
# - Keep Apple Developer credentials secure
# - Use HTTPS in production (required by Apple)
# - Monitor redirect URI usage
