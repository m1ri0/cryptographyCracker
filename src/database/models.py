from enum import Enum
from sqlalchemy import Column, Integer, String

from .db import Base

class StatusEnum(Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    FOUND = 'found'
    EXHAUSTED = 'exhausted'

class Password(Base):
    __tablename__ = 'password'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )

    password = Column(
        String(32),
        nullable=True
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default=StatusEnum.PENDING.value
    )