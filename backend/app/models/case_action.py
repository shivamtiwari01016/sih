from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from app.models.complaint import ComplaintStatus


class CaseAction(Base):
    __tablename__ = "case_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=False)
    action_type = Column(String, nullable=False)
    previous_status = Column(Enum(ComplaintStatus), nullable=True)
    new_status = Column(Enum(ComplaintStatus), nullable=True)
    remarks = Column(Text, nullable=False)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bureau_id = Column(UUID(as_uuid=True), ForeignKey("bureaus.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    supporting_document_reference = Column(String, nullable=True)
    prev_hash = Column(String, nullable=True)
    hash = Column(String, nullable=True)

    complaint = relationship("Complaint", back_populates="actions")
    officer = relationship("User", back_populates="actions")
    bureau = relationship("Bureau", back_populates="actions")
