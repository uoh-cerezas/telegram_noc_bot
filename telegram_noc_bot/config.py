from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mode: str = os.getenv("TELEGRAM_MODE", "mock").lower()
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    noc_api_url: str = os.getenv("NOC_API_URL", "http://127.0.0.1:8060").rstrip("/")
    request_timeout: float = float(os.getenv("NOC_REQUEST_TIMEOUT", "10"))
    allowed_user_ids: frozenset[int] = frozenset(
        int(value.strip())
        for value in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",")
        if value.strip().isdigit()
    )
