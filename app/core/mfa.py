"""Multi-Factor Authentication (MFA) utilities"""

import io
from typing import Tuple

import pyotp
import qrcode
from qrcode.image.pil import PilImage

from app.config import settings


def generate_totp_secret() -> str:
    """
    Generate a new TOTP secret for MFA
    
    Returns:
        Base32-encoded secret string
    """
    return pyotp.random_base32(length=settings.TOTP_SECRET_LENGTH)


def generate_qr_code(secret: str, user_email: str) -> str:
    """
    Generate a QR code image for TOTP setup
    
    Args:
        secret: The TOTP secret
        user_email: User's email for the TOTP label
    
    Returns:
        Base64-encoded PNG image data (data:image... format)
    """
    # Create TOTP URI
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=user_email,
        issuer_name=settings.MFA_ISSUER_NAME
    )
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 data URI
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    import base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"


def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verify a TOTP code against the secret
    
    Args:
        secret: The TOTP secret
        code: The 6-digit code to verify
    
    Returns:
        True if valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # Allow 1 step tolerance


def generate_backup_codes(count: int = 10) -> list[str]:
    """
    Generate backup codes for MFA recovery
    
    Args:
        count: Number of backup codes to generate
    
    Returns:
        List of backup code strings
    """
    import secrets
    return [
        f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}"
        for _ in range(count)
    ]
