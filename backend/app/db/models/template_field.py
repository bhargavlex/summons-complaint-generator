"""
Template Field Model
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class TemplateField(Base):
    __tablename__ = "template_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    field_key = Column(String(100), nullable=False, comment="e.g., plaintiff_name")
    placeholder = Column(String(100), nullable=False, comment="e.g., «Plaintiff_name_»")
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    expected_format = Column(String(255), nullable=True)
    is_required = Column(Boolean, default=True)
    field_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Unique constraint: one field_key per template
    __table_args__ = (
        UniqueConstraint('template_id', 'field_key', name='unique_template_field'),
    )
    
    # Relationships
    template = relationship("Template", back_populates="fields")
    field_values = relationship("FieldValue", back_populates="template_field")
