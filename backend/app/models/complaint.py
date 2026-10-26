from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class ComplaintStatus(str, enum.Enum):
    RECEIVED = "Received"
    UNDER_SCRUTINY = "Under Scrutiny"
    UNDER_PROCESS = "Under Process"
    AWAITING_INFORMATION = "Awaiting Information"
    TRANSFERRED = "Transferred"
    ESCALATED = "Escalated"
    DISPOSED = "Disposed"
    CLOSED = "Closed"


class Priority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class Sensitivity(str, enum.Enum):
    NORMAL = "Normal"
    SENSITIVE = "Sensitive"
    WHISTLEBLOWER = "Whistleblower"
    RAGGING = "Ragging"
    HARASSMENT = "Harassment"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_number = Column(String, unique=True, nullable=False, index=True)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=False, index=True)
    received_date = Column(Date, nullable=False)
    source_channel = Column(String, nullable=True)
    complainant_reference = Column(String, nullable=True)
    complainant_pseudo_id = Column(String, nullable=True, index=True)
    complainant_encrypted = Column(Text, nullable=True)
    category = Column(String, nullable=False, index=True)
    subcategory = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    language = Column(String, default="en")
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    sensitivity = Column(Enum(Sensitivity), default=Sensitivity.NORMAL, index=True)
    current_status = Column(Enum(ComplaintStatus), default=ComplaintStatus.RECEIVED, index=True)
    assigned_bureau_id = Column(UUID(as_uuid=True), ForeignKey("bureaus.id"), nullable=True, index=True)
    assigned_officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_action_at = Column(DateTime(timezone=True), nullable=True)
    next_action = Column(String, nullable=True)
    expected_disposal_date = Column(Date, nullable=True, index=True)
    disposed_at = Column(DateTime(timezone=True), nullable=True)
    embedding_json = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    institution = relationship("Institution", back_populates="complaints")
    assigned_bureau = relationship("Bureau", back_populates="complaints", foreign_keys=[assigned_bureau_id])
    assigned_officer = relationship("User", back_populates="assigned_complaints", foreign_keys=[assigned_officer_id])
    actions = relationship("CaseAction", back_populates="complaint", cascade="all, delete-orphan", order_by="CaseAction.timestamp.asc()")
    documents = relationship("Document", back_populates="complaint", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="complaint")
    transfers = relationship("BureauTransfer", back_populates="complaint", cascade="all, delete-orphan")
    intents = relationship("ActionIntent", back_populates="complaint", cascade="all, delete-orphan")
    access_requests = relationship("AccessRequest", back_populates="complaint", cascade="all, delete-orphan")

    # Related cases
    related_as_1 = relationship("RelatedCase", back_populates="complaint_1", foreign_keys="RelatedCase.complaint_id_1")
    related_as_2 = relationship("RelatedCase", back_populates="complaint_2", foreign_keys="RelatedCase.complaint_id_2")
