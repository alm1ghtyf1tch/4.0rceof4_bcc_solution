# src/llm_refiner.py
import requests
import json

BASE_URL = "http://localhost:1234"     # LM Studio адрес
MODEL_NAME = "openchat-3.5-1210"       # точное имя модели в LM Studio
REQUEST_TIMEOUT = 30

def _safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return None

def _debug_print(prefix, resp):
    try:
        j = _safe_json(resp)
        print(f"[llm_refiner DEBUG] {prefix} status={resp.status_code}")
        if j is not None:
            s = json.dumps(j, ensure_ascii=False)
            print(f"[llm_refiner DEBUG] json: {s[:2000]}")
        else:
            print(f"[llm_refiner DEBUG] text: {resp.text[:2000]}")
    except Exception as e:
        print(f"[llm_refiner DEBUG] error printing response: {e}")

def refine_push(name: str,
                product: str,
                benefit_str: str = "",
                status: str = "",
                archetype: str = "",
                cats: str = "") -> str:
    """
    Генератор персонализированного пуша через LM Studio.
    """
    name = name or ""
    # жёстко задаём правила для модели
    prompt = (
    f"Сгенерируй персонализированный push (180–220 символов) "
    f"для клиента по имени {name}. Продукт: {product}. Выгода: {benefit_str}. "
    f"Статус клиента: {status}. Архетип: {archetype}. Категории: {cats}.\n\n"
    "Требования:\n"
    "- Упомяни имя клиента или статус, но не говори «станьте премиальным», если он уже премиальный.\n"
    "- 1 мысль (главное преимущество) + 1 CTA (короткий, 2–4 слова, например «Активируйте карту»).\n"
    "- Избегай перечислений более чем двух элементов.\n"
    "- Тон: деловой, уверенный, без CAPS.\n"
    "- Не начинай с «Здравствуйте», «Приветствуем», «У вас», «Клиент».\n"
    "- Не используй обращения вроде «Сэр», «Вам известен…», «Знаете ли вы…».\n"
    "- Если клиент премиальный, пиши «Как премиальный клиент…» или «Ваш статус премиальный…».\n"
    "- Макс 1 эмодзи. Выведи только готовый текст (русский), без лишних вводных слов."
    )

    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "Ты маркетолог банка, пишешь лаконичные push-уведомления."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 220
        }
        url = f"{BASE_URL}/v1/chat/completions"
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        data = resp.json()
        _debug_print("chat response", resp)
        if isinstance(data, dict) and "choices" in data and len(data["choices"])>0:
            ch0 = data["choices"][0]
            if "message" in ch0 and isinstance(ch0["message"], dict) and "content" in ch0["message"]:
                return ch0["message"]["content"].strip()
            if "text" in ch0:
                return ch0["text"].strip()
    except Exception as e:
        print(f"[llm_refiner] Exception: {e}")

    fallback = f"{product}: выгода {benefit_str}. Подробнее в приложении."
    return fallback

