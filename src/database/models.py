from .db import Base
from sqlalchemy import Column, Integer, String

class Password(Base):
    __tablename__ = 'password'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )

    password = Column(
        String(31),
        nullable=False
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )