"""
Simple slot filling for 'заявление на перевод в иностранной валюте':
We parse free text (ru/en) to extract: amount, currency, date, recipient, purpose, country, bank, iban/swift.

This is intentionally pragmatic: regex + small heuristics so it works even without an LLM.
If Ollama is available, llm.extract_structured() will refine.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from typing import Optional, Dict

CURRENCY_PAT = r"(USD|EUR|KZT|RUB|GBP|CNY|JPY|AED)"
AMOUNT_PAT = r"(?P<amount>\d{1,3}(?:[ \u00A0]?\d{3})*(?:[.,]\d{1,2})?)\s*(?P<cur>"+CURRENCY_PAT+r")"
DATE_PAT = r"(?:(?P<day>\d{1,2})[./-](?P<month>\d{1,2})[./-](?P<year>\d{2,4}))|(?:(?:сегодня|завтра))"
IBAN_PAT = r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}"
SWIFT_PAT = r"[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?"
ACC_PAT = r"(?:IBAN|iban|СЧЕТ|счёт|account)\s*[:\-]?\s*(?P<iban>"+IBAN_PAT+")"

@dataclass
class TransferForm:
    payer_fullname: Optional[str] = None
    payer_account: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    beneficiary_name: Optional[str] = None
    beneficiary_bank: Optional[str] = None
    beneficiary_country: Optional[str] = None
    beneficiary_account_iban: Optional[str] = None
    beneficiary_swift: Optional[str] = None
    purpose: Optional[str] = None
    execution_date: Optional[str] = None  # dd.mm.yyyy or words

    def to_dict(self) -> Dict:
        return asdict(self)

def _parse_amount_currency(text: str):
    m = re.search(AMOUNT_PAT, text, re.I)
    if not m: return None, None
    amt = m.group("amount").replace(" ", "").replace("\u00A0","").replace(",", ".")
    try:
        return float(amt), m.group("cur").upper()
    except:
        return None, m.group("cur").upper()

def _parse_date(text: str):
    m = re.search(DATE_PAT, text, re.I)
    if not m: return None
    if m.group("day"):
        day = int(m.group("day")); mon = int(m.group("month")); year = int(m.group("year"))
        if year < 100: year += 2000
        return f"{day:02d}.{mon:02d}.{year:04d}"
    return m.group(0).lower()  # 'сегодня'/'завтра'

def _parse_iban(text: str):
    m = re.search(ACC_PAT, text, re.I)
    if m: return m.group("iban")
    m = re.search(IBAN_PAT, text, re.I)
    return m.group(0) if m else None

def _parse_swift(text: str):
    m = re.search(SWIFT_PAT, text, re.I)
    return m.group(0) if m else None

def heuristic_fill(form: TransferForm, text: str) -> TransferForm:
    # Amount & currency
    amt, cur = _parse_amount_currency(text)
    form.amount = form.amount or amt
    form.currency = form.currency or cur

    # Date
    dt = _parse_date(text)
    form.execution_date = form.execution_date or dt

    # IBAN/SWIFT
    form.beneficiary_account_iban = form.beneficiary_account_iban or _parse_iban(text)
    form.beneficiary_swift = form.beneficiary_swift or _parse_swift(text)

    # Beneficiary name/bank/country/purpose – naive cues
    m = re.search(r"(получател[ья]|бенефициар)\s*[:\-]?\s*([^\n,.;]+)", text, re.I)
    if m: form.beneficiary_name = form.beneficiary_name or m.group(2).strip()

    m = re.search(r"(банк|bank)\s*[:\-]?\s*([^\n,.;]+)", text, re.I)
    if m: form.beneficiary_bank = form.beneficiary_bank or m.group(2).strip()

    m = re.search(r"(страна|country)\s*[:\-]?\s*([^\n,.;]+)", text, re.I)
    if m: form.beneficiary_country = form.beneficiary_country or m.group(2).strip()

    m = re.search(r"(назначение|purpose)\s*[:\-]?\s*([^\n]+)", text, re.I)
    if m: form.purpose = form.purpose or m.group(2).strip()

    return form
