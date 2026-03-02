"""Test Configuration"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings

# Test database URL (reuse dev db for standalone testing)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("saramedico_dev", "saramedico_test")

# Create test engine
# Create test session factory
TestingSessionLocal = async_sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest_asyncio.fixture
async def engine():
    """Create a test engine and patch the global database engine"""
    from app import database
    import asyncpg

    # Derive the dev DB URL (where we have permission to CREATE DATABASE)
    dev_db_url = settings.DATABASE_URL
    # asyncpg needs the connection string without the driver prefix
    asyncpg_url = dev_db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Create the test database if it doesn't exist
    conn = await asyncpg.connect(asyncpg_url)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'saramedico_test'"
        )
        if not exists:
            await conn.execute("CREATE DATABASE saramedico_test")
    finally:
        await conn.close()

    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Enable pgvector extension in test DB
    async with test_engine.connect() as conn:
        await conn.execute(__import__('sqlalchemy').text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.commit()
    
    # Patch global engine and session factory
    old_engine = database.engine
    old_session_local = database.AsyncSessionLocal
    
    database.engine = test_engine
    database.AsyncSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Initialize implementation of session factory in conftest
    TestingSessionLocal.configure(bind=test_engine)
    
    yield test_engine
    
    await test_engine.dispose()
    
    # Restore (though mostly relevant for multi-session tests)
    database.engine = old_engine
    database.AsyncSessionLocal = old_session_local

@pytest_asyncio.fixture
async def db_session(engine):
    """Create a test database session"""
    from app.database import Base
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    """Create a test client"""
    from app.main import app
    from app.database import get_db
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Use the app lifespan
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def doctor_user(db_session):
    """Create a test doctor user"""
    from app.models.user import User, Organization
    from app.core.security import hash_password, PIIEncryption
    
    # Create organization
    org = Organization(name="Doctor Org")
    db_session.add(org)
    await db_session.flush()
    
    # Encrypt PII
    encryption = PIIEncryption()
    encrypted_name = encryption.encrypt("Doctor User")
    
    # Create user
    user = User(
        email="doctor@example.com",
        password_hash=hash_password("DoctorPass123"),
        role="doctor",
        organization_id=org.id,
        full_name=encrypted_name,
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user

@pytest_asyncio.fixture
async def test_user(doctor_user):
    """Alias for doctor_user"""
    return doctor_user

@pytest_asyncio.fixture
async def patient_user(db_session):
    """Create a test patient user"""
    from app.models.user import User, Organization
    from app.core.security import hash_password, PIIEncryption
    
    # Create organization (reuse or new)
    org = Organization(name="Patient Org")
    db_session.add(org)
    await db_session.flush()
    
    # Encrypt PII
    encryption = PIIEncryption()
    encrypted_name = encryption.encrypt("Patient User")
    
    # Create user
    user = User(
        email="patient@example.com",
        password_hash=hash_password("PatientPass123"),
        role="patient",
        organization_id=org.id,
        full_name=encrypted_name,
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user

@pytest_asyncio.fixture
async def async_client(client):
    """Alias for client fixture"""
    return client

@pytest_asyncio.fixture
async def test_client(client):
    """Alias for client fixture"""
    return client

@pytest_asyncio.fixture
async def doctor_token(doctor_user):
    """Create a valid access token for the doctor user"""
    from app.core.security import create_access_token
    return create_access_token(data={"sub": str(doctor_user.id), "role": "doctor"})

@pytest_asyncio.fixture
async def patient_token(patient_user):
    """Create a valid access token for the patient user"""
    from app.core.security import create_access_token
    return create_access_token(data={"sub": str(patient_user.id), "role": "patient"})

@pytest_asyncio.fixture
async def patient_id(db_session, test_user, patient_user):
    """Create a test patient and return ID (linked to patient_user)"""
    from app.models.patient import Patient
    from app.core.security import PIIEncryption
    from datetime import date
    import uuid
    
    encryption = PIIEncryption()
    
    # Use patient_user.id for the Patient record to satisfy foreign key constraints 
    # and maintain consistency between User and Patient models
    patient = Patient(
        id=patient_user.id,
        full_name=encryption.encrypt("John Doe"),
        date_of_birth=encryption.encrypt(date(1990, 1, 1).isoformat()),
        gender="male",
        phone_number=encryption.encrypt("+16502531111"),
        mrn=f"ORG-{uuid.uuid4().hex[:6].upper()}",
        organization_id=test_user.organization_id,
        created_by=test_user.id
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    
    return str(patient.id)


@pytest_asyncio.fixture
async def admin_user(db_session, test_user):
    """Create a test admin user in the same org"""
    from app.models.user import User
    from app.core.security import hash_password, PIIEncryption
    
    encryption = PIIEncryption()
    encrypted_name = encryption.encrypt("Admin User")
    
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("AdminPass123"),
        role="admin",
        organization_id=test_user.organization_id,
        full_name=encrypted_name,
        email_verified=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    return admin


@pytest_asyncio.fixture
async def admin_token(admin_user):
    """Create a valid access token for the admin user"""
    from app.core.security import create_access_token
    return create_access_token(data={"sub": str(admin_user.id)})
