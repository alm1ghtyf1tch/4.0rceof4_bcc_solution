# src/local_refine.py
import requests

BASE_URL = "http://localhost:1234"  # адрес из LM Studio
MODEL_NAME = "openchat-3.5-1210"    # имя модели в LM Studio

def refine_push(name, product, benefit_str, reasons=""):
    prompt = (
        f"Сгенерируй короткий пуш-текст (180–220 символов) "
        f"для клиента по имени {name}. "
        f"Предлагаемый продукт: {product}, выгода: {benefit_str}. "
        f"Ключевые категории: {reasons}. "
        "Тон — дружелюбный, ясный, 1 мысль, 1 CTA, не более 1 эмодзи, "
        "без CAPS, заканчивай точкой."
    )

    resp = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Ты создаёшь персонализированные пуш-тексты для клиентов банка."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    },
    timeout=60
    )

    data = resp.json()
    print("[DEBUG LMStudio]", data)  # <<< добавили
    return data["choices"][0]["message"]["content"].strip()
