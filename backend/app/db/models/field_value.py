"""
Field Value Model - Stores extracted and manual values
"""
from sqlalchemy import Column, Integer, Text, ForeignKey, Boolean, DateTime, String, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class FieldValueStatus(str, enum.Enum):
    PENDING = "pending"
    EXTRACTED = "extracted"
    MANUAL = "manual"
    CONFIRMED = "confirmed"


class FieldValue(Base):
    __tablename__ = "field_values"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    template_field_id = Column(Integer, ForeignKey("template_fields.id", ondelete="RESTRICT"), nullable=False)
    extracted_value = Column(Text, nullable=True, comment="Value from LLM")
    manual_value = Column(Text, nullable=True, comment="User override")
    source_document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, comment="Which document it came from")
    source_page_number = Column(Integer, nullable=True, comment="Page number in document")
    extraction_confidence = Column(String(10), nullable=True, comment="LLM confidence score")
    is_missing = Column(Boolean, default=True)
    status = Column(Enum(FieldValueStatus), default=FieldValueStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Unique constraint: one value per field per session
    __table_args__ = (
        UniqueConstraint('session_id', 'template_field_id', name='unique_session_field'),
    )
    
    # Relationships
    session = relationship("Session", back_populates="field_values")
    template_field = relationship("TemplateField", back_populates="field_values")
    source_document = relationship("Document", back_populates="field_values")
    
    @property
    def final_value(self):
        """Returns manual_value if set, otherwise extracted_value"""
        return self.manual_value if self.manual_value else self.extracted_value
