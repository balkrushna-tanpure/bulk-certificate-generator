from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.v1.router import api_router
import app.models # Ensure all models are registered

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables if they don't exist
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Scalable Bulk Certificate Generation API with background processing, resilient batch handling, and PDF export.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for external client applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)

from pathlib import Path
from fastapi.responses import FileResponse, HTMLResponse

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"

@app.get("/", tags=["Dashboard"], response_class=HTMLResponse)
def dashboard():
    """Serves the interactive web interface."""
    if STATIC_INDEX.exists():
        return FileResponse(str(STATIC_INDEX), media_type="text/html")
    return HTMLResponse("<h1>Bulk Certificate Generator API is online. Visit <a href='/docs'>/docs</a>.</h1>")

@app.get("/api", tags=["Root"])
def api_info():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "api_v1_endpoints": {
            "submit_job": "POST /api/v1/jobs",
            "list_jobs": "GET /api/v1/jobs",
            "get_job_status": "GET /api/v1/jobs/{job_id}",
            "download_job_zip": "GET /api/v1/jobs/{job_id}/download",
            "list_certificates": "GET /api/v1/certificates",
            "get_certificate": "GET /api/v1/certificates/{certificate_id}",
            "download_certificate": "GET /api/v1/certificates/{certificate_id}/download",
            "verify_certificate": "GET /api/v1/certificates/verify/{certificate_code}",
        }
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
