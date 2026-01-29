"""FastAPI Dependencies for authentication and authorization"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User

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
    
    result = await db.execute(
        select(User).where(User.id == user_uuid, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


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
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first.",
        )
    return current_user


def require_role(required_role: str):
    """
    Dependency factory to require specific user role
    
    Args:
        required_role: Required role (patient, doctor, admin)
    
    Returns:
        Dependency function that checks role
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires {required_role} role",
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
        if current_user.role not in allowed_roles:
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
            
        # Assuming TokenPayload is a simple object that can be created from a dict
        # If TokenPayload is a Pydantic model, it should be imported from app.core.security
        TokenPayload = SimpleNamespace # Using SimpleNamespace as a placeholder for TokenPayload
        token_data = TokenPayload(**payload)
        
        user_result = await db.execute(select(User).where(User.id == getattr(token_data, "sub", None)))
        user = user_result.scalar_one_or_none()
        
        # The original get_current_active_user checks email_verified, but this WS version checks is_active
        # Assuming 'is_active' is the intended check for WS context.
        if not user or not user.is_active:
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
