# src/local_refine.py
import requests
from .push_generator import simple_post_check

# Адрес локального API LM Studio / Ollama
# Проверь в LM Studio или Ollama какой порт. Чаще всего:
# Ollama: http://localhost:11434/api/generate
# LM Studio: http://localhost:1234/v1/completions
API_URL = "http://localhost:11434/api/generate"  # подстрой под свой

MODEL_NAME = "mistral"  # подстрой под модель, которую ты скачал

def refine_push(name, product, benefit_str, reasons):
    """
    Формирует запрос к локальной LLM (LM Studio/Ollama) и возвращает пуш.
    """
    prompt = (f"Имя: {name}\nПродукт: {product}\nВыгода: {benefit_str}\n"
              f"Расходы: {reasons}\n\nСформулируй 1 пуш-уведомление на русском (до 160 символов).")

    # Пример для Ollama API (stream=False)
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    resp = requests.post(API_URL, json=payload)
    data = resp.json()
    text = data.get('response') or data.get('choices', [{}])[0].get('text', '')
    text = (text or '').strip()

    ok, reason = simple_post_check(text)
    if not ok:
        text = f"{name if name else 'Здравствуйте'}, рекомендуем {product}. Выгода {benefit_str}"
    return text
