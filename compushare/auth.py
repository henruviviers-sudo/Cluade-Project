"""Shared-secret HMAC challenge/response authentication.

The worker sends a random challenge in its `hello` message; the client signs
it with HMAC-SHA256 using the shared token and sends the signature back.  The
worker verifies it with `hmac.compare_digest` to avoid timing leaks.

This is intentionally simple - it proves both ends know the same secret
without ever transmitting it - but the underlying transport is plain TCP.  If
you are running across an untrusted network, tunnel compushare over SSH or a
WireGuard link.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_token(nbytes: int = 32) -> str:
    """Generate a fresh random shared secret as a hex string."""
    return secrets.token_hex(nbytes)


def make_challenge() -> str:
    """Generate a random challenge nonce as a hex string."""
    return secrets.token_hex(16)


def sign_challenge(token: str, challenge: str) -> str:
    """Sign *challenge* with *token* using HMAC-SHA256."""
    return hmac.new(
        token.encode("utf-8"),
        challenge.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_signature(token: str, challenge: str, signature: str) -> bool:
    """Constant-time check that *signature* matches sign_challenge(token, challenge)."""
    expected = sign_challenge(token, challenge)
    return hmac.compare_digest(expected, signature)
