from typing import Optional
from pydantic import BaseModel

from .models import StatusEnum

class PasswordRead(BaseModel):
    id: int
    password: Optional[str] = None
    hashed_password: str
    status: str

class PasswordCreate(BaseModel):
    hashed_password: str
    status: str = StatusEnum.PENDING.value