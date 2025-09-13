# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime
import math

# Helpers for formatting under rubric
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
    # round to 0 decimals for KZT; 2 for USD/EUR
    decimals = 0 if cur == "KZT" else 2
    s = f"{val:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", " ")
    symbol = CURRENCY_SYMBOLS.get(cur, cur)
    return f"{s} {symbol}"

def _trim_220(s: str) -> str:
    if len(s) <= 220:
        return s
    # prefer cutting at sentence boundary
    cut = s.rfind(". ", 0, 220)
    if cut == -1:
        cut = s.rfind(" ", 0, 220)
    return s[:cut].rstrip(" .") + "."

def generate_push(name: str, product: str, est_benefit: float = 0.0, *, currency: str = "KZT", context: dict | None = None) -> str:
    """
    Rubric:
      1) Персональный контекст
      2) Польза/объяснение
      3) Чёткий CTA (2–4 слова)
      TOV: на равных, без воды, 0–1 эмодзи, без CAPS, 180–220 символов
    """
    name = (name or "").split()[0] or "У вас"
    month_phrase = RU_MONTHS[datetime.now().month - 1]
    benefit_text = fmt_money(max(0, est_benefit), currency)

    # Context hints
    fx_curr = (context or {}).get("fx_curr", "USD")
    cats = (context or {}).get("cats", [])

    if product == "Travel Card":
        base = (f"{name}, в {month_phrase} много поездок и такси. С тревел-картой часть расходов вернулась бы кешбэком"
                + (f" — примерно {benefit_text} в месяц" if benefit_text else "") +
                ". Оформить карту.")
    elif product == "Premium Card":
        base = (f"{name}, видно крупный остаток и траты в ресторанах. Премиальная карта даст повышенный кешбэк и бесплатные снятия"
                + (f" — до {benefit_text} в месяц" if benefit_text else "") +
                ". Оформить сейчас.")
    elif product == "Shopper Card":
        base = (f"{name}, у вас много онлайн-покупок и продуктовых трат. Shopper вернёт часть расходов кешбэком"
                + (f" — до {benefit_text} в месяц" if benefit_text else "") +
                ". Оформить карту.")
    elif product == "Everyday Card":
        base = (f"{name}, повседневные траты можно делать выгоднее. Everyday даёт простой кешбэк на еду и коммунальные"
                + (f" — до {benefit_text} в месяц" if benefit_text else "") +
                ". Подключить карту.")
    elif product == "Deposit":
        base = (f"{name}, остаются свободные средства. Разместите их на вкладе — удобно копить и получать вознаграждение"
                + (f" — около {benefit_text} в месяц" if benefit_text else "") +
                ". Открыть вклад.")
    else:
        # FX / multi-currency (fallback)
        base = (f"{name}, вы часто платите в {fx_curr}. В приложении — выгодный обмен и авто-покупка по целевому курсу. "
                "Настроить обмен.")

    return _trim_220(base)
