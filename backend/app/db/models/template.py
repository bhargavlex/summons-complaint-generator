"""
Template Model
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Template(Base):
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    law_firm_id = Column(Integer, ForeignKey("law_firms.id", ondelete="RESTRICT"), nullable=False)
    case_type_id = Column(Integer, ForeignKey("case_types.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, comment="Path to DOCX template file")
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Unique constraint: one active template per firm+case_type combination
    __table_args__ = (
        UniqueConstraint('law_firm_id', 'case_type_id', 'version', name='unique_firm_case_version'),
    )
    
    # Relationships
    law_firm = relationship("LawFirm", back_populates="templates")
    case_type = relationship("CaseType", back_populates="templates")
    fields = relationship("TemplateField", back_populates="template", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="template")
