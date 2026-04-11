"""compushare - share processing power between machines over a network.

Run a worker on the desktop (`python worker.py --token <secret>`) and submit
tasks from the laptop (`python submit.py --host <desktop> --token <secret>
<task> [args...]`).  Tasks are Python callables registered on the worker via
`compushare.tasks.register`.
"""

from . import auth, client, protocol, server, tasks
from .client import RemoteTaskError, WorkerClient
from .tasks import list_tasks, register

__all__ = [
    "RemoteTaskError",
    "WorkerClient",
    "auth",
    "client",
    "list_tasks",
    "protocol",
    "register",
    "server",
    "tasks",
]
