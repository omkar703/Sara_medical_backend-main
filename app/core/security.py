"""Security utilities for authentication and encryption"""

import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.config import settings


# ==========================================
# Password Hashing
# ==========================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


# ==========================================
# JWT Token Management
# ==========================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration
    
    Args:
        data: Payload data to encode in the token
    
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string to decode
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# ==========================================
# Application-Level Encryption (PII)
# ==========================================

class PIIEncryption:
    """Encrypt/decrypt PII fields using Fernet (AES-256)"""
    
    def __init__(self):
        # Initialize Fernet with key from settings
        self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string"""
        if not plaintext:
            return plaintext
        encrypted = self.fernet.encrypt(plaintext.encode('utf-8'))
        return encrypted.decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext string"""
        if not ciphertext:
            return ciphertext
        decrypted = self.fernet.decrypt(ciphertext.encode('utf-8'))
        return decrypted.decode('utf-8')


# Global instance
pii_encryption = PIIEncryption()


# ==========================================
# Token Generation
# ==========================================

def generate_random_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def generate_verification_token() -> str:
    """Generate an email verification token"""
    return generate_random_token(32)


def generate_password_reset_token() -> str:
    """Generate a password reset token"""
    return generate_random_token(32)


# ==========================================
# Token Hashing (for refresh tokens)
# ==========================================

import hashlib

# ... (keep imports)

# ... (keep existing code until hash_token)

# ==========================================
# Token Hashing (for refresh tokens)
# ==========================================

def hash_token(token: str) -> str:
    """Hash a token for storage (refresh tokens) using SHA-256"""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def verify_token_hash(token: str, token_hash: str) -> bool:
    """Verify a token against its hash"""
    return secrets.compare_digest(hash_token(token), token_hash)
