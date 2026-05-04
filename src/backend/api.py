from sqlalchemy import select
from typing import Dict, List
from fastapi import FastAPI, Depends

from database import Database, Settings, PasswordModel, PasswordCreate, PasswordRead

api_app = FastAPI(title="Cripto Cracker API")

@api_app.get("/all-hashes")
async def getAllHashes(db: Database = Depends(Database(Settings()))):
    async with db.getSession() as session:
        result = await session.execute(
            select(PasswordModel.id, PasswordModel.password, PasswordModel.hash, PasswordModel.status)
        )
        hashes = result.fetchall()

    return {"hashes": [{"id": id, "password": password, "hash": hash, "status": status} for id, password, hash, status in hashes] }

@api_app.get("/hash/{hash_id}")
async def getHashById(hash_id: int, db: Database = Depends(Database(Settings()))) -> Dict:
    async with db.getSession() as session:
        result = await session.execute(
            select(PasswordModel.id, PasswordModel.password, PasswordModel.hash, PasswordModel.status)
            .where(PasswordModel.id == hash_id)
        )
        hash_data = result.fetchone()

    if not hash_data:
        return {"error": "Hash not found"}

    id, password, hash, status = hash_data
    return {"id": id, "password": password, "hash": hash, "status": status}

@api_app.post("/add-hash")
async def addHash(hash: str, db: Database = Depends(Database(Settings()))) -> Dict:
    new_password = PasswordCreate(hash=hash)

    async with db.getSession() as session:
        session.add(new_password)
        await session.commit()
        await session.refresh(new_password)

    return {
        "hash": new_password.hash
    }