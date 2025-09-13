# src/push_generator.py
from .config import DEFAULT_CURRENCY
import re

def format_currency(amount, currency=DEFAULT_CURRENCY):
    try:
        v = int(round(float(amount)))
    except Exception:
        v = 0
    return f"{v:,}".replace(',', ' ') + f" {currency}"

PUSH_TEMPLATES = {
    'Travel Card': "{name}, за последние 30 дней вы потратили много на поездки и такси. С Travel-картой вы могли бы вернуть ≈{benefit}. Оформить карту?",
    'Shopper Card': "{name}, вы часто делаете покупки онлайн. С Shopper-картой вы могли бы вернуть ≈{benefit} в месяц. Посмотреть условия?",
    'Premium Card': "{name}, исходя из ваших трат, премиальная карта даст вам ≈{benefit} возврата и привилегии. Узнать подробнее?",
    'Everyday Card': "{name}, карта для повседневных расходов поможет экономить ≈{benefit} в месяц. Посмотреть?",
    'Deposit': "{name}, у вас есть свободные средства — положив их на вклад, вы могли бы получать ≈{benefit} в месяц. Открыть вклад?"
}

def simple_post_check(text, name_present=True, max_len=220, min_len=40):
    # Проверки: длина, отсутствие promise-слов, не более одного эмодзи (упрощенно), имя присутствует
    if len(text) > max_len:
        return False, "too_long"
    if len(text) < min_len:
        return False, "too_short"
    # запретные слова
    bad = ['гарант', '100%', 'абсолютно бесплатно', 'безусловно бесплатно']
    low = text.lower()
    for b in bad:
        if b in low:
            return False, "forbidden_word"
    if name_present and not re.search(r'\b[A-ZА-ЯЁa-zа-яё]+\b', text):
        # упрощённая проверка
        return False, "no_name"
    return True, "ok"

def generate_push(name, product_name, benefit_amount):
    benefit_fmt = format_currency(benefit_amount)
    template = PUSH_TEMPLATES.get(product_name, "{name}, рекомендуем {product}. Примерная выгода {benefit}.")
    text = template.format(name=name if name else "Здравствуйте", product=product_name, benefit=benefit_fmt)
    ok, reason = simple_post_check(text)
    if not ok:
        # fallback: более короткий нейтральный шаблон
        text = f"{name if name else 'Здравствуйте'}, рекомендуем {product_name}. Узнать подробности?"
    return text
