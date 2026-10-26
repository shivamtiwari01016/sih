from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "Super Administrator"
    ADMIN = "Admin"
    BUREAU_ADMIN = "Bureau Administrator"
    CASE_OFFICER = "Case Officer"
    RB_OFFICER = "RB Officer"
    PGRC_OFFICER = "PGRC Officer"
    REGIONAL_OFFICER = "Regional Officer"
    SENIOR_MANAGEMENT = "Senior Management"
    AUDITOR = "Auditor"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    bureau_id = Column(UUID(as_uuid=True), ForeignKey("bureaus.id"), nullable=True)
    region_permissions = Column(String, nullable=True)  # Comma-separated regions or 'All'
    active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    bureau = relationship("Bureau", back_populates="users")
    assigned_complaints = relationship("Complaint", back_populates="assigned_officer", foreign_keys="Complaint.assigned_officer_id")
    actions = relationship("CaseAction", back_populates="officer")
    audit_logs = relationship("AuditLog", back_populates="actor")
    notifications = relationship("Notification", back_populates="recipient")
    watchlist_items = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
