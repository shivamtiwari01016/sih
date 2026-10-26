from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class IntentType(str, enum.Enum):
    NOTICE = "Notice"
    INSPECTION = "Inspection"
    HEARING = "Hearing"
    PENALTY = "Penalty"
    CLOSURE = "Closure"
    TRANSFER = "Transfer"


class IntentStatus(str, enum.Enum):
    PROPOSED = "Proposed"
    AGREED = "Agreed"
    OBJECTED = "Objected"
    WITHDRAWN = "Withdrawn"
    EXECUTED = "Executed"


class ActionIntent(Base):
    __tablename__ = "action_intents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=False, index=True)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=False, index=True)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bureau_id = Column(UUID(as_uuid=True), ForeignKey("bureaus.id"), nullable=True)
    intent_type = Column(Enum(IntentType), nullable=False)
    planned_date = Column(Date, nullable=False)
    status = Column(Enum(IntentStatus), default=IntentStatus.PROPOSED)
    conflicts_json = Column(Text, nullable=True)  # JSON-encoded string describing detected conflicts
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    complaint = relationship("Complaint", back_populates="intents")
    institution = relationship("Institution", back_populates="action_intents")
    officer = relationship("User")
    bureau = relationship("Bureau")
