from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import DeclarativeBase
import enum

class TaskStatus(enum.Enum):
    pending  =  "pending"
    running = "running"
    found = "found"
    exhausted = "exhausted"

class CrackTask(DeclarativeBase):
    __tablename__ = "crack_tasks"

    id = Column(
        Integer,
        primary_key=True
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

    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.pending,
        index=True
    )

    result = Column(
        String(256),
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default="now()"
    )

    updated_at = Column(
        DateTime,
        onupdate="now()"
    )