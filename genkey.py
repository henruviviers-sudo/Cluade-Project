"""Print a fresh random shared-secret token suitable for COMPUSHARE_TOKEN."""

from __future__ import annotations

import argparse
import sys

from compushare.auth import generate_token


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bytes",
        type=int,
        default=32,
        help="Number of random bytes (default: 32, yielding a 64-char hex token)",
    )
    args = parser.parse_args(argv)
    print(generate_token(args.bytes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
