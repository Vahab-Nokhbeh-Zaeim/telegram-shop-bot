"""Minimal Telegram Bot API client built on the standard library."""

import json
import urllib.request
from typing import Any


class TelegramError(RuntimeError):
    """Raised when the Telegram API returns an error."""


class TelegramAPI:
    def __init__(self, token: str, timeout: int = 35) -> None:
        if not token:
            raise ValueError("A bot token is required (set BOT_TOKEN)")
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.timeout = timeout

    def call(self, method: str, **params: Any) -> Any:
        payload = json.dumps(params).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + method,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        if not body.get("ok"):
            raise TelegramError(body.get("description", "Unknown Telegram error"))
        return body["result"]

    def get_updates(self, offset: int | None = None, timeout: int = 30) -> list[dict]:
        params: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        return self.call("getUpdates", **params)

    def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None) -> Any:
        params: dict[str, Any] = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            params["reply_markup"] = reply_markup
        return self.call("sendMessage", **params)

    def answer_callback(self, callback_id: str, text: str = "") -> Any:
        return self.call("answerCallbackQuery", callback_query_id=callback_id, text=text)
