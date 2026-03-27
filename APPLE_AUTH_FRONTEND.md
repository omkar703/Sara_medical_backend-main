# Apple Auth Frontend Integration Guide

This guide provides frontend code examples for integrating Apple Sign In with your React/Next.js application.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Setup](#setup)
3. [Implementation Examples](#implementation-examples)
4. [React Hook Usage](#react-hook-usage)
5. [Next.js Integration](#nextjs-integration)
6. [Error Handling](#error-handling)
7. [Token Management](#token-management)

---

## Prerequisites

- React 16.8+ or Next.js 12+
- Frontend domain registered with Apple
- Backend Apple Auth endpoints configured
- Environment variables set

---

## Setup

### 1. Environment Variables

Create `.env.local`:

```env
# Apple Auth (same as backend APPLE_CLIENT_ID)
REACT_APP_APPLE_CLIENT_ID=com.yourcompany.app.service

# Backend API
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
REACT_APP_FRONTEND_URL=http://localhost:3000
```

### 2. Install Dependencies

```bash
npm install
# No additional packages needed - Apple SDK is loaded from CDN
```

### 3. Add Apple SDK to HTML

Add this to your `public/index.html` or layout:

```html
<!DOCTYPE html>
<html>
  <head>
    <!-- ... other head content ... -->
    <script
      type="text/javascript"
      src="https://appleid.cdn-apple.com/js/appleid.js"
      defer
    ></script>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
```

---

## Implementation Examples

### 1. Apple Sign In Button Component

```jsx
// components/AppleSignInButton.jsx

import React, { useEffect } from 'react';
import styles from './AppleSignInButton.module.css';

export function AppleSignInButton() {
  useEffect(() => {
    // Initialize Apple Sign In
    if (window.AppleID) {
      window.AppleID.auth.init({
        clientId: process.env.REACT_APP_APPLE_CLIENT_ID,
        teamId: process.env.REACT_APP_APPLE_TEAM_ID,
        keyId: process.env.REACT_APP_APPLE_KEY_ID,
        redirectUri: `${window.location.origin}/auth/apple/callback`,
        scope: 'email name',
        usePopup: true,
      });
    }
  }, []);

  const handleAppleSignIn = async () => {
    try {
      // Redirect to backend Apple login endpoint
      window.location.href = `${process.env.REACT_APP_API_BASE_URL}/auth/apple/login`;
    } catch (error) {
      console.error('Apple Sign In error:', error);
    }
  };

  return (
    <button
      onClick={handleAppleSignIn}
      className={styles.appleSignInButton}
      aria-label="Sign in with Apple"
    >
      <svg className={styles.appleIcon} viewBox="0 0 24 24">
        {/* Apple logo SVG */}
      </svg>
      <span>Sign in with Apple</span>
    </button>
  );
}

// Or use the native Apple button:
export function AppleSignInButtonNative() {
  return (
    <div
      id="appleid-signin"
      data-type="sign-in"
      data-mode="black"
      data-locale="en_US"
      data-size="200"
      data-theme="black"
      data-border="true"
      data-border-radius="12"
      data-scale="1.2"
    />
  );
}
```

### 2. Callback Handler Component

```jsx
// pages/auth/apple/callback.jsx

import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';

export function AppleAuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { setAuthTokens, setUser } = useAuth();

  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');
    const userStr = searchParams.get('user');
    const error = searchParams.get('error');

    if (error) {
      console.error('Apple Auth Error:', decodeURIComponent(error));
      navigate('/login', { state: { error: decodeURIComponent(error) } });
      return;
    }

    if (accessToken && refreshToken) {
      try {
        // Store tokens
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        
        // Parse and store user info
        if (userStr) {
          const user = JSON.parse(decodeURIComponent(userStr));
          localStorage.setItem('user', JSON.stringify(user));
          setUser(user);
        }

        // Update auth context
        setAuthTokens(accessToken, refreshToken);

        // Redirect to dashboard
        navigate('/dashboard');
      } catch (err) {
        console.error('Failed to process Apple auth callback:', err);
        navigate('/login', { state: { error: 'Authentication failed' } });
      }
    } else {
      // Missing tokens
      navigate('/login', { state: { error: 'Authentication failed' } });
    }
  }, [searchParams, navigate, setAuthTokens, setUser]);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div>
        <p>Processing Apple Sign In...</p>
        <div className="spinner">
          {/* Loading spinner */}
        </div>
      </div>
    </div>
  );
}
```

### 3. CSS for Apple Button

```css
/* AppleSignInButton.module.css */

.appleSignInButton {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  background-color: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
  min-width: 200px;
}

.appleSignInButton:hover {
  background-color: #1a1a1a;
}

.appleSignInButton:active {
  background-color: #333;
}

.appleIcon {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.appleSignInButton:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

## React Hook Usage

### useAuth Hook

```jsx
// hooks/useAuth.js

import { useContext, useCallback } from 'react';
import { AuthContext } from '../context/AuthContext';

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  const {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    login,
    logout,
    setAuthTokens,
    setUser,
    refreshAccessToken,
  } = context;

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    login,
    logout,
    setAuthTokens,
    setUser,
    refreshAccessToken,
  };
}
```

### AuthContext Provider

```jsx
// context/AuthContext.jsx

import React, { createContext, useState, useCallback, useEffect } from 'react';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [refreshToken, setRefreshToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Initialize from localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user');
    const storedRefreshToken = localStorage.getItem('refresh_token');

    if (storedToken && storedUser) {
      setAccessToken(storedToken);
      setRefreshToken(storedRefreshToken);
      setUser(JSON.parse(storedUser));
      setIsAuthenticated(true);
    }
  }, []);

  const setAuthTokens = useCallback((access, refresh) => {
    setAccessToken(access);
    setRefreshToken(refresh);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  const refreshAccessToken = useCallback(async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_BASE_URL}/auth/refresh`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAuthTokens(data.access_token, refreshToken);
        return true;
      } else {
        logout();
        return false;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      return false;
    }
  }, [refreshToken, setAuthTokens, logout]);

  const value = {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    setAuthTokens,
    setUser,
    logout,
    refreshAccessToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
```

---

## Next.js Integration

### Next.js App Router

```typescript
// app/auth/apple/callback/page.tsx

'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function AppleAuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');
    const userStr = searchParams.get('user');
    const error = searchParams.get('error');

    if (error) {
      router.push(`/login?error=${encodeURIComponent(error)}`);
      return;
    }

    if (accessToken && refreshToken) {
      // Store in cookies or localStorage
      document.cookie = `accessToken=${accessToken}; path=/`;
      document.cookie = `refreshToken=${refreshToken}; path=/`;

      if (userStr) {
        const user = JSON.parse(decodeURIComponent(userStr));
        localStorage.setItem('user', JSON.stringify(user));
      }

      // Redirect to dashboard
      router.push('/dashboard');
    } else {
      router.push('/login?error=Authentication failed');
    }
  }, [searchParams, router]);

  return (
    <div className="flex justify-center items-center h-screen">
      <p>Processing Apple Sign In...</p>
    </div>
  );
}
```

### API Route for Token Refresh

```typescript
// app/api/auth/refresh/route.ts

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { refresh_token } = body;

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/refresh`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token }),
      }
    );

    if (!response.ok) {
      return NextResponse.json({ error: 'Token refresh failed' }, { status: 401 });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
```

---

## Error Handling

```jsx
// components/AppleSignInWithErrorHandling.jsx

import React, { useState } from 'react';

export function AppleSignInWithErrorHandling() {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSignIn = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Redirect to backend Apple login
      window.location.href = `${process.env.REACT_APP_API_BASE_URL}/auth/apple/login`;
    } catch (err) {
      setError('Failed to initiate Apple Sign In');
      console.error('Sign in error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}
      <button
        onClick={handleSignIn}
        disabled={isLoading}
        aria-busy={isLoading}
      >
        {isLoading ? 'Signing in...' : 'Sign in with Apple'}
      </button>
    </div>
  );
}
```

---

## Token Management

### API Interceptor

```javascript
// utils/apiClient.js

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

export async function apiCall(endpoint, options = {}) {
  let token = localStorage.getItem('access_token');

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // If 401, try to refresh token
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');

    if (refreshToken) {
      const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (refreshResponse.ok) {
        const { access_token } = await refreshResponse.json();
        localStorage.setItem('access_token', access_token);
        token = access_token;

        // Retry original request
        headers['Authorization'] = `Bearer ${token}`;
        response = await fetch(`${API_BASE_URL}${endpoint}`, {
          ...options,
          headers,
        });
      }
    }
  }

  return response;
}
```

---

## Testing

### Unit Test Example

```javascript
// __tests__/AppleSignInButton.test.js

import { render, screen, fireEvent } from '@testing-library/react';
import { AppleSignInButton } from '../components/AppleSignInButton';

describe('AppleSignInButton', () => {
  beforeEach(() => {
    // Mock environment variables
    process.env.REACT_APP_APPLE_CLIENT_ID = 'test-client-id';
    process.env.REACT_APP_API_BASE_URL = 'http://localhost:8000/api/v1';
  });

  test('renders button', () => {
    render(<AppleSignInButton />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  test('redirects to Apple login on click', () => {
    const { location } = window;
    delete window.location;
    window.location = { href: '' };

    render(<AppleSignInButton />);
    fireEvent.click(screen.getByRole('button'));

    expect(window.location.href).toContain('/auth/apple/login');

    window.location = location;
  });
});
```

---

## Security Best Practices

1. **HTTPS Only**: Use HTTPS in production
2. **Secure Storage**: Store tokens in httpOnly cookies when possible
3. **CORS**: Whitelist your frontend domain in CORS settings
4. **Token Refresh**: Implement automatic token refresh before expiry
5. **Logout**: Clear all auth data on logout
6. **Error Messages**: Don't expose sensitive error details to users

---

## Troubleshooting

### "Apple Auth not configured"
- Verify `REACT_APP_APPLE_CLIENT_ID` is set
- Check backend environment variables

### "Invalid redirect URI"
- Verify frontend URL matches backend configuration
- Check protocol (http vs https)

### Tokens not appearing in URL
- Check browser console for errors
- Verify callback route is correct
- Check CORS configuration

### Blank page at callback
- Verify callback route exists
- Check for JavaScript errors in console
- Verify token parsing logic

---

## Resources

- [Apple Sign In Documentation](https://developer.apple.com/sign-in-with-apple/)
- [React Documentation](https://react.dev)
- [Next.js Documentation](https://nextjs.org)
- [MDN - localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)
- [JWT Introduction](https://jwt.io/introduction)

---

## Support

For backend integration issues, see `APPLE_AUTH_SETUP.md`
For API documentation, see `APPLE_AUTH_QUICK_REF.md`
For implementation details, see `APPLE_AUTH_IMPLEMENTATION.md`
