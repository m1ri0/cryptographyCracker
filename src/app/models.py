from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
import enum
import uuid

class Base(DeclarativeBase):
    pass

class JobStatus(enum.Enum):
    running = "running"
    found = "found"
    exhausted = "exhausted"

class HashRecord(Base):
    __tablename__ = "hash_records"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    hash_value = Column(
        String(256),
        nullable=False,
        index=True
    )

    algorithm = Column(
        String(32),
        nullable=False
    )

class CrackJob(Base):
    __tablename__ = "crack_jobs"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    hash_id = Column(
        String,
        ForeignKey("hash_records.id"),
        nullable=False,
        index=True
    )

    status = Column(
        Enum(JobStatus),
        default=JobStatus.running,
        index=True
    )

    result = Column(
        String(256),
        nullable=True
    )