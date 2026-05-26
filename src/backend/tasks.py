import os
import random
import time
import hashlib
import redis
from celery import Celery, chord
from sqlalchemy import update

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

db = Database(Settings())

ACTIVE_QUEUES_KEY = "active_job_queues"

def normalizeWordlistPaths(wordlist_paths):
    if not wordlist_paths:
        return []

    if isinstance(wordlist_paths, str):
        return [path.strip() for path in wordlist_paths.split(",") if path.strip()]

    return [str(path).strip() for path in wordlist_paths if str(path).strip()]

def expandWordlistPaths(wordlist_paths):
    expanded_paths = []

    for path in normalizeWordlistPaths(wordlist_paths):
        if os.path.isdir(path):
            files = sorted(
                os.path.join(path, filename)
                for filename in os.listdir(path)
                if os.path.isfile(os.path.join(path, filename))
            )
            expanded_paths.extend(files)
        else:
            expanded_paths.append(path)

    return expanded_paths

def cleanupJobKeys(job_id: int):
    redis_client.delete(f"job_cracked_{job_id}")
    redis_client.delete(f"group_id_{job_id}")
    redis_client.delete(f"current_wordlist_{job_id}")
    redis_client.delete(f"tasks_for_job_{job_id}")

def getDatabaseSession():
    return db.getSession()

def markJobAsProcessing(job_id: int):
    with getDatabaseSession() as session:
        session.execute(
            update(PasswordModel)
            .where(PasswordModel.id == job_id)
            .values(status=StatusEnum.PROCESSING.value)
        )
        session.commit()

def markJobAsFound(job_id: int, cracked_pass: str):
    with getDatabaseSession() as session:
        session.execute(
            update(PasswordModel)
            .where(PasswordModel.id == job_id)
            .values(password=cracked_pass, status=StatusEnum.FOUND.value)
        )
        session.commit()

def markJobAsExhausted(job_id: int):
    with getDatabaseSession() as session:
        session.execute(
            update(PasswordModel)
            .where(PasswordModel.id == job_id)
            .values(status=StatusEnum.EXHAUSTED.value)
        )
        session.commit()

def cancelGroup(group_id: str, job_id: int):
    try:
        celery_app.control.revoke(group_id, terminate=True, signal='SIGKILL')
        return f"Group {group_id} cancelled successfully."
    except Exception as e:
        return f"Error cancelling group {group_id}: {str(e)}"

def shuffleQueue(queue_name: str = "celery"):
    with redis_client.pipeline() as pipe:
        while True:
            try:
                pipe.watch(queue_name)
                tasks = pipe.lrange(queue_name, 0, -1)

                if not tasks:
                    pipe.reset()
                    return
                
                tasks = list(tasks)
                random.shuffle(tasks)

                pipe.multi()
                pipe.delete(queue_name)
                pipe.rpush(queue_name, *tasks)
                pipe.execute()
                break

            except Exception as e:
                print(f"Error shuffling queue: {e}")
                time.sleep(1)
                continue


@celery_app.task
def finalizeJob(results: list, job_id: int):
    flag_key = f"job_cracked_{job_id}"
    
    if not redis_client.get(flag_key):
        markJobAsExhausted(job_id)
        cleanupJobKeys(job_id)
        return f"Job {job_id} exhausted. No password found."

    cleanupJobKeys(job_id)

@celery_app.task
def finalizeWordlist(
    results: list,
    job_id: int,
    target_hash: str,
    wordlist_paths,
    next_wordlist_index: int,
    lines_per_chunk: int
):
    flag_key = f"job_cracked_{job_id}"

    if redis_client.get(flag_key):
        cleanupJobKeys(job_id)
        return f"Job {job_id} cracked. Wordlist rotation stopped."

    return dispatchWordlist(
        job_id=job_id,
        target_hash=target_hash,
        wordlist_paths=wordlist_paths,
        wordlist_index=next_wordlist_index,
        lines_per_chunk=lines_per_chunk
    )

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
    wordlist_path=None,
    wordlist_paths=None,
    lines_per_chunk: int = 50_000
):
    configured_wordlists = wordlist_paths if wordlist_paths is not None else wordlist_path

    cleanupJobKeys(job_id)
    markJobAsProcessing(job_id)

    return dispatchWordlist(
        job_id=job_id,
        target_hash=target_hash,
        wordlist_paths=expandWordlistPaths(configured_wordlists),
        wordlist_index=0,
        lines_per_chunk=lines_per_chunk
    )

def dispatchWordlist(
    job_id: int,
    target_hash: str,
    wordlist_paths,
    wordlist_index: int,
    lines_per_chunk: int
):
    queue_name = f"job_{job_id%5}"
    paths = expandWordlistPaths(wordlist_paths)

    while wordlist_index < len(paths):
        wordlist_path = paths[wordlist_index]

        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as wordlist:
                total_lines = sum(1 for _ in wordlist)
        except FileNotFoundError:
            print(f"Wordlist file not found: {wordlist_path}. Trying next wordlist.")
            wordlist_index += 1
            continue

        if total_lines <= 0:
            print(f"Wordlist file is empty: {wordlist_path}. Trying next wordlist.")
            wordlist_index += 1
            continue

        tasks = []
        for start in range(0, total_lines, lines_per_chunk):
            end = min(start + lines_per_chunk, total_lines)
            tasks.append(
                processWordListChunck
                .s(job_id, target_hash, wordlist_path, start, end)
                .set(queue=queue_name)
            )

        callback = finalizeWordlist.s(
            job_id=job_id,
            target_hash=target_hash,
            wordlist_paths=paths,
            next_wordlist_index=wordlist_index + 1,
            lines_per_chunk=lines_per_chunk
        ).set(queue=queue_name)

        result = chord(tasks)(callback)
        redis_client.set(f"group_id_{job_id}", result.id, ex=86400)
        redis_client.set(f"current_wordlist_{job_id}", wordlist_path, ex=86400)

        return (
            f"Work {job_id} dispatched with {len(tasks)} chunks "
            f"for wordlist {wordlist_path}"
        )

    markJobAsExhausted(job_id)
    cleanupJobKeys(job_id)

    return f"Job {job_id} exhausted. No password found in configured wordlists."