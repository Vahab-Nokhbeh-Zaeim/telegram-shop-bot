"""Render docs/preview.html: a Telegram-style chat built from the bot's real replies.

Usage:
    python tools/render_preview.py
Then open docs/preview.html in a browser (or take a screenshot of it for the README).
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shopbot.catalog import Catalog  # noqa: E402
from shopbot.handlers import ShopBot  # noqa: E402

CHAT_ID = 7
USER = {"first_name": "وهاب", "username": "vahab"}


def text_update(text: str) -> dict:
    return {"message": {"chat": {"id": CHAT_ID}, "from": USER, "text": text}}


def button_update(data: str) -> dict:
    return {"callback_query": {"id": "q", "data": data, "message": {"chat": {"id": CHAT_ID}}}}


def to_html(telegram_html: str) -> str:
    """Telegram HTML is already escaped; keep <b> and turn new lines into <br>."""
    allowed = re.sub(r"<(?!/?b>)", "&lt;", telegram_html)
    return allowed.replace("\n", "<br>")


def bubble(text: str, side: str, buttons: list[str] | None = None) -> str:
    rows = "".join(f'<div class="btn">{html.escape(b)}</div>' for b in buttons or [])
    keyboard = f'<div class="keyboard">{rows}</div>' if rows else ""
    return f'<div class="msg {side}"><div class="bubble">{text}</div>{keyboard}</div>'


def toast(text: str) -> str:
    return f'<div class="toast">{html.escape(text)}</div>'


def main() -> None:
    bot = ShopBot(Catalog.from_file(ROOT / "data" / "products.json"), admin_chat_id=1)
    parts = []

    def user_says(text: str) -> None:
        parts.append(bubble(html.escape(text), "user"))
        for action in bot.handle(text_update(text)):
            if action.params.get("chat_id") != CHAT_ID:
                continue
            keyboard = action.params.get("reply_markup", {}).get("inline_keyboard", [])
            parts.append(bubble(to_html(action.params["text"]), "bot", [row[0]["text"] for row in keyboard]))

    def user_taps(data: str) -> None:
        for action in bot.handle(button_update(data)):
            if action.method == "answer_callback":
                if action.params.get("text"):
                    parts.append(toast(action.params["text"]))
            else:
                keyboard = action.params.get("reply_markup", {}).get("inline_keyboard", [])
                parts.append(bubble(to_html(action.params["text"]), "bot", [row[0]["text"] for row in keyboard]))

    user_says("/categories")
    user_taps("cat:1")
    user_taps("add:headset")
    user_says("/search ماوس")
    user_taps("add:mouse")
    user_says("/checkout")

    page = TEMPLATE.replace("{{messages}}", "\n".join(parts))
    out = ROOT / "docs" / "preview.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {out}")


TEMPLATE = """<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<title>Telegram Shop Bot preview</title>
<style>
  html, body { margin: 0; background: #0e1621; font-family: Tahoma, "Segoe UI", sans-serif; }
  body { direction: ltr; }
  .phone { direction: rtl; width: 420px; background: #0e1621; padding-bottom: 16px; }
  .top { background: #17212b; color: #fff; padding: 14px 18px; display: flex; gap: 12px; align-items: center; }
  .avatar { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #5eb5f7, #2b8ae2);
            display: grid; place-items: center; font-weight: bold; }
  .top small { display: block; color: #7f91a4; font-size: 12px; }
  .chat { padding: 12px 12px 0; display: flex; flex-direction: column; gap: 8px; }
  .msg { display: flex; flex-direction: column; max-width: 82%; }
  .msg.user { align-self: flex-end; }
  .msg.bot { align-self: flex-start; }
  .bubble { padding: 8px 12px; border-radius: 14px; color: #fff; font-size: 14px; line-height: 1.7; }
  .user .bubble { background: #2b5278; border-bottom-left-radius: 4px; direction: ltr; text-align: left; }
  .bot .bubble { background: #182533; border-bottom-right-radius: 4px; }
  .keyboard { display: grid; gap: 4px; margin-top: 4px; }
  .btn { background: rgba(255,255,255,.08); color: #fff; text-align: center; padding: 7px; border-radius: 8px; font-size: 13px; }
  .toast { align-self: center; background: rgba(0,0,0,.55); color: #fff; font-size: 12px; padding: 4px 12px; border-radius: 12px; }
</style>
</head>
<body>
<div class="phone">
  <div class="top"><div class="avatar">🛒</div><div>فروشگاه<small>bot</small></div></div>
  <div class="chat">
{{messages}}
  </div>
</div>
</body>
</html>
"""

if __name__ == "__main__":
    main()
