from fastapi import APIRouter, Form
from models import SessionLocal, User
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/setup")
async def auth_setup(
    name: str = Form(""),
    phone: str = Form(""),
    emergency_contact: str = Form(""),
):
    """Save user profile and emergency contacts to DB"""
    db = SessionLocal()
    try:
        user = User(
            name=name,
            phone=phone,
            emergency_contact=emergency_contact,
            created_at=datetime.utcnow().isoformat(),
        )
        db.add(user)
        db.commit()
    finally:
        db.close()

    return {
        "status": "success",
        "message": "User profile saved",
        "user": {
            "name": name,
            "phone": phone,
            "emergency_contact": emergency_contact,
        },
    }