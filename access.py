"""Owner-only access control for the Telegram bot (fail-closed).

ALLOWED_USER_IDS is a comma-separated list of numeric Telegram user IDs.
If it is unset/empty/invalid, nobody is authorized.
"""
import os
from typing import Optional, Set


def allowed_user_ids(raw: Optional[str] = None) -> Set[int]:
    raw = os.getenv("ALLOWED_USER_IDS", "") if raw is None else raw
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.add(int(part))
    return ids


def is_authorized(user_id: Optional[int], raw: Optional[str] = None) -> bool:
    if user_id is None:
        return False
    return user_id in allowed_user_ids(raw)
