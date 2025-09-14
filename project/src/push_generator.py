# src/push_generator.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime
import math
import re

RU_MONTHS = [
    "январе","феврале","марте","апреле","мае","июне",
    "июле","августе","сентябре","октябре","ноябре","декабре"
]

CURRENCY_SYMBOLS = {
    "KZT": "₸",
    "USD": "$",
    "EUR": "€",
    "RUB": "₽",
    "GBP": "£",
}

def fmt_money(val: float, cur: str = "KZT") -> str:
    """2 490 ₸ ; decimal comma; thousands with space; currency separated by space."""
    if val is None or math.isnan(val):
        return ""
    decimals = 0 if cur == "KZT" else 2
    s = f"{val:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", " ")
    symbol = CURRENCY_SYMBOLS.get(cur, cur)
    return f"{s} {symbol}"

def _trim_220(s: str) -> str:
    if len(s) <= 220:
        return s
    cut = s.rfind(". ", 0, 220)
    if cut == -1:
        cut = s.rfind(" ", 0, 220)
    return s[:cut].rstrip(" .") + "."

def simple_post_check(push_text: str) -> bool:
    """Проверка: 180–220 символов, точка в конце, без CAPS, ≤1 emoji."""
    length_ok = 180 <= len(push_text) <= 220
    ends_with_period = push_text.strip().endswith('.')
    caps_ok = not bool(re.search(r'[A-Z]{2,}', push_text))
    emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', push_text))
    emoji_ok = emoji_count <= 1
    return length_ok and ends_with_period and caps_ok and emoji_ok

def generate_push(name: str, product: str, est_benefit: float = 0.0,
                  *, currency: str = "KZT", context: dict | None = None) -> str:
    """
    1) Персональный контекст
    2) Польза/объяснение
    3) CTA (2–4 слова)
    TOV: на равных, без воды, ≤1 эмодзи, без CAPS, 180–220 символов
    """
    name = (name or "").strip()
    name = name.split()[0] if name else "Вы"
    month_phrase = RU_MONTHS[datetime.now().month - 1]
    benefit_text = fmt_money(max(0, est_benefit), currency)
    fx_curr = (context or {}).get("fx_curr", "USD")

    # Шаблоны под русские имена продуктов
    if product == "Карта для путешествий":
        base = (f"{name}, в {month_phrase} много поездок и такси. "
                f"С картой для путешествий часть расходов вернулась бы — около {benefit_text} в месяц. Оформить карту.")
    elif product == "Премиальная карта":
        base = (f"{name}, видно крупный остаток и траты в ресторанах/красоте. "
                f"Премиальная карта даст повышенный кешбэк и бесплатные снятия — до {benefit_text} в месяц. Оформить сейчас.")
    elif product == "Кредитная карта":
        base = (f"{name}, ваши топ-категории трат дают возможность вернуть до {benefit_text} в месяц. "
                "Кредитная карта — до 10% кешбэка в любимых категориях и льготный период. Оформить?")
    elif product == "Обмен валют":
        base = (f"{name}, вы часто платите в {fx_curr}. В приложении — выгодный обмен и авто-покупка по целевому курсу. Настроить обмен.")
    elif product.startswith("Депозит"):
        base = (f"{name}, у вас есть свободные средства. "
                f"Разместите их на {product.lower()} и получайте ≈{benefit_text} в месяц. Открыть вклад.")
    elif product == "Инвестиции":
        base = (f"{name}, попробуйте инвестиции с низким порогом входа и без комиссий на старт. Открыть счёт.")
    elif product == "Золотые слитки":
        base = (f"{name}, хотите диверсифицировать? Золотые слитки — защита стоимости. Посмотреть условия?")
    elif product == "Кредит наличными":
        base = (f"{name}, если нужен запас на крупные траты — можно оформить кредит наличными с гибкими условиями. Узнать лимит?")
    else:
        base = (f"{name}, рекомендуем {product}. Посмотреть?")

    push_text = _trim_220(base)
    if not simple_post_check(push_text):
        push_text = f"{name}, основываясь на ваших тратах, рекомендуем: {product}. Узнать подробнее?"
    return push_text
