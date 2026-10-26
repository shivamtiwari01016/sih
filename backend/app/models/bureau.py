from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Bureau(Base):
    __tablename__ = "bureaus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bureau_code = Column(String, unique=True, nullable=False)
    bureau_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="bureau")
    complaints = relationship("Complaint", back_populates="assigned_bureau", foreign_keys="Complaint.assigned_bureau_id")
    transfers_from = relationship("BureauTransfer", back_populates="from_bureau", foreign_keys="BureauTransfer.from_bureau_id")
    transfers_to = relationship("BureauTransfer", back_populates="to_bureau", foreign_keys="BureauTransfer.to_bureau_id")
    actions = relationship("CaseAction", back_populates="bureau")
