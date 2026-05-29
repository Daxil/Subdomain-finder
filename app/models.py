from sqlalchemy import Column, Integer, String, JSON, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class ScanStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

class Target(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ScanJob(Base):
    __tablename__ = "scan_jobs"
    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, nullable=False)
    status = Column(Enum(ScanStatus), default=ScanStatus.pending)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    results = Column(JSON, nullable=True)
