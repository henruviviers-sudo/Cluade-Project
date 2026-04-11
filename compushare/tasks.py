"""Task registry plus a handful of built-in compute tasks.

Tasks are plain Python callables registered by name.  When a client submits a
task, the worker looks up the callable in this registry and runs it on its
process pool.  Only registered tasks can be executed - the client cannot ship
arbitrary code to the worker, which keeps the threat surface manageable.

Add your own tasks by importing :func:`register` and decorating a function::

    from compushare.tasks import register

    @register()
    def fib(n):
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a
"""

from __future__ import annotations

import hashlib
import time
from typing import Callable, Dict, List, Optional

_REGISTRY: Dict[str, Callable] = {}


class TaskNotFound(KeyError):
    """Raised when a client requests a task that is not registered."""


def register(name: Optional[str] = None) -> Callable[[Callable], Callable]:
    """Decorator that adds a callable to the task registry under *name*.

    If *name* is omitted, the function's ``__name__`` is used.
    """

    def decorator(func: Callable) -> Callable:
        task_name = name or func.__name__
        _REGISTRY[task_name] = func
        return func

    return decorator


def get_task(name: str) -> Callable:
    if name not in _REGISTRY:
        raise TaskNotFound(f"Task '{name}' is not registered")
    return _REGISTRY[name]


def list_tasks() -> List[str]:
    return sorted(_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Built-in tasks
# ---------------------------------------------------------------------------


@register()
def ping() -> str:
    """Return ``'pong'``.  Useful for liveness checks."""
    return "pong"


@register()
def echo(value):
    """Return *value* unchanged."""
    return value


@register()
def sum_range(start: int, stop: int) -> int:
    """Return ``sum(range(start, stop))``."""
    return sum(range(int(start), int(stop)))


@register()
def count_primes(limit: int) -> int:
    """Count primes strictly below *limit* using a Sieve of Eratosthenes."""
    limit = int(limit)
    if limit < 3:
        return 0
    sieve = bytearray([1]) * limit
    sieve[0] = 0
    sieve[1] = 0
    for i in range(2, int(limit ** 0.5) + 1):
        if sieve[i]:
            start = i * i
            sieve[start::i] = b"\x00" * ((limit - start - 1) // i + 1)
    return sum(sieve)


@register()
def count_primes_in_range(lo: int, hi: int) -> int:
    """Count primes in ``[lo, hi)``.  Used by the parallel-fan-out example."""
    lo = max(int(lo), 2)
    hi = int(hi)
    if hi <= lo:
        return 0
    sieve = bytearray([1]) * hi
    sieve[0] = 0
    sieve[1] = 0
    for i in range(2, int(hi ** 0.5) + 1):
        if sieve[i]:
            start = i * i
            sieve[start::i] = b"\x00" * ((hi - start - 1) // i + 1)
    return sum(sieve[lo:hi])


@register()
def hash_data(data, algorithm: str = "sha256") -> str:
    """Hash *data* (str or bytes) using the named hashlib algorithm."""
    h = hashlib.new(algorithm)
    if isinstance(data, str):
        data = data.encode("utf-8")
    elif isinstance(data, list):
        # JSON has no native byte type, so byte payloads come across as a list
        # of integers from the client side.
        data = bytes(data)
    h.update(data)
    return h.hexdigest()


@register()
def matmul(a, b):
    """Naive O(n^3) matrix multiply for two 2-D lists.  Returns a list of lists."""
    rows_a = len(a)
    cols_a = len(a[0]) if rows_a else 0
    rows_b = len(b)
    cols_b = len(b[0]) if rows_b else 0
    if cols_a != rows_b:
        raise ValueError(
            f"Incompatible matrix shapes: {rows_a}x{cols_a} * {rows_b}x{cols_b}"
        )
    result = [[0.0] * cols_b for _ in range(rows_a)]
    for i in range(rows_a):
        row_a = a[i]
        result_row = result[i]
        for k in range(cols_a):
            aik = row_a[k]
            row_b = b[k]
            for j in range(cols_b):
                result_row[j] += aik * row_b[j]
    return result


@register()
def sleep(seconds: float) -> float:
    """Sleep for *seconds* seconds and return that value.  Useful for testing."""
    time.sleep(float(seconds))
    return float(seconds)
