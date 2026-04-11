"""Client API for talking to a compushare worker.

A :class:`WorkerClient` wraps a single TCP connection and serializes calls
over it.  For parallel task submission, create one client per concurrent
in-flight task and submit from a thread pool (see ``examples/parallel_primes.py``).
"""

from __future__ import annotations

import logging
import socket
import threading
import uuid
from typing import Any, List, Optional

from . import auth, protocol

log = logging.getLogger("compushare.client")


class RemoteTaskError(RuntimeError):
    """Raised when a task running on the remote worker raises an exception."""

    def __init__(
        self,
        message: str,
        error_type: Optional[str] = None,
        traceback: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.traceback = traceback


class WorkerClient:
    """Synchronous client for a compushare worker.

    Use as a context manager for automatic cleanup::

        with WorkerClient("desktop.local", 8765, token) as client:
            print(client.call("count_primes", 1_000_000))
    """

    def __init__(
        self,
        host: str,
        port: int,
        token: str,
        connect_timeout: float = 30.0,
    ) -> None:
        self.host = host
        self.port = port
        self.token = token
        self.connect_timeout = connect_timeout
        self._sock: Optional[socket.socket] = None
        self._lock = threading.Lock()
        self.server_name: Optional[str] = None
        self.available_tasks: List[str] = []
        self.worker_count: int = 0

    # ----------------------------------------------------------- lifecycle
    def connect(self) -> None:
        sock = socket.create_connection(
            (self.host, self.port), timeout=self.connect_timeout
        )
        sock.settimeout(None)
        try:
            hello = protocol.recv_message(sock)
            if hello.get("type") != "hello":
                raise RemoteTaskError(
                    f"Expected hello from server, got {hello.get('type')!r}"
                )
            challenge = hello.get("challenge")
            if not isinstance(challenge, str):
                raise RemoteTaskError("Server hello did not include a challenge")
            self.server_name = hello.get("server_name")
            self.available_tasks = list(hello.get("tasks", []))
            self.worker_count = int(hello.get("workers", 0) or 0)
            signature = auth.sign_challenge(self.token, challenge)
            protocol.send_message(sock, {"type": "auth", "signature": signature})
            result = protocol.recv_message(sock)
            if result.get("type") != "auth_result" or not result.get("ok"):
                raise RemoteTaskError(
                    f"Authentication failed: {result.get('reason', 'unknown')}"
                )
        except Exception:
            sock.close()
            raise
        self._sock = sock
        log.info(
            "Connected to %s (%d worker slots, %d tasks)",
            self.server_name,
            self.worker_count,
            len(self.available_tasks),
        )

    def close(self) -> None:
        with self._lock:
            sock = self._sock
            self._sock = None
        if sock is None:
            return
        try:
            protocol.send_message(sock, {"type": "bye"})
        except (OSError, protocol.ProtocolError):
            pass
        try:
            sock.close()
        except OSError:
            pass

    def __enter__(self) -> "WorkerClient":
        if self._sock is None:
            self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # --------------------------------------------------------------- calls
    def _require_socket(self) -> socket.socket:
        if self._sock is None:
            raise RuntimeError("WorkerClient is not connected; call .connect() first")
        return self._sock

    def call(
        self,
        name: str,
        *args: Any,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """Run *name* on the worker with the given args and return its result."""
        task_id = str(uuid.uuid4())
        message = {
            "type": "task",
            "id": task_id,
            "name": name,
            "args": list(args),
            "kwargs": kwargs,
            "timeout": timeout,
        }
        with self._lock:
            sock = self._require_socket()
            protocol.send_message(sock, message)
            response = protocol.recv_message(sock)

        if response.get("type") != "result":
            raise RemoteTaskError(
                f"Unexpected response type: {response.get('type')!r}"
            )
        if response.get("status") == "ok":
            return response.get("result")
        raise RemoteTaskError(
            response.get("error", "unknown remote error"),
            error_type=response.get("error_type"),
            traceback=response.get("traceback"),
        )

    def list_tasks(self) -> List[str]:
        with self._lock:
            sock = self._require_socket()
            protocol.send_message(sock, {"type": "list_tasks"})
            response = protocol.recv_message(sock)
        return list(response.get("tasks", []))

    def ping(self) -> float:
        with self._lock:
            sock = self._require_socket()
            protocol.send_message(sock, {"type": "ping"})
            response = protocol.recv_message(sock)
        return float(response.get("time", 0.0))
