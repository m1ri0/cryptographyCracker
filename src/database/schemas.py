from pydantic import BaseModel

class PasswordRead(BaseModel):
    id: int
    hashed_password: str

class PasswordCreate(BaseModel):
    password: str