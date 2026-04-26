import asyncio
import hashlib
import redis
from celery import Celery
from celery import group
from sqlalchemy.future import select
from sqlalchemy import update

from database import Database, Settings, PasswordModel, StatusEnum

CELERY_BROKER_URL = 'redis://redis:6379/0'

celery_app = Celery(
    'cracker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL
)

redis_client = redis.Redis(host='redis', port=6379, db=1, decode_responses=True)

settings = Settings()
db = Database(settings)

async def markJobAsFound(job_id: int, cracked_pass: str):
    async with db.getSession() as session:
        await session.execute(
            update(PasswordModel)
            .where(PasswordModel.id == job_id)
            .values(password=cracked_pass, status=StatusEnum.FOUND.value)
        )
        await session.commit()

@celery_app.task
def processWordListChunck(
    job_id: int,
    target_hash: str,
    wordlist_path: str,
    start: int,
    end: int
):
    flag_key = f"job_cracked_{job_id}"

    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as wordlist:
            for _ in range(start):
                next(wordlist, None)

                lines_to_read = end - start

            for i in range(lines_to_read):
                word = wordlist.readline()

                if not word:
                    break

                word = word.strip()

                if i % 1000 == 0:
                    if redis_client.get(flag_key):
                        return f"Worker aborted, another worker cracked the hash: {job_id}"
                    
                word_hash = hashlib.md5(word.encode().hexdigest())

                if word_hash == target_hash:
                    redis_client.set(flag_key, "true", ex=86400)

                    asyncio.run(markJobAsFound(job_id, word))

                    return f"Hash cracked! {word}"
                
        return f"Chunk processed, {start}-{end}. Hash not found: {job_id}"
    except FileNotFoundError:
        return f"Wordlist file not found: {wordlist_path}"
    
@celery_app.task
def dispatchBruteForce(
    job_id: int,
    target_hash: str,
    wordlist_path: str,
    lines_per_chunk: int = 50_000
):
    redis_client.delete(f"job_cracked_{job_id}")

    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as wordlist:
            total_lines = sum(1 for _ in wordlist)
    except FileNotFoundError:
        return f"Wordlist file not found: {wordlist_path}"
    
    tasks = []
    for start in range(0, total_lines, lines_per_chunk):
        end = min(start + lines_per_chunk, total_lines)
        tasks.append(processWordListChunck.s(job_id, target_hash, wordlist_path, start, end))

    job_group = group(tasks)
    job_group.apply_async()

    return f"Work {job_id} dispatched with {len(tasks)} chunks and sent to Redis"