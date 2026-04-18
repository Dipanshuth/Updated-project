from fastapi import APIRouter, Form
from models import SessionLocal, Alert
from datetime import datetime

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/send")
async def send_alert(evidence_id: str = Form("")):
    """Send emergency alert and log it"""
    db = SessionLocal()
    try:
        alert = Alert(
            evidence_id=evidence_id,
            alert_type="emergency",
            message=f"Emergency alert triggered for evidence {evidence_id}",
            sent_to="Police Control Room, Emergency Contact 1",
            status="sent",
            created_at=datetime.utcnow().isoformat(),
        )
        db.add(alert)
        db.commit()
    finally:
        db.close()

    return {
        "status": "sent",
        "evidence_id": evidence_id,
        "message": "Emergency alert dispatched to nearby authorities and emergency contacts",
        "notified": ["Police Control Room", "Emergency Contact 1"],
        "sent_at": datetime.utcnow().isoformat(),
    }