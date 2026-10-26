from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class CoordinationDecision(Base):
    __tablename__ = "coordination_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    related_case_id = Column(UUID(as_uuid=True), ForeignKey("related_cases.id"), nullable=False, index=True)
    decision_text = Column(Text, nullable=False)
    lead_bureau_id = Column(UUID(as_uuid=True), ForeignKey("bureaus.id"), nullable=True)
    pause_until = Column(Date, nullable=True)
    decided_by = Column(Text, nullable=True)  # JSON-encoded array of officer IDs who signed/agreed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    related_case = relationship("RelatedCase")
    lead_bureau = relationship("Bureau")
