import uvicorn
from typing import Dict
from hashlib import md5, sha256
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Hash Generator para Cracking")

hashes: Dict[str, str] = {}

class PassInput(BaseModel):
    password: str
    algorithm: str = "md5"

@app.post("/genhash")
def generate_hash(input: PassInput):
    if input.algorithm == "md5":
        hash = md5(input.password.encode()).hexdigest()
    elif input.algorithm == "sha256":
        hash = sha256(input.password.encode()).hexdigest()
    else:
        raise HTTPException(status_code=400, detail="Unsupported algorithm")
    
    hash_id = f"hash_{len(hashes)}"
    hashes[hash_id] = hash
    return {"hash_id": hash_id, "hash": hash}

@app.get("/hash/{hash_id}")
def get_hash(hash_id: str):
    if hash_id not in hashes:
        raise HTTPException(status_code=404, detail="Hash not found")
    return {"hash": hashes[hash_id]}