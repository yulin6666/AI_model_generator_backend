"""
IDM-VTON Backend API
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import vton_router

settings = get_settings()

app = FastAPI(
    title="IDM-VTON API",
    description="High-quality virtual try-on API powered by IDM-VTON (ECCV2024)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vton_router.router)


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "IDM-VTON API",
        "version": "1.0.0",
        "status": "ok",
        "description": "High-quality virtual try-on using IDM-VTON (ECCV2024)",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "info": "/api/vton/info",
            "try_on": "/api/vton/try-on",
            "try_on_upload": "/api/vton/try-on/upload",
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "replicate_configured": bool(settings.replicate_api_token),
        "model": "IDM-VTON",
    }
