import hashlib
from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy import select

from database import Database, Settings, PasswordModel, PasswordMapper
from backend.tasks import dispatchBruteForce 

router = APIRouter(prefix="/cripto_crack", tags=["API Endpoints"])

@router.get("/all-hashes")
async def getAllHashes(session = Depends(Database(Settings()).getAsyncSession)) -> Dict:
    result = await session.execute(
        select(PasswordModel.id, PasswordModel.password, PasswordModel.hashed_password, PasswordModel.status)
    )
    hashes = result.fetchall()
    
    return {"hashes": [PasswordMapper.to_dict(password) for password in hashes] }

@router.get("/hash/{hash_id}")
async def getHashById(hash_id: int, session = Depends(Database(Settings()).getAsyncSession)) -> Dict:
    result = await session.execute(
        select(PasswordModel.id, PasswordModel.password, PasswordModel.hashed_password, PasswordModel.status)
        .where(PasswordModel.id == hash_id)
    )
    hash_data = result.fetchone()

    if not hash_data:
        return {"error": "Hash not found"}

    id, password, hash, status = hash_data
    return PasswordMapper.to_dict(PasswordModel(id=id, password=password, hashed_password=hash, status=status))

@router.post("/add-password")
async def addPassword(password: str, session = Depends(Database(Settings()).getAsyncSession)) -> Dict:
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    new_password = PasswordModel(hashed_password=hashed_password)

    session.add(new_password)
    await session.commit()
    await session.refresh(new_password)

    return PasswordMapper.to_dict(new_password)

@router.post("/crack/{hash_id}")
async def crackPassword(hash_id: int, session = Depends(Database(Settings()).getAsyncSession)) -> Dict:
    search_result = await session.execute(
        select(PasswordModel)
        .where(PasswordModel.id == hash_id)
    )

    password_entry = search_result.scalar_one_or_none()

    if not password_entry:
        return {"error": "Hash not found"}
    
    task = dispatchBruteForce.delay(job_id=password_entry.id, target_hash=password_entry.hashed_password, wordlist_path="./wordlists/Pwdb_top-10000000.txt")

    return {"message": "Task dispatched successfully",
            "task_id": task.id
    }