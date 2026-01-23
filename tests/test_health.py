"""Test Health Check Endpoints"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test overall health check"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]
    assert "minio" in data["services"]


@pytest.mark.asyncio
async def test_health_check_database(client: AsyncClient):
    """Test database health check"""
    response = await client.get("/health/database")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "connected"
    assert data.get("service") == "PostgreSQL"


@pytest.mark.asyncio
async def test_health_check_redis(client: AsyncClient):
    """Test Redis health check"""
    response = await client.get("/health/redis")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "connected"
    assert data.get("service") == "Redis"


@pytest.mark.asyncio
async def test_health_check_minio(client: AsyncClient):
    """Test MinIO health check"""
    response = await client.get("/health/minio")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "connected"
    assert data.get("service") == "MinIO"
