"""
UI helpers for displaying and editing the transfer form inside Streamlit.
"""

from typing import Dict, Tuple
import streamlit as st
from .slot_filling import TransferForm

FIELDS = [
    ("payer_fullname", "Плательщик (ФИО)"),
    ("payer_account", "Счёт плательщика (IBAN)"),
    ("amount", "Сумма"),
    ("currency", "Валюта (USD/EUR/...)"),
    ("beneficiary_name", "Получатель (бенефициар)"),
    ("beneficiary_bank", "Банк получателя"),
    ("beneficiary_country", "Страна получателя"),
    ("beneficiary_account_iban", "Счёт получателя (IBAN)"),
    ("beneficiary_swift", "SWIFT/BIC"),
    ("purpose", "Назначение платежа"),
    ("execution_date", "Дата исполнения (дд.мм.гггг/сегодня/завтра)"),
]

def form_editor(initial: TransferForm) -> Tuple[TransferForm, bool]:
    st.subheader("Заявление на перевод в иностранной валюте")
    col1, col2 = st.columns(2)
    values = {}
    for i, (key, label) in enumerate(FIELDS):
        with (col1 if i % 2 == 0 else col2):
            values[key] = st.text_input(label, value=str(getattr(initial, key) or ""))

    # Cast amount if numeric
    try:
        values["amount"] = float(values["amount"]) if values["amount"] else None
    except:
        pass

    updated = TransferForm(**values)
    saved = st.button("Сохранить форму")
    if saved:
        st.success("Сохранено в сессию (можно экспортировать ниже).")
    return updated, saved

def export_buttons(form: TransferForm):
    import json, io
    st.download_button(
        "Скачать JSON",
        data=json.dumps(form.to_dict(), ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="transfer_form.json",
        mime="application/json",
    )
    # Simple TXT stub for judges
    txt = io.StringIO()
    for k, v in form.to_dict().items():
        txt.write(f"{k}: {v}\n")
    st.download_button("Скачать TXT", data=txt.getvalue(), file_name="transfer_form.txt")
