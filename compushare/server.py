"""TCP worker server.

This module hosts the worker that runs on the machine donating CPU time
(typically the desktop).  Each accepted client connection runs in its own
handler thread; tasks are dispatched onto a shared process pool so the worker
can use every core in parallel.
"""

from __future__ import annotations

import logging
import os
import socketserver
import time
import traceback
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Optional, Union

from . import auth, protocol, tasks

log = logging.getLogger("compushare.server")

Executor = Union[ProcessPoolExecutor, ThreadPoolExecutor]


def _run_task(name, args, kwargs):
    """Top-level helper so it can be pickled and sent to worker processes."""
    func = tasks.get_task(name)
    return func(*args, **kwargs)


class _WorkerHandler(socketserver.BaseRequestHandler):
    """Per-connection handler.  One instance lives in each handler thread."""

    server: "WorkerServer"  # narrowed type for the inherited attribute

    def handle(self) -> None:
        sock = self.request
        peer = self.client_address
        log.info("Connection from %s:%s", peer[0], peer[1])
        try:
            if not self._authenticate(sock):
                log.warning("Authentication failed for %s:%s", peer[0], peer[1])
                return
            self._serve(sock)
        except protocol.ProtocolError as exc:
            log.warning("Protocol error from %s:%s: %s", peer[0], peer[1], exc)
        except Exception:  # noqa: BLE001
            log.exception("Unhandled error serving %s:%s", peer[0], peer[1])
        finally:
            try:
                sock.close()
            except OSError:
                pass
            log.info("Disconnected %s:%s", peer[0], peer[1])

    # ------------------------------------------------------------------ auth
    def _authenticate(self, sock) -> bool:
        challenge = auth.make_challenge()
        protocol.send_message(
            sock,
            {
                "type": "hello",
                "server_name": self.server.name,
                "version": 1,
                "challenge": challenge,
                "tasks": tasks.list_tasks(),
                "workers": self.server.max_workers,
            },
        )
        response = protocol.recv_message(sock)
        if response.get("type") != "auth":
            protocol.send_message(
                sock,
                {"type": "auth_result", "ok": False, "reason": "expected auth message"},
            )
            return False
        signature = response.get("signature", "")
        if not isinstance(signature, str) or not auth.verify_signature(
            self.server.token, challenge, signature
        ):
            protocol.send_message(
                sock,
                {"type": "auth_result", "ok": False, "reason": "bad signature"},
            )
            return False
        protocol.send_message(sock, {"type": "auth_result", "ok": True})
        return True

    # --------------------------------------------------------------- request
    def _serve(self, sock) -> None:
        while True:
            try:
                msg = protocol.recv_message(sock)
            except protocol.ProtocolError:
                return
            mtype = msg.get("type")
            if mtype == "task":
                self._handle_task(sock, msg)
            elif mtype == "list_tasks":
                protocol.send_message(
                    sock, {"type": "task_list", "tasks": tasks.list_tasks()}
                )
            elif mtype == "ping":
                protocol.send_message(sock, {"type": "pong", "time": time.time()})
            elif mtype == "bye":
                return
            else:
                protocol.send_message(
                    sock,
                    {"type": "error", "message": f"Unknown message type: {mtype!r}"},
                )

    def _handle_task(self, sock, msg) -> None:
        task_id = msg.get("id") or str(uuid.uuid4())
        name = msg.get("name")
        args = msg.get("args") or []
        kwargs = msg.get("kwargs") or {}
        timeout = msg.get("timeout")

        if not isinstance(name, str):
            protocol.send_message(
                sock,
                {
                    "type": "result",
                    "id": task_id,
                    "status": "error",
                    "error": "task name must be a string",
                    "error_type": "ValueError",
                },
            )
            return

        log.info(
            "Task %s: %s args=%s kwargs=%s timeout=%s",
            task_id,
            name,
            args,
            kwargs,
            timeout,
        )
        start = time.time()
        try:
            future = self.server.executor.submit(_run_task, name, args, kwargs)
            result = future.result(timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            elapsed = time.time() - start
            log.warning("Task %s failed after %.3fs: %s", task_id, elapsed, exc)
            protocol.send_message(
                sock,
                {
                    "type": "result",
                    "id": task_id,
                    "status": "error",
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "traceback": traceback.format_exc(),
                    "elapsed": elapsed,
                },
            )
            return

        elapsed = time.time() - start
        log.info("Task %s completed in %.3fs", task_id, elapsed)
        protocol.send_message(
            sock,
            {
                "type": "result",
                "id": task_id,
                "status": "ok",
                "result": result,
                "elapsed": elapsed,
            },
        )


class WorkerServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP server backed by a process pool."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        host: str,
        port: int,
        token: str,
        max_workers: Optional[int] = None,
        name: str = "compushare-worker",
        use_processes: bool = True,
    ) -> None:
        super().__init__((host, port), _WorkerHandler)
        self.token = token
        self.name = name
        self.max_workers = max_workers or os.cpu_count() or 1
        self.executor: Executor
        if use_processes:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def server_close(self) -> None:
        super().server_close()
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            # cancel_futures was added in 3.9; fall back gracefully
            self.executor.shutdown(wait=False)


def serve(
    host: str,
    port: int,
    token: str,
    max_workers: Optional[int] = None,
    use_processes: bool = True,
) -> None:
    """Run a worker until the process is interrupted."""
    server = WorkerServer(
        host, port, token, max_workers=max_workers, use_processes=use_processes
    )
    log.info(
        "compushare worker listening on %s:%s with %d %s",
        host,
        port,
        server.max_workers,
        "processes" if use_processes else "threads",
    )
    log.info("Registered tasks: %s", ", ".join(tasks.list_tasks()))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Interrupted, shutting down")
    finally:
        server.server_close()
