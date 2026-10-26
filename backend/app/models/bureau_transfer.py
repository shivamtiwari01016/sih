from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class TransferStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    COMPLETED = "Completed"


class BureauTransfer(Base):
    __tablename__ = "bureau_transfers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=False)
    from_bureau_id = Column(UUID(as_uuid=True), ForeignKey("bureaus.id"), nullable=False)
    to_bureau_id = Column(UUID(as_uuid=True), ForeignKey("bureaus.id"), nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=False)
    transfer_status = Column(Enum(TransferStatus), default=TransferStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    complaint = relationship("Complaint", back_populates="transfers")
    from_bureau = relationship("Bureau", back_populates="transfers_from", foreign_keys=[from_bureau_id])
    to_bureau = relationship("Bureau", back_populates="transfers_to", foreign_keys=[to_bureau_id])
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
