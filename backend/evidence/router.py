import os
import hashlib
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from models import SessionLocal, Evidence

router = APIRouter(tags=["Evidence"])

@router.post("/upload-evidence")
async def upload_evidence(
    file: UploadFile = File(...),
    gps_data: str = Form(""),
    timestamp: str = Form(""),
    device_id: str = Form(""),
):
    """
    Accepts audio file, GPS data, timestamp, and device ID. 
    Stores securely (local storage) and tracks in DB.
    """
    evidence_id = f"EVD-{str(uuid.uuid4())[:8].upper()}"
    os.makedirs("uploads", exist_ok=True)
    
    file_path = os.path.join("uploads", f"{evidence_id}_{file.filename}")
    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    file_hash = hashlib.sha256(content).hexdigest()

    db = SessionLocal()
    try:
        # Parsing GPS if available (e.g. "28.6139, 77.2090")
        lat = ""
        lng = ""
        if gps_data and "," in gps_data:
            lat, lng = [part.strip() for part in gps_data.split(",", 1)]

        evidence = Evidence(
            evidence_id=evidence_id,
            filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            file_type=file.content_type or "audio/unknown",
            sha256_hash=file_hash,
            description=f"Automated upload from device {device_id}",
            incident_datetime=timestamp or datetime.utcnow().isoformat(),
            location=gps_data,
            latitude=lat,
            longitude=lng,
            status="pending",
            created_at=datetime.utcnow().isoformat(),
        )
        db.add(evidence)
        db.commit()
    finally:
        db.close()

    return {
        "status": "success",
        "evidence_id": evidence_id,
        "hash": file_hash,
        "message": "Evidence uploaded securely."
    }

@router.get("/verify-integrity")
async def verify_integrity(evidence_id: str):
    """
    Checks the tamper-evident storage for the hash.
    Generates SHA-256 hash or returns existing securely stored one.
    """
    db = SessionLocal()
    try:
        record = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        # Verify if file still exists and hash matches
        verification_status = "intact"
        if os.path.exists(record.file_path):
            with open(record.file_path, "rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
                if current_hash != record.sha256_hash:
                    verification_status = "tampered"
        else:
            verification_status = "file_missing"

        return {
            "evidence_id": evidence_id,
            "stored_hash": record.sha256_hash,
            "verification_status": verification_status,
            "algorithm": "SHA-256",
            "message": f"Integrity check: {verification_status}"
        }
    finally:
        db.close()
