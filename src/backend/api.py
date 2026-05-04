from sqlalchemy import select
from typing import Dict, List
from fastapi import APIRouter, Depends

from database import Database, Settings, PasswordModel, PasswordCreate, PasswordRead

router = APIRouter(prefix="/api", tags=["API Endpoints"])

@router.get("/all-hashes")
async def getAllHashes(session = Depends(Database(Settings()).getSession)) -> Dict:
    result = await session.execute(
        select(PasswordModel.id, PasswordModel.password, PasswordModel.hash, PasswordModel.status)
    )
    hashes = result.fetchall()
    
    return {"hashes": [{"id": id, "password": password, "hash": hash, "status": status} for id, password, hash, status in hashes] }

@router.get("/hash/{hash_id}")
async def getHashById(hash_id: int, session = Depends(Database(Settings()).getSession)) -> Dict:
    result = await session.execute(
        select(PasswordModel.id, PasswordModel.password, PasswordModel.hash, PasswordModel.status)
        .where(PasswordModel.id == hash_id)
    )
    hash_data = result.fetchone()

    if not hash_data:
        return {"error": "Hash not found"}

    id, password, hash, status = hash_data
    return {"id": id, "password": password, "hash": hash, "status": status}

@router.post("/add-hash")
async def addHash(hash: str, session = Depends(Database(Settings()).getSession)) -> Dict:
    new_password = PasswordCreate(hashed_password=hash)

    session.add(new_password)
    await session.commit()
    await session.refresh(new_password)

    return {
        "hash": new_password.hashed_password
    }