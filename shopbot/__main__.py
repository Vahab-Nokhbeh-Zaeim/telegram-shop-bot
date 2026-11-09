"""Run the bot with long polling: python -m shopbot"""

import logging
import os
import time
from pathlib import Path

from .api import TelegramAPI, TelegramError
from .catalog import Catalog
from .handlers import ShopBot

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("shopbot")

DEFAULT_CATALOG = Path(__file__).resolve().parent.parent / "data" / "products.json"


def main() -> None:
    token = os.environ.get("BOT_TOKEN", "")
    admin = os.environ.get("ADMIN_CHAT_ID")
    catalog_path = os.environ.get("CATALOG_PATH", DEFAULT_CATALOG)

    api = TelegramAPI(token)
    bot = ShopBot(Catalog.from_file(catalog_path), int(admin) if admin else None)
    offset = None
    log.info("Bot started, waiting for messages")
    while True:
        try:
            for update in api.get_updates(offset):
                offset = update["update_id"] + 1
                for action in bot.handle(update):
                    getattr(api, action.method)(**action.params)
        except (TelegramError, OSError) as error:
            log.warning("Telegram request failed: %s", error)
            time.sleep(3)


if __name__ == "__main__":
    main()
