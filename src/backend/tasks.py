import time
import hashlib
import redis
from celery import Celery, group
from sqlalchemy import update
from celery.result import GroupResult

from database import Database, Settings, PasswordModel, StatusEnum

CELERY_BROKER_URL = 'redis://redis:6379/0'

celery_app = Celery(
    'cracker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1
)

redis_client = redis.Redis(host='redis', port=6379, db=1, decode_responses=True)

def markJobAsFound(job_id: int, cracked_pass: str):
    settings = Settings()
    db = Database(settings)

    with db.getSession() as session:
        session.execute(
            update(PasswordModel)
            .where(PasswordModel.id == job_id)
            .values(password=cracked_pass, status=StatusEnum.FOUND.value)
        )
        session.commit()

def cancelGroup(group_id: str, job_id: int):
    saved_group = GroupResult.restore(group_id, app=celery_app)
    if saved_group:
        saved_group.revoke(terminate=True, signal='SIGKILL')
        redis_client.delete(f"tasks_for_job_{job_id}")
        return f"Group {group_id} cancelled successfully."
    else:
        return f"No group found with id: {group_id}"

@celery_app.task
def processWordListChunck(
    job_id: int,
    target_hash: str,
    wordlist_path: str,
    start: int,
    end: int
):
    flag_key = f"job_cracked_{job_id}"

    if redis_client.get(flag_key):
        return f"Worker aborted, another worker cracked the hash: {job_id}"

    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as wordlist:
            lines_to_read = end - start

            for _ in range(start):
                next(wordlist, None)

            for i in range(lines_to_read):
                word = wordlist.readline()

                if not word:
                    break

                word = word.strip()

                if i % 1000 == 0:
                    if redis_client.get(flag_key):
                        return f"Worker aborted, another worker cracked the hash: {job_id}"
                    
                word_hash = hashlib.md5(word.encode()).hexdigest()

                if word_hash == target_hash:
                    redis_client.set(flag_key, "true", ex=86400)

                    markJobAsFound(job_id, word)

                    group_id = redis_client.get(f"group_id_{job_id}")
                    if not group_id:
                        time.sleep(0.5)
                        group_id = redis_client.get(f"group_id_{job_id}")

                    if group_id:
                        print(cancelGroup(group_id, job_id))
                    else:
                        print(f"CRITICAL: Dont is possible, group_id should be in Redis for job_id {job_id}")

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
    redis_client.delete(f"tasks_for_job_{job_id}")

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
    result = job_group.apply_async()
    result.save()

    redis_client.set(f"group_id_{job_id}", result.id, ex=86400)

    return f"Work {job_id} dispatched with {len(tasks)} chunks and sent to Redis"