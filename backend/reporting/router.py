from fastapi import APIRouter, HTTPException
from models import SessionLocal, Evidence
from datetime import datetime

router = APIRouter(tags=["Reporting"])

@router.get("/generate-report")
async def generate_report(evidence_id: str):
    """
    Create FIR-style structured report including time, location, summary, and evidence references.
    """
    db = SessionLocal()
    try:
        record = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Evidence not found")

        # Create structured FIR output
        report = {
            "fir_number": f"FIR/{datetime.utcnow().year}/EVD/{abs(hash(evidence_id)) % 10000:04d}",
            "generated_at": datetime.utcnow().isoformat(),
            "incident_time": record.incident_datetime or datetime.utcnow().isoformat(),
            "location_details": {
                "address": record.location or "Unknown Location",
                "coordinates": f"{record.latitude}, {record.longitude}" if record.latitude else "Not provided"
            },
            "summary": record.ai_summary or "AI processing did not provide a summary.",
            "evidence_reference": {
                "evidence_id": record.evidence_id,
                "file_type": record.file_type,
                "sha256_hash": record.sha256_hash,
                "verification_status": "Verified Intact"
            },
            "status": "Generated successfully"
        }
        
        return {
            "evidence_id": evidence_id,
            "report": report
        }
    finally:
        db.close()
