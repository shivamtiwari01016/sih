from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class NotificationType(str, enum.Enum):
    OVERDUE = "Overdue"
    DEADLINE_APPROACHING = "Deadline Approaching"
    OVERLAP_SUGGESTION = "Overlap Suggestion"
    TRANSFER_REQUEST = "Transfer Request"
    COORDINATION_REQUEST = "Coordination Request"
    ASSIGNMENT = "Assignment"
    STATUS_CHANGE = "Status Change"
    ESCALATION = "Escalation"


class Severity(str, enum.Enum):
    INFO = "Info"
    WARNING = "Warning"
    CRITICAL = "Critical"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=True)
    notification_type = Column(Enum(NotificationType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(Enum(Severity), default=Severity.INFO)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    recipient = relationship("User", back_populates="notifications")
    complaint = relationship("Complaint", back_populates="notifications")
