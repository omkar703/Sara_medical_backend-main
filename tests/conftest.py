"""Test Configuration"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings

# Test database URL (use a separate test database)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/saramedico_dev", "/saramedico_test")

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
    """Create a test engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
    )
    
    # Initialize implementation of session factory
    TestingSessionLocal.configure(bind=engine)
    
    yield engine
    
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(engine):
    """Create a test database session"""
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
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user"""
    from app.models.user import User, Organization
    from app.core.security import hash_password, PIIEncryption
    
    # Create organization
    org = Organization(name="Test Org")
    db_session.add(org)
    await db_session.flush()
    
    # Encrypt PII
    encryption = PIIEncryption()
    encrypted_name = encryption.encrypt("Test User")
    
    # Create user
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPass123"),
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
async def async_client(client):
    """Alias for client fixture"""
    return client

@pytest_asyncio.fixture
async def doctor_token(test_user):
    """Create a valid access token for the test user"""
    from app.core.security import create_access_token
    return create_access_token(data={"sub": str(test_user.id)})

@pytest_asyncio.fixture
async def patient_id(db_session, test_user):
    """Create a test patient and return ID"""
    from app.models.patient import Patient
    from app.core.security import PIIEncryption
    from datetime import date
    import uuid
    
    encryption = PIIEncryption()
    
    patient = Patient(
        full_name=encryption.encrypt("John Doe"),
        date_of_birth=encryption.encrypt(date(1990, 1, 1).isoformat()),
        gender="male",
        phone_number=encryption.encrypt("+1234567890"),
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
