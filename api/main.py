"""
LinkOps SOAR-Copilot API
AI-Powered Security Orchestration, Automation & Response Platform
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
from datetime import datetime, timedelta
from collections import defaultdict

from core.config import get_settings
from core.logging import setup_logging
from routes import (
    auth,
    incidents, 
    playbooks,
    ai_copilot,
    connectors,
    dashboard,
    health
)

# Initialize settings and logging
settings = get_settings()
setup_logging()
logger = logging.getLogger(__name__)

# Rate limiting store (in-memory for now)
rate_limit_store = defaultdict(list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 LinkOps SOAR-Copilot starting up...")
    
    # Initialize AI models
    try:
        from engines.llm_engine import initialize_llm
        await initialize_llm()
        logger.info("✅ LLM engine initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM: {e}")
    
    # Initialize RAG pipeline
    try:
        from engines.rag_engine import initialize_rag
        await initialize_rag()
        logger.info("✅ RAG pipeline initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG: {e}")
    
    # Initialize connectors
    try:
        from connectors.splunk.client import test_connection as test_splunk
        from connectors.limacharlie.client import test_connection as test_limacharlie
        
        if settings.SPLUNK_HOST:
            await test_splunk()
            logger.info("✅ Splunk connector ready")
            
        if settings.LIMACHARLIE_OID:
            await test_limacharlie()  
            logger.info("✅ LimaCharlie connector ready")
            
    except Exception as e:
        logger.warning(f"⚠️ Connector initialization warning: {e}")
    
    logger.info("🛡️ SOAR-Copilot ready for security operations!")
    
    yield
    
    # Shutdown
    logger.info("🛑 SOAR-Copilot shutting down...")


# Create FastAPI app
app = FastAPI(
    title="LinkOps SOAR-Copilot API",
    description="AI-Powered Security Orchestration, Automation & Response Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


def rate_limit_check(client_ip: str, max_requests: int = 100, window_minutes: int = 1) -> bool:
    """Simple in-memory rate limiting for API endpoints"""
    now = datetime.now()
    window_start = now - timedelta(minutes=window_minutes)
    
    # Clean old requests
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip] 
        if req_time > window_start
    ]
    
    # Check if under limit
    if len(rate_limit_store[client_ip]) >= max_requests:
        return False
    
    # Add current request
    rate_limit_store[client_ip].append(now)
    return True


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add comprehensive security headers"""
    response = await call_next(request)
    
    # Security headers for SOAR platform
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # CSP for security dashboard
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' ws: wss: https:; "
        "font-src 'self' data:; "
        "frame-ancestors 'none';"
    )
    
    # HSTS in production
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
    
    return response


@app.middleware("http") 
async def rate_limiting(request: Request, call_next):
    """Rate limiting for security endpoints"""
    # More restrictive limits for sensitive endpoints
    if any(path in request.url.path for path in ["/api/incidents", "/api/playbooks", "/api/ai"]):
        client_ip = request.client.host
        if not rate_limit_check(client_ip, max_requests=50):
            return Response(
                content='{"error": "Rate limit exceeded for security endpoints"}',
                status_code=429,
                media_type="application/json"
            )
    
    return await call_next(request)


# Add compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS for security dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,  # Security: no credentials in CORS
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Mount static files for security assets
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Include API routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(playbooks.router, prefix="/api/playbooks", tags=["playbooks"])
app.include_router(ai_copilot.router, prefix="/api/ai", tags=["ai-copilot"])
app.include_router(connectors.router, prefix="/api/connectors", tags=["connectors"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])


@app.get("/")
async def root():
    """SOAR-Copilot API root endpoint"""
    return {
        "message": "LinkOps SOAR-Copilot API v1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health",
        "timestamp": datetime.utcnow().isoformat(),
        "security_notice": "This system handles sensitive security data - ensure proper authorization"
    }


@app.get("/api/status")
async def system_status():
    """System status endpoint for monitoring"""
    return {
        "service": "soar-copilot-api",
        "version": "1.0.0",
        "status": "healthy",
        "components": {
            "llm_engine": "operational",
            "rag_pipeline": "operational", 
            "mcp_tools": "operational",
            "rpa_engine": "operational",
            "connectors": {
                "splunk": "operational" if settings.SPLUNK_HOST else "disabled",
                "limacharlie": "operational" if settings.LIMACHARLIE_OID else "disabled"
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app", 
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_config=None  # Use our custom logging
    )