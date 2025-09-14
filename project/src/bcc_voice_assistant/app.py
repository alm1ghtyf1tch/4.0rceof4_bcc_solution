# project/src/bcc_voice_assistant/app.py
# BCC Voice & Chat Assistant (Streamlit)
# - Reuses src/ pipeline (features -> rank -> push)
# - Chat + FX form autofill (slot filling + optional Ollama)
# - Optional voice (Vosk STT + pyttsx3 TTS)

from __future__ import annotations
import sys, tempfile
from pathlib import Path
import pandas as pd
import streamlit as st

# ── Locate a folder that CONTAINS "src" and add it to sys.path ─────────────────
APP_DIR = Path(__file__).resolve().parent  # .../project/src/bcc_voice_assistant
CANDIDATE_ROOTS: list[Path] = []

# typical layouts after your merges:
#   <repo>/project/src/...   (this file lives here)
#   <repo>/src/...
try:
    CANDIDATE_ROOTS.append(APP_DIR.parents[1])  # .../project/src
    CANDIDATE_ROOTS.append(APP_DIR.parents[2])  # .../project
    CANDIDATE_ROOTS.append(APP_DIR.parents[3])  # .../<repo_root>
except IndexError:
    pass

SELECTED_ROOT = None
for root in CANDIDATE_ROOTS:
    if root and (root / "src").is_dir():
        SELECTED_ROOT = root
        break

# Fallback: walk further up just in case
if SELECTED_ROOT is None:
    p = APP_DIR
    for _ in range(6):
        if (p / "src").is_dir():
            SELECTED_ROOT = p
            break
        p = p.parent

if SELECTED_ROOT is None:
    st.stop()  # hard fail early for clarity
else:
    if str(SELECTED_ROOT) not in sys.path:
        sys.path.insert(0, str(SELECTED_ROOT))

# ── Import pipeline pieces from src/ ───────────────────────────────────────────
from src.data_loader import load_zip_by_client, load_csv_list
from src.feature_engineering import build_features_table
from src.ranking import rank_by_benefit
from src.push_generator import generate_push
from src.config import PRODUCT_PARAMS, RESULTS_DIR

# ── Assistant helpers ──────────────────────────────────────────────────────────
from src.bcc_voice_assistant.assistant.llm import chat as llm_chat, extract_structured, status as llm_status
from src.bcc_voice_assistant.assistant.knowledge import PRODUCT_SUMMARIES, TOV_HINT
from src.bcc_voice_assistant.assistant.slot_filling import TransferForm, heuristic_fill
from src.bcc_voice_assistant.assistant.forms import form_editor, export_buttons
from src.bcc_voice_assistant.assistant.voice import stt_vosk, tts_pyttsx3, MODEL_DIR

st.set_page_config(page_title="BCC Voice & Chat Assistant", layout="wide")

