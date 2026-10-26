from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class FeedbackVerdict(str, enum.Enum):
    CONFIRM = "confirm"
    DISMISS = "dismiss"
    LINK = "link"


class OverlapFeedback(Base):
    __tablename__ = "overlap_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    overlap_id = Column(UUID(as_uuid=True), ForeignKey("related_cases.id"), nullable=False, index=True)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    verdict = Column(Enum(FeedbackVerdict), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    related_case = relationship("RelatedCase")
    officer = relationship("User")
