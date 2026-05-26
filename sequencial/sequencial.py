import argparse
import hashlib
import os
import time


DEFAULT_WORDLISTS = "src/wordlists/Pwdb_top-10000000.txt"


def normalize_wordlist_paths(wordlists):
    paths = []

    for value in wordlists:
        paths.extend(path.strip() for path in value.split(",") if path.strip())

    return paths


def expand_wordlist_paths(wordlists):
    expanded_paths = []

    for path in normalize_wordlist_paths(wordlists):
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


def md5_hash(value):
    return hashlib.md5(value.encode()).hexdigest()


def crack_hash(target_hash, wordlist_paths):
    attempts = 0
    skipped_wordlists = []
    started_at = time.perf_counter()

    for wordlist_path in wordlist_paths:
        try:
            with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as wordlist:
                for raw_word in wordlist:
                    word = raw_word.strip()

                    if not word:
                        continue

                    attempts += 1

                    if md5_hash(word) == target_hash:
                        elapsed = time.perf_counter() - started_at
                        return {
                            "status": "found",
                            "password": word,
                            "wordlist": wordlist_path,
                            "attempts": attempts,
                            "elapsed_seconds": elapsed,
                            "hashes_per_second": attempts / elapsed if elapsed > 0 else attempts
                        }
        except FileNotFoundError:
            skipped_wordlists.append(wordlist_path)

    elapsed = time.perf_counter() - started_at
    return {
        "status": "exhausted",
        "password": None,
        "wordlist": None,
        "attempts": attempts,
        "elapsed_seconds": elapsed,
        "hashes_per_second": attempts / elapsed if elapsed > 0 else attempts,
        "skipped_wordlists": skipped_wordlists
    }


def print_result(result):
    print(f"Status: {result['status']}")
    print(f"Attempts: {result['attempts']}")
    print(f"Elapsed seconds: {result['elapsed_seconds']:.6f}")
    print(f"Hashes per second: {result['hashes_per_second']:.2f}")

    if result["status"] == "found":
        print(f"Password: {result['password']}")
        print(f"Wordlist: {result['wordlist']}")
    else:
        skipped = result.get("skipped_wordlists", [])
        if skipped:
            print("Skipped wordlists:")
            for wordlist_path in skipped:
                print(f"- {wordlist_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sequential MD5 wordlist cracker for comparison with Celery workers."
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--hash", dest="target_hash", help="MD5 hash to crack.")
    target.add_argument("--password", help="Plain password to hash and crack.")
    parser.add_argument(
        "--wordlists",
        nargs="+",
        default=[DEFAULT_WORDLISTS],
        help="Wordlist files, directories, or comma-separated paths."
    )

    return parser.parse_args()


def main():
    args = parse_args()
    target_hash = args.target_hash or md5_hash(args.password)
    wordlist_paths = expand_wordlist_paths(args.wordlists)

    print(f"Target hash: {target_hash}")
    print(f"Wordlists: {len(wordlist_paths)}")

    result = crack_hash(target_hash, wordlist_paths)
    print_result(result)


if __name__ == "__main__":
    main()
