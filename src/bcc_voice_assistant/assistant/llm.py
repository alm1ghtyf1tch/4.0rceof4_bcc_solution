"""
Provider-agnostic tiny LLM client:
- If Ollama is running locally (default), we use it (FREE).
- Otherwise, we fall back to a rule-based answer using knowledge.py.

Exported functions:
  chat(prompt, history) -> str
  extract_structured(prompt, schema_hint) -> dict | None
"""

from __future__ import annotations
import os, json, requests
from typing import List, Dict, Optional
from .knowledge import PRODUCT_SUMMARIES, TOV_HINT

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

def _ollama_available() -> bool:
    try:
        r = requests.get(OLLAMA_URL+"/api/tags", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False

SYSTEM = (
    "Ты – дружелюбный банковский ассистент. Общайся просто, доброжелательно, "
    "без жаргона и давления; обращайся на «вы». Отвечай кратко и по делу."
)

def _ollama_chat(prompt: str, history: List[Dict[str,str]]) -> str:
    msgs = [{"role":"system","content":SYSTEM}]
    msgs += history
    msgs.append({"role":"user","content":prompt})
    r = requests.post(OLLAMA_URL+"/api/chat", json={"model": OLLAMA_MODEL, "messages": msgs}, timeout=60)
    r.raise_for_status()
    return r.json().get("message", {}).get("content", "")

def _rule_based_answer(prompt: str) -> str:
    low = prompt.lower()

    def anyhit(keys): return any(k in low for k in keys)

    travel = ["travel","flight","hotel","taxi","uber","bolt","airport","путеш","ави","отел","такси"]
    dining = ["dining","restaurant","eat out","еда","ресторан","кафе","такси кешбэк","taxi"]
    online = ["online shopping","marketplace","amazon","aliexpress","ozon","wildberries","онлайн","market","shop"]
    fx     = ["usd","eur","exchange","fx","currency","валют","доллар","евро"]
    transfer=["transfer","wire","tuition","study fee","payment abroad","perevod","перевод","оплат","платеж"]
    deposit = ["deposit","vklad","вклад","накопит"]
    card    = ["card","new card","карта","оформить карту"]
    cashback= ["cashback","кешбэк","кэшбэк"]

    if anyhit(travel):  return "Часто путешествуете/такси? Подойдёт **Travel Card**: повышенный кешбэк в поездках и транспорте. Сравнить варианты?"
    if anyhit(dining):  return "Для ресторанов/еды: **Premium Card** (повышенный кешбэк) или **Everyday/Shopper**. Рассчитать выгоду по вашим тратам?"
    if anyhit(online):  return "Много онлайн-покупок? **Shopper Card** возвращает часть расходов на онлайн и продукты. Посмотреть условия?"
    if anyhit(fx):      return "Часто платите в USD/EUR? Нужен мультивалютный счёт/карта: меньше потерь на конвертации, авто-покупка по целевому курсу. Настроить?"
    if anyhit(transfer):return "Нужен перевод в валюте. Напишите сумму/валюту, получателя, банк, страну и назначение — заполню черновик заявления."
    if anyhit(deposit): return "Свободные средства? Вклад поможет копить и получать вознаграждение. Открыть вклад?"
    if anyhit(card) or anyhit(cashback):
        return "Подберу карту: Travel (путешествия/такси), Shopper (онлайн/еда), Premium (повышенный кешбэк), Everyday (повседневные). Что для вас важнее?"

    return "Готов помочь: подскажите, что именно хотите сделать (перевод, карта, вклад, обмен валюты и т.п.)."

def status():
    return {"ollama_ok": _ollama_available(), "url": OLLAMA_URL, "model": OLLAMA_MODEL}




def chat(prompt: str, history: List[Dict[str,str]]) -> str:
    if _ollama_available():
        try:
            return _ollama_chat(prompt, history)
        except Exception:
            pass
    return _rule_based_answer(prompt)

def extract_structured(prompt: str, schema_hint: str = "") -> Optional[Dict]:
    """
    Best-effort: ask the model to produce a tiny JSON with fields we care about.
    Falls back to None if no LLM.
    """
    if not _ollama_available():
        return None
    sys = SYSTEM + " Отвечай строго форматом JSON без комментариев."
    msgs = [{"role":"system","content":sys}, {"role":"user","content":f"Извлеки данные по схеме: {schema_hint}\nТекст: {prompt}"}]
    r = requests.post(OLLAMA_URL+"/api/chat", json={"model": OLLAMA_MODEL, "messages": msgs}, timeout=60)
    try:
        return json.loads(r.json().get("message", {}).get("content", "{}"))
    except Exception:
        return None
