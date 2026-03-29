import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User

class OnboardingRequiredException(Exception):
    """Exception raised when a user must complete onboarding."""
    pass

# Security scheme for JWT bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session
    
    Returns:
        Current user object
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from payload
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )
    
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User)
        .options(selectinload(User.organization))
        .where(User.id == user_uuid, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


async def get_user_optional(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """Get the current user or None if not authenticated"""
    if not credentials:
        return None
        
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (email verified)
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current user if email is verified
    
    Raises:
        HTTPException: If email is not verified
    """
    from app.config import settings
    # Bypass email verification in development
    if not current_user.email_verified and settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first.",
        )
    return current_user


from fastapi import Request

async def require_active_account(
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to require an active account.
    Blocks requests if user is still pending onboarding,
    unless the route starts with /api/v1/auth/onboarding/.
    """
    if current_user.account_status == "pending_onboarding":
        if not request.url.path.startswith("/api/v1/auth/onboarding/"):
            raise OnboardingRequiredException()
    return current_user


async def require_onboarding_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to require an onboarding token.
    Enforces token type 'onboarding' and correct scopes.
    """
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token type
    if payload.get("type") != "onboarding":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected onboarding token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Verify scopes
    scopes = payload.get("scopes", [])
    if "onboarding:write" not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing required scope: onboarding:write",
        )
    
    # Get user ID from payload
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )
    
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User)
        .options(selectinload(User.organization))
        .where(User.id == user_uuid, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


def require_role(required_role):
    """
    Dependency factory to require specific user role(s)
    
    Args:
        required_role: Required role as a string ('doctor') or list of roles (['doctor', 'hospital', 'admin'])
    
    Returns:
        Dependency function that checks role
    """
    # Normalize to a list for uniform handling
    allowed_roles = [required_role] if isinstance(required_role, str) else list(required_role)

    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # Normalize role to string for comparison
        user_role_str = str(current_user.role).split('.')[-1] if hasattr(current_user.role, 'value') else str(current_user.role)
        
        if user_role_str not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires one of: {', '.join(allowed_roles)}",
            )
        return current_user
    
    return role_checker


def require_any_role(*allowed_roles: str):
    """
    Dependency factory to require any of the specified roles
    
    Args:
        allowed_roles: Tuple of allowed roles (e.g., "doctor", "admin", "hospital")
    
    Returns:
        Dependency function that checks if user has any of the allowed roles
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # Normalize role to string for comparison
        user_role_str = str(current_user.role).split('.')[-1] if hasattr(current_user.role, 'value') else str(current_user.role)
        
        if user_role_str not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires one of: {', '.join(allowed_roles)}",
            )
        return current_user
    
    return role_checker


# Pre-defined role dependencies
require_doctor = require_role("doctor")
require_admin = require_role("admin")
require_patient = require_role("patient")


async def get_current_active_user_ws(token: str, db: AsyncSession = None) -> User:
    """
    Get current user from token string (for WebSockets)
    Note: Requires manual DB session management if not dependency injected
    """
    from app.database import AsyncSessionLocal
    from types import SimpleNamespace # Added to make TokenPayload work as a simple object
    
    # Create a new session if not provided
    close_session = False
    if not db:
        db = AsyncSessionLocal()
        close_session = True
        
    try:
        payload = decode_token(token)
        if not payload:
            return None
            
        # Get user ID from payload and convert to UUID object
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
            
        try:
            user_uuid = UUID(user_id_str)
        except (ValueError, TypeError):
            return None
        
        user_result = await db.execute(select(User).where(User.id == user_uuid))
        user = user_result.scalar_one_or_none()
        
        # Check if user exists and is not soft-deleted
        if not user or user.deleted_at is not None:
            return None
            
        return user
    except Exception:
        return None
    finally:
        if close_session:
            await db.close()


def get_organization_id(current_user: User = Depends(get_current_active_user)) -> UUID:
    """
    Get the organization ID of the current user
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Organization UUID
    """
    return current_user.organization_id
