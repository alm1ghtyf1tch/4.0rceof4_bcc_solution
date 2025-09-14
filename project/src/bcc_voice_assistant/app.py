
## `bcc_voice_assistant/app.py`
# Streamlit front-end for the BCC Hackathon demo
# - Reuses your existing src/ pipeline (features -> rank -> push)
# - Casual chat that can also fill a FX transfer form (slot filling + optional LLM)
# - Optional voice in/out (Vosk + pyttsx3)
#
# Tips for judges:
# 1) Upload a ZIP with transactions/transfers for 60 clients, or select multiple CSVs.
# 2) Click "Run recommender".
# 3) Use "Chat" to ask for help or say something like:
#    "нужно оплатить обучение 2400 USD завтра получатель John Smith в США, банк Chase, SWIFT CHASUS33"
#    → slots will auto-fill.


#To RUN THE APP RUN 
#cd "C:\Users\Zhangir\Desktop\Hackathon AI voice assistant\4.0rceof4_bcc_solution"
#streamlit run ".\src\bcc_voice_assistant\app.py"

from __future__ import annotations
import os, sys
from pathlib import Path
import streamlit as st
import pandas as pd
import tempfile
import json


# --- Ensure we can import your repo's src/ modules ---
# app.py path: <repo_root>\src\bcc_voice_assistant\app.py
ROOT = Path(__file__).resolve().parents[2]   # -> <repo_root>
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SRC_DIR = ROOT / "src"   # for file paths later (NOT for imports)

# ---- imports (package-style) ----
from src.pipeline import run_pipeline_from_zip
from src.data_loader import load_zip_by_client, load_csv_list
from src.feature_engineering import build_features_table
from src.ranking import rank_by_benefit
from src.push_generator import generate_push
from src.config import PRODUCT_PARAMS, RESULTS_DIR

# --- Assistant helpers ---
from assistant.llm import chat as llm_chat, extract_structured
from assistant.knowledge import PRODUCT_SUMMARIES, TOV_HINT
from assistant.slot_filling import TransferForm, heuristic_fill
from assistant.forms import form_editor, export_buttons
from src.bcc_voice_assistant.assistant.voice import stt_vosk, tts_pyttsx3, MODEL_DIR
st.caption(f"Vosk model path resolved to: {MODEL_DIR}")
from assistant.llm import chat as llm_chat, extract_structured
from assistant.llm import status as llm_status  # add this import
from assistant.voice import MODEL_DIR
st.caption(f"Vosk model path: {MODEL_DIR}")

st.set_page_config(page_title="BCC Voice & Chat Assistant", layout="wide")

with st.sidebar:
    ...
    s = llm_status()
    st.caption(f"LLM: {'✅ Ollama' if s['ollama_ok'] else '❌ Fallback (rules)'}  •  {s['model']} @ {s['url']}")

# ---- Sidebar: Data upload & run -------------------------------------------------
with st.sidebar:
    st.title("📊 Data & Recommender")
    mode = st.radio("Input type", ["ZIP with all CSVs", "Multiple CSV files"])
    uploaded_zip = None
    uploaded_csvs = None
    if mode == "ZIP with all CSVs":
        uploaded_zip = st.file_uploader("Upload ZIP", type=["zip"])
    else:
        uploaded_csvs = st.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=True)
    topn = st.slider("Top-N products", 1, 5, 4)
    run_btn = st.button("Run recommender")

# ---- Main layout with tabs ------------------------------------------------------
st.title("BCC Voice & Chat Assistant")
tabs = st.tabs(["🏠 Overview", "💬 Chat", "🎙 Voice (optional)"])

# Session state
if "features_df" not in st.session_state:
    st.session_state.features_df = None
if "recs_df" not in st.session_state:
    st.session_state.recs_df = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "transfer_form" not in st.session_state:
    st.session_state.transfer_form = TransferForm()

# ---- RUN PIPELINE ---------------------------------------------------------------
def run_pipeline():
    # 1) Load data to per-client dict
    if uploaded_zip is not None:
        clients = load_zip_by_client(uploaded_zip)
    else:
        if not uploaded_csvs:
            st.warning("Please upload CSVs or ZIP.")
            return
        tmp_paths = []
        TMPDIR = Path(tempfile.gettempdir()) / "bcc_uploads"
        TMPDIR.mkdir(parents=True, exist_ok=True)
        for f in uploaded_csvs:
            p = TMPDIR / f.name
            with open(p, "wb") as out:
                out.write(f.read())
            tmp_paths.append(str(p))
        clients = load_csv_list(tmp_paths)

    # 2) Build features
    features = build_features_table(clients)

    # 3) Rank products
    recs = rank_by_benefit(features, top_n=topn)

    # 4) Merge name & push for top-1
    small = features[["client_code","name"]] if "name" in features.columns else features[["client_code"]]
    merged = recs.merge(small, on="client_code", how="left")
    pushes = []
    for _, r in merged.iterrows():
        push = generate_push(r.get("name",""), r.get("top1", None), r.get("top1_benefit", 0.0))
        pushes.append(push)
    merged["push_top1"] = pushes
    merged["top_products_json"] = merged["top_products"].apply(
    lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, tuple)) else ""
)
    merged = merged.drop(columns=["top_products"])

    st.session_state.features_df = features
    st.session_state.recs_df = merged

