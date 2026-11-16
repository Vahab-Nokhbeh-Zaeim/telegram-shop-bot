"""Every text the bot sends, in one place (Persian).

To support another language, translate the values in TEXT and keep the keys.
Messages are sent with Telegram's HTML parse mode, so literal < and > are escaped.
"""

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa_number(value: int) -> str:
    """Write a number with Persian digits: 1001 -> ۱۰۰۱."""
    return str(value).translate(PERSIAN_DIGITS)


def format_price(amount: int) -> str:
    """850000 -> ۸۵۰٬۰۰۰ تومان"""
    return f"{amount:,}".replace(",", "٬").translate(PERSIAN_DIGITS) + " تومان"


DEFAULT_CATEGORY = "سایر"

TEXT = {
    "start": (
        "سلام {name}! 👋 به فروشگاه خوش آمدی.\n\n"
        "/catalog – دیدن همه محصولات\n"
        "/categories – دیدن دسته‌بندی‌ها\n"
        "/search &lt;نام&gt; – جستجوی محصول\n"
        "/cart – سبد خرید\n"
        "/checkout – ثبت سفارش\n"
        "/clear – خالی کردن سبد خرید"
    ),
    "default_name": "دوست عزیز",
    "catalog_title": "محصولات",
    "product_line": "• {name} – {status}",
    "out_of_stock": "ناموجود",
    "add_button": "➕ افزودن {name}",
    "search_usage": "نحوه استفاده: /search ماوس",
    "search_none": "محصولی با «{query}» پیدا نشد.",
    "search_title": "نتایج جستجوی «{query}»",
    "categories_title": "یک دسته‌بندی را انتخاب کن",
    "categories_empty": "هنوز محصولی ثبت نشده است.",
    "category_button": "{name} ({count})",
    "category_missing": "این دسته‌بندی دیگر وجود ندارد. دوباره /categories را بفرست.",
    "cart_title": "سبد خرید شما",
    "cart_empty": "سبد خرید شما خالی است. با /catalog محصول اضافه کن.",
    "cart_line": "• {name} × {quantity} = {total}",
    "cart_total": "\n<b>جمع کل: {total}</b>",
    "checkout_empty": "سبد خرید شما خالی است.",
    "order_placed": "✅ سفارش شماره {order_id} ثبت شد!\n\n{summary}\n\nبه‌زودی با شما تماس می‌گیریم.",
    "admin_new_order": "🛒 سفارش جدید شماره {order_id} از {customer}\n\n{summary}",
    "cleared": "سبد خرید شما خالی شد.",
    "added": "{name} به سبد خرید اضافه شد",
    "unavailable": "متأسفانه این محصول موجود نیست",
    "unknown": "متوجه نشدم. برای دیدن دستورها /start را بفرست.",
}


def t(key: str, **values: object) -> str:
    """Return the text for a key, filled with the given values."""
    return TEXT[key].format(**values)
