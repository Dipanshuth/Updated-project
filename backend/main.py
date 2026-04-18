"""
AI Digital Memory Vault — FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import os
import sys

# Ensure backend directory is on sys.path so relative imports always work
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from models import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

# Create uploads directory
os.makedirs(os.path.join(BACKEND_DIR, "uploads"), exist_ok=True)

app = FastAPI(
    title="AI Digital Memory Vault",
    description="API for civilian evidence upload, AI analysis, and FIR generation",
    version="1.0.0",
)

# CORS — Allow frontend to connect (from any origin, including file:// and localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
uploads_path = os.path.join(BACKEND_DIR, "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

# Import route modules
from routes import auth, evidence, alerts

# New Modular Pipeline Routers
from detection.router import router as detection_router
from evidence.router import router as new_evidence_router
from inference.router import router as inference_router
from reporting.router import router as reporting_router

# Include routers — MUST be before frontend static mount
app.include_router(auth.router)
app.include_router(evidence.router)
app.include_router(alerts.router)

# Include New AI Pipeline Routers
app.include_router(detection_router)
app.include_router(new_evidence_router)
app.include_router(inference_router)
app.include_router(reporting_router)

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health():
    return {
        "service": "AI Digital Memory Vault API",
        "version": "1.0.0",
        "status": "active",
    }

@app.get("/api")
async def api_info():
    return {
        "endpoints": [
            "POST /auth/setup",
            "POST /evidence/upload",
            "POST /evidence/{id}/analyze",
            "GET  /evidence/{id}/timeline",
            "GET  /evidence/{id}/report",
            "POST /evidence/{id}/hash",
            "GET  /evidence/list",
            "POST /alerts/send",
            "POST /detect-trigger",
            "POST /detect-trigger-audio",
            "POST /upload-evidence",
            "POST /run-inference",
            "GET  /generate-timeline",
            "GET  /generate-report",
            "GET  /verify-integrity",
        ]
    }

# ==================== FRONTEND STATIC FILES ====================
# IMPORTANT: This must come LAST — after all API routes are registered
# Otherwise it shadows the API endpoints
frontend_path = os.path.normpath(os.path.join(BACKEND_DIR, "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    print("\n" + "=" * 60)
    print("  AI Digital Memory Vault -- Backend Server")
    print("=" * 60)
    print(f"  Backend dir:  {BACKEND_DIR}")
    print(f"  Frontend dir: {frontend_path}")
    print(f"  Database:     {os.path.join(BACKEND_DIR, 'memory_vault.db')}")
    print(f"  Uploads dir:  {uploads_path}")
    print("=" * 60)
    print("  [OK] Server is ready!")
    print("  URL: http://localhost:8000")
    print("  API docs: http://localhost:8000/docs")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)