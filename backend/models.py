"""
AI Digital Memory Vault — Database Models
SQLite with SQLAlchemy ORM
"""

from sqlalchemy import create_engine, Column, String, Integer, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database — single file, zero setup
DATABASE_URL = "sqlite:///./memory_vault.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Evidence(Base):
    """Evidence record model"""
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evidence_id = Column(String(50), unique=True, index=True, nullable=False)
    filename = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    file_type = Column(String(100))
    sha256_hash = Column(String(64))
    description = Column(Text, default="")
    incident_datetime = Column(String(50), default="")
    location = Column(String(500), default="")
    latitude = Column(String(20), default="")
    longitude = Column(String(20), default="")
    status = Column(String(20), default="pending")  # pending, processing, analyzed, error
    distress_detected = Column(Integer, default=0)  # 0 or 1
    confidence = Column(Float, default=0.0)
    ai_summary = Column(Text, default="")
    created_at = Column(String(50))


class User(Base):
    """User profile model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255))
    phone = Column(String(20))
    emergency_contact = Column(String(20))
    created_at = Column(String(50))


class Alert(Base):
    """Alert/notification model"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evidence_id = Column(String(50))
    alert_type = Column(String(50))  # emergency, notification, status
    message = Column(Text)
    sent_to = Column(String(500))
    status = Column(String(20), default="pending")  # pending, sent, failed
    created_at = Column(String(50))
