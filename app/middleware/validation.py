
from fastapi import Request, UploadFile, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class ValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Content-Type Check for POST/PUT
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type:
                 # Some requests might not have body, but let's be strict for /api/v1/ai
                 if request.url.path.startswith("/api/v1/doctor/ai"):
                     return JSONResponse(status_code=400, content={"detail": "Content-Type header missing"})
            
            # 2. Content-Length Check (Prevents oversized payloads early)
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10 MB limit
                return JSONResponse(status_code=413, content={"detail": "Request entity too large"})
        
        # 2. Size validation (Basic) can be done here or in Nginx. 
        # Python middleware reading body for size is tricky as it consumes the stream.
        # We'll rely on Starlette/FastAPI limits or specific file upload endpoints checks.
        
        response = await call_next(request)
        return response
