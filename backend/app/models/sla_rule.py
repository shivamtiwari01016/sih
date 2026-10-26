from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base


class SlaRule(Base):
    __tablename__ = "sla_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String, unique=True, nullable=False, index=True)
    days_to_dispose = Column(Integer, nullable=False, default=30)
    ack_hours_for_overlap = Column(Integer, nullable=False, default=24)
