from typing import Dict
from hashlib import md5, sha256
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.db import get_session
from app.models import HashRecord, CrackJob, JobStatus
from core.tasks import dispatch_crack_job

app = FastAPI(title="Hash Generator para Cracking")

class PassInput(BaseModel):
    password: str
    algorithm: str = "md5"

class CrackInput(BaseModel):
    n_workers: int = 4

@app.post("/gen-hash")
def generate_hash(input: PassInput, session: Session = Depends(get_session)):
    if input.algorithm == "md5":
        hash = md5(input.password.encode()).hexdigest()
    elif input.algorithm == "sha256":
        hash = sha256(input.password.encode()).hexdigest()
    else:
        raise HTTPException(status_code=400, detail="Unsupported algorithm")
    
    record = HashRecord(hash=hash, algorithm=input.algorithm)
    session.add(record)
    session.commit()
    session.refresh(record)

    return {"hash_id": record.id, "hash": hash}

@app.post("/crack/{hash_id}")
def crack_hash(hash_id: str, input: CrackInput, session: Session = Depends(get_session)):
    record = session.get(HashRecord, hash_id)
    if not record:
        raise HTTPException(status_code=404, detail="Hash not found")
    
    job = CrackJob(hash_id=hash_id, status=JobStatus.running)
    session.add(job)
    session.commit()
    session.refresh(job)

    dispatch_crack_job(
        job_id=str(job.id),
        hash=record.hash,
        algorithm=record.algorithm,
        n_workers=input.n_workers
    )

    return {"job_id": str(job.id), "status": "running"}

@app.get("/jobs/{job_id}")
def get_job(job_id: str, session: Session = Depends(get_session)):
    job = session.get(CrackJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": job.status, "result": job.result}