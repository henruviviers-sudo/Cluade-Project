"""Run a compushare worker on this machine.

Typical usage on the desktop::

    python worker.py --token mysharedsecret

The worker listens on 0.0.0.0:8765 by default and uses every CPU core.  Use
``python genkey.py`` to generate a strong random token.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from compushare import server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="compushare worker - share processing power over the network",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind address (default: 0.0.0.0, i.e. all interfaces)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="TCP port to listen on (default: 8765)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("COMPUSHARE_TOKEN"),
        help="Shared-secret token (defaults to $COMPUSHARE_TOKEN)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes/threads (default: CPU count)",
    )
    parser.add_argument(
        "--threads",
        action="store_true",
        help="Use a thread pool instead of a process pool (avoids the GIL only "
        "for I/O-bound tasks; use the default process pool for CPU-bound work).",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )

    if not args.token:
        parser.error("--token (or the COMPUSHARE_TOKEN environment variable) is required")

    server.serve(
        host=args.host,
        port=args.port,
        token=args.token,
        max_workers=args.workers,
        use_processes=not args.threads,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
