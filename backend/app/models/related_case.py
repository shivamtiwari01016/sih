from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class RelationshipType(str, enum.Enum):
    POTENTIAL_DUPLICATE = "Potential Duplicate"
    RELATED_MATTER = "Related Matter"
    SHARED_INSTITUTION = "Shared Institution"
    CROSS_BUREAU_COORDINATION = "Cross-Bureau Coordination"


class ReviewStatus(str, enum.Enum):
    SUGGESTED = "Suggested"
    ACKNOWLEDGED = "Acknowledged"
    COORDINATING = "Coordinating"
    CONFIRMED_RELATED = "Confirmed Related"
    DECIDED = "Decided"
    REJECTED = "Rejected"
    REQUIRES_FURTHER_REVIEW = "Requires Further Review"


class RelatedCase(Base):
    __tablename__ = "related_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id_1 = Column(UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=False)
    complaint_id_2 = Column(UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=False)
    relationship_type = Column(Enum(RelationshipType), nullable=False)
    similarity_score = Column(Float, nullable=True)
    matching_reasons = Column(Text, nullable=True)  # JSON string
    review_status = Column(Enum(ReviewStatus), default=ReviewStatus.SUGGESTED)
    lead_bureau_id = Column(UUID(as_uuid=True), ForeignKey("bureaus.id"), nullable=True)
    lead_bureau_code = Column(String, nullable=True)
    ack_due_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    complaint_1 = relationship("Complaint", back_populates="related_as_1", foreign_keys=[complaint_id_1])
    complaint_2 = relationship("Complaint", back_populates="related_as_2", foreign_keys=[complaint_id_2])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    lead_bureau = relationship("Bureau", foreign_keys=[lead_bureau_id])
    messages = relationship("CoordinationMessage", cascade="all, delete-orphan", order_by="CoordinationMessage.created_at.asc()")
    decisions = relationship("CoordinationDecision", cascade="all, delete-orphan", order_by="CoordinationDecision.created_at.desc()")
    feedback = relationship("OverlapFeedback", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('complaint_id_1', 'complaint_id_2', name='uq_complaint_pair'),
    )
