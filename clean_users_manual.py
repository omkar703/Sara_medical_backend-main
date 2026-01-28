
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import dotenv_values

async def clean_users():
    # Helper to get env vars without depending on app logic
    config = dotenv_values("backend/.env")
    
    # Construct DB URL manually for local connection
    # Assuming standard defaults if not in file, but they are in file.
    db_user = config.get("DATABASE_USER", "saramedico_user")
    db_pass = config.get("DATABASE_PASSWORD", "SaraMed1c0_Dev_2024!Secure")
    db_host = "127.0.0.1"
    db_port = "5435" # Mapped port
    db_name = config.get("DATABASE_NAME", "saramedico_dev")
    
    db_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    print(f"Connecting to {db_url.replace(db_pass, '***')}")
    
    engine = create_async_engine(db_url, echo=False)
    
    emails = [
        "audit_admin@saramedico.com",
        "audit_doctor@saramedico.com", 
        "audit_patient@saramedico.com"
    ]
    
    async with engine.begin() as conn:
        print("Cleaning up audit users...")
        for email in emails:
            # Get User ID
            result = await conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email}
            )
            user_id = result.scalar()
            
            if user_id:
                print(f"  Deleting dependencies for {email} ({user_id})...")
                # Delete dependencies
                # Data Access Grants
                await conn.execute(
                    text("DELETE FROM data_access_grants WHERE patient_id = :uid OR doctor_id = :uid"),
                    {"uid": user_id}
                )
                # Consultations
                await conn.execute(
                    text("DELETE FROM consultations WHERE patient_id = :uid OR doctor_id = :uid"),
                    {"uid": user_id}
                )
                # Appointments
                await conn.execute(
                    text("DELETE FROM appointments WHERE patient_id = :uid OR doctor_id = :uid"),
                    {"uid": user_id}
                )
                # AI Processing Queue
                await conn.execute(
                    text("DELETE FROM ai_processing_queue WHERE patient_id = :uid OR doctor_id = :uid"),
                    {"uid": user_id}
                )
                # Chat History
                await conn.execute(
                    text("DELETE FROM chat_history WHERE patient_id = :uid OR doctor_id = :uid"),
                    {"uid": user_id}
                )
                # Tasks
                await conn.execute(
                    text("DELETE FROM tasks WHERE doctor_id = :uid"),
                    {"uid": user_id}
                )
                # Activity Logs
                await conn.execute(
                    text("DELETE FROM activity_logs WHERE user_id = :uid"),
                    {"uid": user_id}
                )
                # Chunks (via Documents)
                await conn.execute(
                    text("DELETE FROM chunks WHERE patient_id = :uid OR document_id IN (SELECT id FROM documents WHERE uploaded_by = :uid)"),
                    {"uid": user_id}
                )
                # Documents
                await conn.execute(
                    text("DELETE FROM documents WHERE patient_id = :uid OR uploaded_by = :uid"),
                    {"uid": user_id}
                )
                # Audit Logs
                await conn.execute(
                    text("DELETE FROM audit_logs WHERE user_id = :uid"),
                    {"uid": user_id}
                )
                # Refresh Tokens
                await conn.execute(
                    text("DELETE FROM refresh_tokens WHERE user_id = :uid"),
                    {"uid": user_id}
                )
                # Patient Profile (if exists)
                await conn.execute(
                    text("DELETE FROM patients WHERE id = :uid"),
                    {"uid": user_id}
                )
                # Finally User
                await conn.execute(
                    text("DELETE FROM users WHERE id = :uid"),
                    {"uid": user_id}
                )
                print(f"  Deleted user {email}")
            else:
                print(f"  User {email} not found.")
        print("✅ Cleanup complete.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clean_users())
