# Telegram Shop Bot

A lightweight Telegram bot for small online shops. Customers browse products, add them to a cart with inline buttons and place orders — and the shop owner gets a notification for every new order.

Built with **pure Python 3.12** and the Telegram Bot API, with **no third-party dependencies**.

![tests](https://github.com/Vahab-Nokhbeh-Zaeim/telegram-shop-bot/actions/workflows/tests.yml/badge.svg)

## Features

- Product catalog loaded from a JSON file
- Inline "Add to cart" buttons for products in stock
- Product search by name
- Per-user carts with stock validation
- Checkout with order numbers and an order summary
- Order notifications sent to an admin chat
- Long polling with automatic retry on network errors
- Business logic separated from the API layer and covered by unit tests

## Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and list of commands |
| `/catalog` | Browse products and add them to the cart |
| `/search <name>` | Find products by name (case-insensitive) |
| `/cart` | View the cart and total price |
| `/checkout` | Place the order |
| `/clear` | Empty the cart |

## Getting Started

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Clone the repository and set the environment variables:

```bash
git clone https://github.com/Vahab-Nokhbeh-Zaeim/telegram-shop-bot.git
cd telegram-shop-bot
export BOT_TOKEN="your-token"
export ADMIN_CHAT_ID="your-chat-id"   # optional
```

On Windows PowerShell use `$env:BOT_TOKEN="your-token"`.

3. Run the bot:

```bash
python -m shopbot
```

Products live in `data/products.json`; edit it or point `CATALOG_PATH` to your own file.

## Project Structure

```
shopbot/
  api.py        Telegram Bot API client (urllib)
  catalog.py    Product model and catalog loader
  cart.py       Per-chat carts and price formatting
  handlers.py   Commands and callbacks -> actions
  __main__.py   Long polling loop
data/products.json
tests/          Unit tests
```

## Running Tests

```bash
python -m unittest discover -s tests -v
```

## License

[MIT](LICENSE) © Vahab Nokhbeh Zaeim
