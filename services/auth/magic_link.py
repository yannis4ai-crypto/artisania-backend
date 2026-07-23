import hashlib
import hmac
import time

from config import settings


def generate_token(email: str) -> str:
    issued_at = str(int(time.time()))
    payload = f"{email}:{issued_at}"
    signature = hmac.new(
        settings.magic_link_secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload}:{signature}"


def verify_token(token: str) -> str | None:
    try:
        email, issued_at, signature = token.split(":")
    except ValueError:
        return None
    payload = f"{email}:{issued_at}"
    expected = hmac.new(
        settings.magic_link_secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    if time.time() - int(issued_at) > settings.magic_link_ttl_minutes * 60:
        return None
    return email
