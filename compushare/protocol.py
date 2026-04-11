"""Length-prefixed JSON message framing used by compushare."""

from __future__ import annotations

import json
import socket
import struct
from typing import Any, Dict

# Hard cap on a single message so a malicious or buggy peer can't make us
# allocate gigabytes.  64 MiB is plenty for normal task payloads.
MAX_MESSAGE_SIZE = 64 * 1024 * 1024


class ProtocolError(Exception):
    """Raised when the wire protocol is violated."""


def send_message(sock: socket.socket, message: Dict[str, Any]) -> None:
    """Serialize *message* as JSON and send it with a 4-byte length prefix."""
    payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_MESSAGE_SIZE:
        raise ProtocolError(
            f"Outgoing message too large: {len(payload)} bytes "
            f"(max {MAX_MESSAGE_SIZE})"
        )
    header = struct.pack(">I", len(payload))
    sock.sendall(header + payload)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ProtocolError("Connection closed by peer")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_message(sock: socket.socket) -> Dict[str, Any]:
    """Read a single length-prefixed JSON message from *sock*."""
    header = _recv_exact(sock, 4)
    (length,) = struct.unpack(">I", header)
    if length > MAX_MESSAGE_SIZE:
        raise ProtocolError(
            f"Incoming message too large: {length} bytes (max {MAX_MESSAGE_SIZE})"
        )
    payload = _recv_exact(sock, length)
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"Malformed message payload: {exc}") from exc
    if not isinstance(decoded, dict):
        raise ProtocolError(f"Expected JSON object, got {type(decoded).__name__}")
    return decoded
