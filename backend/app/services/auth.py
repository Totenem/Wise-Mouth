"""Minimal auth: scrypt password hashes + stateless HMAC-signed bearer tokens (stdlib only)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import secrets
import time

from ..config import settings

log = logging.getLogger("wisemouth.auth")

TOKEN_TTL_S = 30 * 24 * 3600
_secret: bytes | None = None


def _key() -> bytes:
    global _secret
    if _secret is None:
        if settings.auth_secret:
            _secret = settings.auth_secret.encode()
        else:
            log.warning("AUTH_SECRET not set: using a random key, logins will not survive a restart")
            _secret = secrets.token_bytes(32)
    return _secret


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    h = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}${h.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
        h = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
        return hmac.compare_digest(h.hex(), hash_hex)
    except ValueError:
        return False


def _sign(payload: str) -> str:
    return hmac.new(_key(), payload.encode(), hashlib.sha256).hexdigest()


def make_token(user_id: str) -> str:
    payload = f"{user_id}.{int(time.time()) + TOKEN_TTL_S}"
    return base64.urlsafe_b64encode(f"{payload}.{_sign(payload)}".encode()).decode()


def user_id_from_token(token: str | None) -> str | None:
    if not token:
        return None
    try:
        uid, exp, sig = base64.urlsafe_b64decode(token.encode()).decode().rsplit(".", 2)
        if not hmac.compare_digest(sig, _sign(f"{uid}.{exp}")) or int(exp) < time.time():
            return None
        return uid
    except (ValueError, UnicodeDecodeError):
        return None
