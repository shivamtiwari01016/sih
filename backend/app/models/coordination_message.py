from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class CoordinationMessage(Base):
    __tablename__ = "coordination_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    related_case_id = Column(UUID(as_uuid=True), ForeignKey("related_cases.id"), nullable=False, index=True)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    mentions = Column(Text, nullable=True)  # JSON-encoded array of mentioned user IDs or roles
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    related_case = relationship("RelatedCase")
    officer = relationship("User")
