"""Email service for sending verification and notification emails"""

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from jinja2 import Template

from app.config import settings


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send an email using SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (optional)
    
    Returns:
        True if email sent successfully
    """
    # Create message
    message = MIMEMultipart("alternative")
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = to_email
    message["Subject"] = subject
    
    # Add text and HTML parts
    if text_content:
        part1 = MIMEText(text_content, "plain")
        message.attach(part1)
    
    part2 = MIMEText(html_content, "html")
    message.attach(part2)
    
    try:
        # Send email
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=settings.SMTP_TLS,
            start_tls=settings.SMTP_SSL,
        )
        return True
    except Exception as e:
        # Log error in production
        print(f"Failed to send email to {to_email}: {str(e)}")
        return False


async def send_verification_email(to_email: str, verification_token: str, user_name: str) -> bool:
    """
    Send email verification email
"""
    from typing import Optional
        
    verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={verification_token}"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #4F46E5; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; background-color: #f9fafb; }
            .button { display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }
            .footer { padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to Saramedico!</h1>
            </div>
            <div class="content">
                <h2>Hello {{ user_name }},</h2>
                <p>Thank you for registering with Saramedico. Please verify your email address to activate your account.</p>
                <p><a href="{{ verification_url }}" class="button">Verify Email Address</a></p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{{ verification_url }}</p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't create an account with us, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 Saramedico. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_content = template.render(
        user_name=user_name,
        verification_url=verification_url
    )
    
    return await send_email(
        to_email=to_email,
        subject="Verify Your Email - Saramedico",
        html_content=html_content,
        text_content=f"Please verify your email by visiting: {verification_url}"
    )


async def send_password_reset_email(to_email: str, reset_token: str, user_name: str) -> bool:
    """
    Send password reset email
    """
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #DC2626; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; background-color: #f9fafb; }
            .button { display: inline-block; padding: 12px 24px; background-color: #DC2626; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }
            .footer { padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }
            .warning { background-color: #FEF3C7; padding: 15px; border-left: 4px solid: #F59E0B; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <h2>Hello {{ user_name }},</h2>
                <p>We received a request to reset your password for your Saramedico account.</p>
                <p><a href="{{ reset_url }}" class="button">Reset Password</a></p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{{ reset_url }}</p>
                <div class="warning">
                    <p><strong>Security Notice:</strong></p>
                    <p>This link will expire in 1 hour for your security.</p>
                    <p>If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
                </div>
            </div>
            <div class="footer">
                <p>&copy; 2026 Saramedico. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_content = template.render(
        user_name=user_name,
        reset_url=reset_url
    )
    
    return await send_email(
        to_email=to_email,
        subject="Password Reset Request - Saramedico",
        html_content=html_content,
        text_content=f"Reset your password by visiting: {reset_url}"
    )


async def send_invitation_email(email: str, token: str, role: str, org_name: str) -> bool:
    """
    Send team invitation email
    """
    invite_url = f"{settings.FRONTEND_URL}/auth/invite?token={token}"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #10B981; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; background-color: #f9fafb; }
            .button { display: inline-block; padding: 12px 24px; background-color: #10B981; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }
            .footer { padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Team Invitation</h1>
            </div>
            <div class="content">
                <h2>Hello,</h2>
                <p>You have been invited to join the <strong>{{ org_name }}</strong> team on Saramedico as a <strong>{{ role }}</strong>.</p>
                <p>Click the button below to accept the invitation and set up your account.</p>
                <p><a href="{{ invite_url }}" class="button">Accept Invitation</a></p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{{ invite_url }}</p>
                <p>This invitation will expire in 48 hours.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 Saramedico. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_content = template.render(
        org_name=org_name,
        role=role,
        invite_url=invite_url
    )
    
    return await send_email(
        to_email=email,
        subject=f"Invitation to join {org_name} on Saramedico",
        html_content=html_content,
        text_content=f"You have been invited to join {org_name}. Accept here: {invite_url}"
    )

async def send_doctor_credentials_email(
    to_email: str, 
    name: str, 
    password: str, 
    department: str, 
    role: str, 
    org_name: str
) -> bool:
    """
    Send an email containing login credentials to a doctor 
    created directly by a hospital administrator.
    """
    login_url = f"{settings.FRONTEND_URL}/auth/login"
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2563EB; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9fafb; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #2563EB; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .credentials {{ background-color: #E5E7EB; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 16px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to {org_name}</h1>
            </div>
            <div class="content">
                <h2>Hello Dr. {name},</h2>
                <p>An account has been created for you at <strong>{org_name}</strong> under the <strong>{department}</strong> department as <strong>{role}</strong>.</p>
                <p>You can access the Saramedico platform using the following credentials:</p>
                
                <div class="credentials">
                    <p style="margin: 0;"><strong>Email:</strong> {to_email}</p>
                    <p style="margin: 0;"><strong>Password:</strong> {password}</p>
                </div>
                
                <p><em>For your security, we strongly advise you to change your password immediately after logging in.</em></p>
                <p><a href="{login_url}" class="button">Log In to Your Account</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(
        to_email=to_email,
        subject=f"Your Saramedico Account Credentials for {org_name}",
        html_content=html_template,
        text_content=f"Your account was created. Email: {to_email}, Password: {password}. Please login at {login_url}"
    )