from celery import group
from celery.app.control import Control
from app.celery import celery_app
from .db import get_session
from app.models import CrackJob, JobStatus
import hashlib

@celery_app.task(bind=True, queue='crack')
def crack_chunck(self, job_id: str, hash_value: str, algorithm: str, candidates: list[str]):
    for candidate in candidates:

        # Verify if the task has been done by another worker
        if self.is_aborted():
            return None
        
        digest = hashlib.new(algorithm, candidate.encode()).hexdigest()

        if digest == hash_value:
            with get_session() as session:
                job =  session.get(CrackJob, job_id)
                if job.status == JobStatus.running:
                    job.status = JobStatus.found
                    job.result = candidate
                    session.commit()

            # revoke all other tasks in the same job
            celery_app.control.revoke(
                self.request.group,
                terminate=True
            )
            return candidate
        
    return None

def dispatch_crack_job(job_id: str, hash_value: str, algorithm: str, wordlist: list[str], n_workers: int = 4):
    chunk_size = len(wordlist) // n_workers
    chunks =[
        wordlist[i:i+chunk_size]
        for i in range(0, len(wordlist), chunk_size)
    ]

    job = group(
        crack_chunck.s(job_id, hash_value, algorithm, chunk)
        for chunk in chunks
    )

    job.apply_async()