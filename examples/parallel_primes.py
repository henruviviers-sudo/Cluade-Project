"""Fan a prime-counting workload out across the worker's CPU cores.

Each chunk runs over its own TCP connection so the worker can dispatch them
onto different processes in its pool concurrently.

Usage::

    python examples/parallel_primes.py --host desktop.local --token mysecret \
        --limit 20000000 --chunks 8
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# Make `compushare` importable when running this file directly from the repo.
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compushare.client import WorkerClient  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--token", required=True)
    parser.add_argument("--limit", type=int, default=10_000_000)
    parser.add_argument("--chunks", type=int, default=8)
    args = parser.parse_args()

    if args.chunks < 1:
        parser.error("--chunks must be >= 1")

    chunk_size = args.limit // args.chunks
    ranges = []
    for i in range(args.chunks):
        lo = i * chunk_size
        hi = args.limit if i == args.chunks - 1 else (i + 1) * chunk_size
        ranges.append((lo, hi))

    print(
        f"Counting primes below {args.limit:,} in {args.chunks} chunk(s) "
        f"on {args.host}:{args.port}"
    )

    clients = [WorkerClient(args.host, args.port, args.token) for _ in ranges]
    for c in clients:
        c.connect()

    try:
        start = time.time()
        with ThreadPoolExecutor(max_workers=len(clients)) as pool:
            futures = [
                pool.submit(client.call, "count_primes_in_range", lo, hi)
                for client, (lo, hi) in zip(clients, ranges)
            ]
            counts = [f.result() for f in futures]
        elapsed = time.time() - start
    finally:
        for c in clients:
            c.close()

    total = sum(counts)
    print(f"Found {total:,} primes in {elapsed:.2f}s")
    for (lo, hi), count in zip(ranges, counts):
        print(f"  [{lo:>12,}, {hi:>12,}) -> {count:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
