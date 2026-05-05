from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy import select

from database import Database, Settings, PasswordModel, PasswordMapper

router = APIRouter(prefix="cripto_crack", tags=["API Endpoints"])

@router.get("/all-hashes")
async def getAllHashes(session = Depends(Database(Settings()).getSession)) -> Dict:
    result = await session.execute(
        select(PasswordModel.id, PasswordModel.password, PasswordModel.hashed_password, PasswordModel.status)
    )
    hashes = result.fetchall()
    
    return {"hashes": [PasswordMapper.to_dict(password) for password in hashes] }

@router.get("/hash/{hash_id}")
async def getHashById(hash_id: int, session = Depends(Database(Settings()).getSession)) -> Dict:
    result = await session.execute(
        select(PasswordModel.id, PasswordModel.password, PasswordModel.hashed_password, PasswordModel.status)
        .where(PasswordModel.id == hash_id)
    )
    hash_data = result.fetchone()

    if not hash_data:
        return {"error": "Hash not found"}

    id, password, hash, status = hash_data
    return PasswordMapper.to_dict(PasswordModel(id=id, password=password, hashed_password=hash, status=status))

@router.post("/add-hash")
async def addHash(hash: str, session = Depends(Database(Settings()).getSession)) -> Dict:
    new_password = PasswordModel(hashed_password=hash)

    session.add(new_password)
    await session.commit()
    await session.refresh(new_password)

    return PasswordMapper.to_dict(new_password)