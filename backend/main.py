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

from models import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="AI Digital Memory Vault",
    description="API for civilian evidence upload, AI analysis, and FIR generation",
    version="1.0.0",
)

# CORS — Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
        ]
    }

# ==================== FRONTEND STATIC FILES ====================
# IMPORTANT: This must come LAST — after all API routes are registered
# Otherwise it shadows the API endpoints
import os
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)