# ── helpers ────────────────────────────────────────────────────────────────────
def dedup_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicate-named columns (keep the first) for Arrow/Streamlit."""
    if df is None:
        return df
    return df.loc[:, ~pd.Index(df.columns).duplicated(keep="first")]

# ── Sidebar: data upload & status ──────────────────────────────────────────────
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

    s = llm_status()
    st.caption(f"LLM: {'✅ Ollama' if s.get('ollama_ok') else '❌ Fallback (rules)'} • {s.get('model')} @ {s.get('url')}")

# ── Main layout ────────────────────────────────────────────────────────────────
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

# ── Runner ─────────────────────────────────────────────────────────────────────
def run_pipeline():
    """Load (ZIP or CSVs) → features → ranking → push → flatten → dedup → save."""
    # 1) Load data into per-client dict
    if uploaded_zip is not None:
        clients = load_zip_by_client(uploaded_zip)
    else:
        if not uploaded_csvs:
            st.warning("Please upload CSVs or ZIP.")
            return
        tmpdir = Path(tempfile.mkdtemp(prefix="bcc_csv_"))
        paths = []
        for f in uploaded_csvs:
            p = tmpdir / f.name
            p.write_bytes(f.read())
            paths.append(str(p))
        clients = load_csv_list(paths)

    # 2) Features
    features = build_features_table(clients)

    # 3) Ranking (ensure DataFrame even if API changes)
    recs_df = rank_by_benefit(features, top_n=topn)
    if isinstance(recs_df, tuple):
        # If someone changed API, pick the DF that has product columns
        recs_df = next((x for x in recs_df if isinstance(x, pd.DataFrame)), None)
        if recs_df is None:
            st.error("Unexpected ranking output (not a DataFrame).")
            return

    # 4) Merge name & generate push for top-1
    small = features[["client_code", "name"]] if "name" in features.columns else features[["client_code"]]
    merged = recs_df.merge(small, on="client_code", how="left")

    # avoid duplicate push_top1 if pipeline already added it
    if "push_top1" in merged.columns:
        merged = merged.drop(columns=["push_top1"])
    pushes = []
    for _, r in merged.iterrows():
        pushes.append(
            generate_push(
                r.get("name", ""),
                r.get("top1", None),
                float(r.get("top1_benefit", 0.0) or 0.0),
            )
        )
    merged["push_top1"] = pushes

    # 5) Flatten top_products into scalar columns (only if not already present)
    def tp_to_cols(tp):
        out = {}
        if isinstance(tp, (list, tuple)):
            for i in range(4):
                if i < len(tp) and isinstance(tp[i], (list, tuple)) and len(tp[i]) >= 2:
                    out[f"top{i+1}_product"] = tp[i][0]
                    out[f"top{i+1}_benefit"] = float(tp[i][1] or 0.0)
                else:
                    out[f"top{i+1}_product"] = None
                    out[f"top{i+1}_benefit"] = 0.0
        else:
            for i in range(4):
                out[f"top{i+1}_product"] = None
                out[f"top{i+1}_benefit"] = 0.0
        return out

    if "top_products" in merged.columns:
        already = set(merged.columns)
        extra = merged["top_products"].apply(tp_to_cols).apply(pd.Series)
        # Only keep columns that do NOT already exist
        extra = extra[[c for c in extra.columns if c not in already]]
        merged = pd.concat([merged.drop(columns=["top_products"]), extra], axis=1)

    # final safety: drop any duplicate-named columns (Arrow requirement)
    merged = dedup_columns(merged)

    # Save
    st.session_state.features_df = features
    st.session_state.recs_df = merged

# ── Overview tab ───────────────────────────────────────────────────────────────
with tabs[0]:
    st.caption(f"Vosk model path resolved to: {MODEL_DIR or 'not found'}")
    st.subheader("1) Recommender")
    if run_btn:
        run_pipeline()

    if st.session_state.features_df is not None:
        st.success("Features built ✅")
        safe_feat = dedup_columns(st.session_state.features_df)
        st.dataframe(safe_feat.head(20), use_container_width=True)

    if st.session_state.recs_df is not None:
        st.success("Recommendations ready ✅")
        safe_recs = dedup_columns(st.session_state.recs_df)
        st.dataframe(safe_recs.head(30), use_container_width=True)

        # Export CSVs to <SELECTED_ROOT>/src/ + RESULTS_DIR from config
        SRC_DIR = (SELECTED_ROOT / "src").resolve()
        outdir = (SRC_DIR / RESULTS_DIR).resolve()
        outdir.mkdir(parents=True, exist_ok=True)
        (safe_feat if 'safe_feat' in locals() else st.session_state.features_df).to_csv(outdir / "features_streamlit.csv", index=False)
        safe_recs.to_csv(outdir / "recommendations_streamlit.csv", index=False)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button("⬇️ Download features.csv",
                               data=open(outdir / "features_streamlit.csv", "rb").read(),
                               file_name="features.csv", mime="text/csv")
        with c2:
            st.download_button("⬇️ Download recommendations.csv",
                               data=open(outdir / "recommendations_streamlit.csv", "rb").read(),
                               file_name="recommendations.csv", mime="text/csv")

    st.divider()
    st.subheader("2) Product Glossary (for demo talk track)")
    for k, v in PRODUCT_SUMMARIES.items():
        st.markdown(f"**{k}** — {v}")
    st.caption("TOV: " + TOV_HINT + " (см. ТЗ по пуш-сообщениям).")

# ── Chat tab ───────────────────────────────────────────────────────────────────
with tabs[1]:
    st.subheader("Чат с ассистентом")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_msg = st.chat_input("Спросите про продукт или продиктуйте реквизиты перевода…")
    if user_msg:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})

        form = heuristic_fill(st.session_state.transfer_form, user_msg)
        schema = "{amount: number, currency: string, beneficiary_name: string, beneficiary_bank: string, beneficiary_country: string, beneficiary_account_iban: string, beneficiary_swift: string, purpose: string, execution_date: string}"
        extracted = extract_structured(user_msg, schema_hint=schema)
        if extracted:
            for k, v in extracted.items():
                if hasattr(form, k) and getattr(form, k) in (None, "", 0):
                    setattr(form, k, v)
        st.session_state.transfer_form = form

        answer = llm_chat(user_msg, st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

    st.divider()
    st.subheader("Черновик заявления (автозаполнение из сообщений)")
    updated, _ = form_editor(st.session_state.transfer_form)
    st.session_state.transfer_form = updated
    export_buttons(st.session_state.transfer_form)

# ── Voice tab ──────────────────────────────────────────────────────────────────
with tabs[2]:
    st.subheader("Голосовой режим (офлайн, опционально)")
    st.caption(f"Vosk model path resolved to: {MODEL_DIR or 'not found'}")

    try:
        from audio_recorder_streamlit import audio_recorder
        audio_bytes = audio_recorder(text="Нажмите, скажите запрос и отпустите", pause_threshold=2.0)
    except Exception:
        audio_bytes = None
        st.info("Установите audio-recorder-streamlit для записи микрофона.")

    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        recognized = stt_vosk(audio_bytes) or ""
        if recognized:
            st.write("Распознано:", f"**{recognized}**")

            form = heuristic_fill(st.session_state.transfer_form, recognized)
            schema = "{amount: number, currency: string, beneficiary_name: string, beneficiary_bank: string, beneficiary_country: string, beneficiary_account_iban: string, beneficiary_swift: string, purpose: string, execution_date: string}"
            extracted = extract_structured(recognized, schema_hint=schema)
            if extracted:
                for k, v in extracted.items():
                    if hasattr(form, k) and getattr(form, k) in (None, "", 0):
                        setattr(form, k, v)
            st.session_state.transfer_form = form

            st.session_state.chat_history.append({"role": "user", "content": recognized})
            reply = llm_chat(recognized, st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.write("Ответ ассистента:", reply)
            wav = tts_pyttsx3(reply)
            if wav:
                st.audio(wav, format="audio/wav")
        else:
            st.warning("Не удалось распознать речь. Убедитесь, что язык модели Vosk совпадает с языком речи (ru/en).")