with tabs[0]:
    st.subheader("1) Recommender")
    if run_btn:
        run_pipeline()

    if st.session_state.features_df is not None:
        st.success("Features built ✅")
        st.dataframe(st.session_state.features_df.head(20), use_container_width=True)

    if st.session_state.recs_df is not None:
        st.success("Recommendations ready ✅")
        st.dataframe(st.session_state.recs_df.head(30), use_container_width=True)

        # Export CSVs to local /results
        outdir = (SRC_DIR / RESULTS_DIR).resolve()
        outdir.mkdir(parents=True, exist_ok=True)
        f_features = outdir / "features_streamlit.csv"
        f_recs = outdir / "recommendations_streamlit.csv"
        st.session_state.features_df.to_csv(f_features, index=False)
        st.session_state.recs_df.to_csv(f_recs, index=False)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button("⬇️ Download features.csv", data=open(f_features, "rb").read(),
                               file_name="features.csv", mime="text/csv")
        with c2:
            st.download_button("⬇️ Download recommendations.csv", data=open(f_recs, "rb").read(),
                               file_name="recommendations.csv", mime="text/csv")

    st.divider()
    st.subheader("2) Product Glossary (for demo talk track)")
    for k, v in PRODUCT_SUMMARIES.items():
        st.markdown(f"**{k}** — {v}")

    st.caption("TOV: " + TOV_HINT + " (см. ТЗ по пуш-сообщениям).")

# ---- CHAT -----------------------------------------------------------------------
with tabs[1]:
    st.subheader("Чат с ассистентом")
    # Show history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_msg = st.chat_input("Спросите про продукт или продиктуйте реквизиты перевода…")
    if user_msg:
        st.session_state.chat_history.append({"role":"user","content":user_msg})

        # 1) Try to extract structured transfer data
        form = heuristic_fill(st.session_state.transfer_form, user_msg)

        # 2) If LLM available, refine extraction to JSON
        schema = "{amount: number, currency: string, beneficiary_name: string, beneficiary_bank: string, beneficiary_country: string, beneficiary_account_iban: string, beneficiary_swift: string, purpose: string, execution_date: string}"
        extracted = extract_structured(user_msg, schema_hint=schema)
        if extracted:
            for k, v in extracted.items():
                if hasattr(form, k) and getattr(form, k) in (None, "", 0):
                    setattr(form, k, v)

        st.session_state.transfer_form = form

        # 3) Chat answer (uses Ollama if present, else rule-based)
        answer = llm_chat(user_msg, st.session_state.chat_history)

        st.session_state.chat_history.append({"role":"assistant","content":answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

    st.divider()
    st.subheader("Черновик заявления (автозаполнение из сообщений)")
    updated, _ = form_editor(st.session_state.transfer_form)
    st.session_state.transfer_form = updated
    export_buttons(st.session_state.transfer_form)

# ---- VOICE (OPTIONAL) ----------------------------------------------------------
with tabs[2]:
    st.subheader("Голосовой режим (офлайн, опционально)")
    st.caption(f"Vosk model path resolved to: {MODEL_DIR}")

    try:
        from audio_recorder_streamlit import audio_recorder
        audio_bytes = audio_recorder(text="Нажмите, скажите запрос и отпустите", pause_threshold=2.0)
    except Exception:
        audio_bytes = None
        st.info("Установите audio-recorder-streamlit для записи микрофона.")

    # Only proceed if we actually have audio
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")

        recognized = stt_vosk(audio_bytes) or ""
        if recognized:
            st.write("Распознано:", f"**{recognized}**")

            # 👉 auto-fill the FX transfer form from voice text
            form = heuristic_fill(st.session_state.transfer_form, recognized)
            schema = "{amount: number, currency: string, beneficiary_name: string, beneficiary_bank: string, beneficiary_country: string, beneficiary_account_iban: string, beneficiary_swift: string, purpose: string, execution_date: string}"
            extracted = extract_structured(recognized, schema_hint=schema)
            if extracted:
                for k, v in extracted.items():
                    if hasattr(form, k) and getattr(form, k) in (None, "", 0):
                        setattr(form, k, v)
            st.session_state.transfer_form = form

            # Chat reply + TTS
            st.session_state.chat_history.append({"role":"user","content":recognized})
            reply = llm_chat(recognized, st.session_state.chat_history)
            st.session_state.chat_history.append({"role":"assistant","content":reply})

            st.write("Ответ ассистента:", reply)
            wav = tts_pyttsx3(reply)
            if wav:
                st.audio(wav, format="audio/wav")
        else:
            st.warning("Не удалось распознать речь. Убедитесь, что язык модели Vosk совпадает с языком речи (ru/en).")
