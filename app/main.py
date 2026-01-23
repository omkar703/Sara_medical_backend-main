"""Main FastAPI Application"""

from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import close_db, init_db


async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Saramedico Backend...")
    print(f"📦 Environment: {settings.APP_ENV}")
    print(f"🔧 Debug Mode: {settings.APP_DEBUG}")
    
    # Database initialization temporarily disabled for debugging
    # Will be re-enabled once DB auth is fixed
    if settings.APP_ENV == "development":
        await init_db()
        print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Saramedico Backend...")
    await close_db()
    print("✅ Database connections closed")



# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="HIPAA-Compliant Medical AI SaaS Platform Backend",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from app.api.v1 import api_router
app.include_router(api_router, prefix="/api/v1")


# Health Check Endpoints
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Overall health check endpoint.
    Returns the status of all critical services.
    """
    from app.utils.health import check_all_services
    
    return await check_all_services()


@app.get("/health/database", tags=["Health"])
async def health_check_database() -> Dict[str, str]:
    """Database connectivity check"""
    from app.utils.health import check_database
    
    return await check_database()


@app.get("/health/redis", tags=["Health"])
async def health_check_redis() -> Dict[str, str]:
    """Redis connectivity check"""
    from app.utils.health import check_redis
    
    return await check_redis()


@app.get("/health/minio", tags=["Health"])
async def health_check_minio() -> Dict[str, str]:
    """MinIO connectivity check"""
    from app.utils.health import check_minio
    
    return await check_minio()


@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    if settings.APP_DEBUG:
        # In debug mode, show full error
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "traceback": traceback.format_exc()
            }
        )
    else:
        # In production, hide error details
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred"
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.APP_DEBUG,
        workers=1 if settings.APP_DEBUG else settings.API_WORKERS,
    )
