from sqlalchemy import Column, String, DateTime, Index, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aicte_permanent_id = Column(String, unique=True, nullable=True, index=True)
    institution_name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False, index=True)
    aliases = Column(Text, nullable=True)  # JSON-encoded string of alternate names/abbreviations
    institution_type = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    region = Column(String, nullable=True, index=True)
    district = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    contact_email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    established_year = Column(Integer, nullable=True)
    ownership = Column(String, nullable=True)
    affiliation = Column(String, nullable=True)
    institution_status = Column(String, default="Active")
    embedding = Column(Text, nullable=True)  # JSON-encoded vector embedding
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    complaints = relationship("Complaint", back_populates="institution")
    watchers = relationship("Watchlist", back_populates="institution", cascade="all, delete-orphan")
    action_intents = relationship("ActionIntent", back_populates="institution", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_institution_name_region', 'normalized_name', 'region'),
    )
