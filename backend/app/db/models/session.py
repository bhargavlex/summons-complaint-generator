"""
Processing Session Model
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class SessionStatus(str, enum.Enum):
    CREATED = "created"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    EXTRACTING = "extracting"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), nullable=False, unique=True, index=True, comment="UUID for API reference")
    template_id = Column(Integer, ForeignKey("templates.id", ondelete="RESTRICT"), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.CREATED, nullable=False)
    created_by = Column(String(255), nullable=True, comment="Lexvia user identifier")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    template = relationship("Template", back_populates="sessions")
    documents = relationship("Document", back_populates="session", cascade="all, delete-orphan")
    field_values = relationship("FieldValue", back_populates="session", cascade="all, delete-orphan")
    plaintiffs = relationship("Plaintiff", back_populates="session", cascade="all, delete-orphan")
    defendants = relationship("Defendant", back_populates="session", cascade="all, delete-orphan")
