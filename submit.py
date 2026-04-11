"""Submit a single task to a compushare worker.

Examples::

    python submit.py --host desktop.local --token mysecret --ping
    python submit.py --host desktop.local --token mysecret --list
    python submit.py --host desktop.local --token mysecret count_primes 1000000
    python submit.py --host desktop.local --token mysecret sum_range 0 1000000
    python submit.py --host desktop.local --token mysecret echo '"hello"'

Positional arguments and ``--kwarg KEY=VALUE`` values are parsed as JSON when
possible (so ``42`` becomes an int, ``"foo"`` becomes a string, ``[1,2,3]``
becomes a list); strings that fail to parse are sent as-is.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from compushare.client import RemoteTaskError, WorkerClient


def parse_value(s: str):
    """Try JSON-decoding *s*; fall back to the raw string on failure."""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return s


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Submit a task to a compushare worker",
    )
    parser.add_argument("--host", required=True, help="Worker hostname or IP")
    parser.add_argument(
        "--port", type=int, default=8765, help="Worker port (default: 8765)"
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("COMPUSHARE_TOKEN"),
        help="Shared-secret token (defaults to $COMPUSHARE_TOKEN)",
    )
    parser.add_argument(
        "--list", action="store_true", help="List the tasks the worker exposes"
    )
    parser.add_argument(
        "--ping", action="store_true", help="Round-trip a ping and exit"
    )
    parser.add_argument("task", nargs="?", help="Name of the task to invoke")
    parser.add_argument(
        "args",
        nargs="*",
        help="Positional arguments to the task (parsed as JSON when possible)",
    )
    parser.add_argument(
        "--kwarg",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Keyword argument (repeatable; VALUE is parsed as JSON when possible)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Server-side wall-clock timeout for the task in seconds",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print remote tracebacks on error"
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.DEBUG if args.verbose else logging.WARNING,
    )

    if not args.token:
        parser.error(
            "--token (or the COMPUSHARE_TOKEN environment variable) is required"
        )
    if not (args.task or args.list or args.ping):
        parser.error("provide a task name, or use --list / --ping")

    client = WorkerClient(args.host, args.port, args.token)
    try:
        client.connect()
    except OSError as exc:
        print(f"Failed to connect to {args.host}:{args.port}: {exc}", file=sys.stderr)
        return 1
    except RemoteTaskError as exc:
        print(f"Handshake failed: {exc}", file=sys.stderr)
        return 1

    try:
        if args.ping:
            t = client.ping()
            print(f"pong @ {t}")
            return 0
        if args.list:
            for name in client.list_tasks():
                print(name)
            return 0

        positional = [parse_value(a) for a in args.args]
        kwargs = {}
        for kv in args.kwarg:
            if "=" not in kv:
                parser.error(f"invalid --kwarg {kv!r} (expected KEY=VALUE)")
            key, _, raw = kv.partition("=")
            kwargs[key] = parse_value(raw)

        try:
            result = client.call(
                args.task, *positional, timeout=args.timeout, **kwargs
            )
        except RemoteTaskError as exc:
            print(
                f"Task error ({exc.error_type or 'RemoteTaskError'}): {exc}",
                file=sys.stderr,
            )
            if args.verbose and exc.traceback:
                print(exc.traceback, file=sys.stderr)
            return 2

        print(json.dumps(result, indent=2, default=str))
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
