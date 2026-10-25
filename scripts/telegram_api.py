"""Small standard-library client for Telegram Bot API sendMessage."""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_CHANNEL_ID = "@WafarnalakMasr"


def send_message(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN. Add it as a GitHub Actions repository secret."
        )

    chat_id = os.environ.get("TELEGRAM_CHANNEL_ID", DEFAULT_CHANNEL_ID).strip()
    if not chat_id:
        raise RuntimeError("TELEGRAM_CHANNEL_ID is empty.")

    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(
            f"Telegram returned HTTP {exc.code}: {detail or 'no response body'}"
        ) from None
    except URLError as exc:
        raise RuntimeError(f"Could not reach Telegram: {exc.reason}") from None
    except TimeoutError:
        raise RuntimeError("Telegram request timed out.") from None

    if not result.get("ok"):
        description = result.get("description", "Unknown Telegram API error")
        raise RuntimeError(f"Telegram rejected the message: {description}")
