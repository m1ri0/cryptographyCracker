from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bruteforce:secret@db:5432/hashcracker")

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()