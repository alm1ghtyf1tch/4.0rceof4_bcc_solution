BCC Voice & Chat Assistant (Hackathon Demo)

An AI assistant for a bank hackathon that:
Analyzes customer transactions/transfers and recommends the best product mix using your existing src/ pipeline.

Chats casually (RU/EN), fills FX transfer forms from plain text/voice (“заявление на перевод в иностранной валюте”).

Sends push-like messages with the right Tone of Voice (TOV) and structure (personal context → benefit → single CTA).

This app reuses your modules in src/ (feature engineering, benefit estimation, ranking, push generation) and wraps them in a Streamlit UI with optional offline voice (Vosk STT + pyttsx3 TTS) and optional local LLM (Ollama).

🔧 Prerequisites

Python 3.10–3.11 (3.12 works for most, but 3.10/3.11 is safest).

Git

Windows / macOS / Linux supported

(Optional) Ollama for local LLM chat: https://ollama.com

(Optional) Vosk small RU model (~50–60 MB) for offline speech-to-text

📦 Repo layout (after merge)
repo-root/
├─ README.md                ← (this file)
├─ requirements.txt
├─ project/
│  └─ src/
│     └─ bcc_voice_assistant/
│        ├─ app.py          ← Streamlit entry point
│        ├─ assistant/
│        │  ├─ llm.py       ← Ollama + rules fallback
│        │  ├─ forms.py     ← FX form UI + export
│        │  ├─ slot_filling.py
│        │  ├─ knowledge.py ← product summaries, TOV hints
│        │  └─ voice.py     ← Vosk STT + pyttsx3 TTS (dynamic model path)
│        └─ models/
│           └─ vosk-model/  ← (Put Vosk model here, not committed)
└─ src/
   ├─ config.py             ← PRODUCT_PARAMS, RESULTS_DIR, categories
   ├─ data_loader.py        ← ZIP/CSV loader (per-client dict)
   ├─ feature_engineering.py
   ├─ benefit_calculator.py
   ├─ ranking.py
   ├─ push_generator.py
   └─ pipeline.py           ← batch pipeline (not required by the app)


Outputs (features_streamlit.csv, recommendations_streamlit.csv) are written to:

<src/>/<RESULTS_DIR from config.py>


By default RESULTS_DIR = '../results', so you’ll see files in:

repo-root/src/../results  →  repo-root/results

🚀 Quick start
1) Clone & create a virtual environment

Windows (PowerShell)

git clone <YOUR_REPO_URL> bcc-assistant
cd bcc-assistant

python -m venv .venv
& .\.venv\Scripts\Activate.ps1    # activate venv

python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt


macOS / Linux

git clone <YOUR_REPO_URL> bcc-assistant
cd bcc-assistant

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

2) (Optional) Install Ollama & a local model

Install Ollama: https://ollama.com/download

Start it, then pull a model:

ollama pull llama3.1  # or qwen2, phi3, etc.


The app auto-detects Ollama at http://localhost:11434. If not found, it uses a rules-based fallback for chat.

3) (Optional) Download Vosk RU model (offline STT)

Download vosk-model-small-ru-0.22 (or EN if you prefer):

RU: https://alphacephei.com/vosk/models
 → vosk-model-small-ru-0.22.zip

Unzip it to:

project/src/bcc_voice_assistant/models/vosk-model


After unzip, this folder must contain am/ and conf/ subfolders:

project/src/bcc_voice_assistant/models/vosk-model/am
project/src/bcc_voice_assistant/models/vosk-model/conf


💡 You do not have to hardcode any paths. The app’s voice.py dynamically locates the model, but you can also point an env var for clarity:

Windows:

$env:VOSK_MODEL_PATH = (Resolve-Path ".\project\src\bcc_voice_assistant\models\vosk-model").Path


macOS/Linux:

export VOSK_MODEL_PATH="$(pwd)/project/src/bcc_voice_assistant/models/vosk-model"

4) Run the app

Recommended (uses your active venv’s Streamlit):

# Windows (PowerShell, from repo root)
$env:PYTHONPATH = (Resolve-Path ".").Path
python -m streamlit run ".\project\src\bcc_voice_assistant\app.py"

# macOS / Linux
export PYTHONPATH="$(pwd)"
python -m streamlit run "./project/src/bcc_voice_assistant/app.py"


Then open the URL Streamlit prints (usually http://localhost:8501
).

🧪 Using the app

Overview → Data & Recommender (sidebar):

Upload either:

One ZIP containing multiple CSVs (transactions & transfers), or

Multiple CSV files (select all)

Click Run recommender.

You’ll see:

Features table

Recommendations table

Download buttons for both.

Chat tab:

Ask questions about products or write a transfer request in natural language, e.g.
нужно оплатить обучение 2400 USD завтра, получатель John Smith, банк Chase, SWIFT CHASUS33

The assistant:

Responds casually (Ollama if available).

Auto-fills an FX transfer form (slots extracted from text).

You can edit the form and export it.

Voice tab (optional):

Use the mic widget, speak in the same language as your model (RU/EN).

The assistant transcribes with Vosk, fills the form, replies, and speaks using pyttsx3.

🧠 How recommendations work

Your existing pipeline is reused:

feature_engineering.py builds per-client features (total spend, % by categories, incoming/outgoing, etc.).

benefit_calculator.py estimates monthly benefit per product using PRODUCT_PARAMS (cashbacks/rates).

ranking.py sorts products by estimated benefit and returns top_products per client.

push_generator.py creates a single TOV-compliant push for the top product (personal context → benefit → single CTA).

The Streamlit app:

Shows features + recommendations

Flattens top_products into columns safely (no PyArrow duplicate-column errors)

Writes outputs to results/.

Tune products in src/config.py → PRODUCT_PARAMS.
Change TOV or copy lines from assistant/knowledge.py or push_generator.py.

🧾 Expected CSV format (flexible)

The loader is forgiving but expects:

Either CSVs include client_code column, or file names contain a number (used as client_code).

Transactions CSVs typically include date, amount, category, merchant (names vary); detection uses presence of category.

Transfers CSVs include at least type, direction, amount (names vary); detection uses presence of type + direction.

ZIP mode: put many CSVs inside one ZIP and upload.

🗣️ Push TOV rubric (used by generator)

Each push = 1) Personal context → 2) Benefit → 3) Single CTA.
Tone: friendly, concise, on “вы”, 0–1 emoji max, no caps, no pressure.
Channel length target: 180–220 chars.
(See assistant/knowledge.py & your rubric for details.)

🧰 Troubleshooting (copy/paste fixes)
1) “ModuleNotFoundError: No module named src.data_loader”

You’re likely launching Streamlit from the wrong directory or PYTHONPATH isn’t set.

Fix:

Always run from repo root.

Use:

# Windows
& .\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Resolve-Path ".").Path
python -m streamlit run ".\project\src\bcc_voice_assistant\app.py"

# macOS / Linux
source .venv/bin/activate
export PYTHONPATH="$(pwd)"
python -m streamlit run "./project/src/bcc_voice_assistant/app.py"

2) “Invalid value: File does not exist: …app.py”

You’re in the wrong folder or using an old path.

Entry file is: project/src/bcc_voice_assistant/app.py.

3) Mixed virtualenvs / “Fatal error in launcher…”

You may have two venvs (e.g. .venv and project\.venv) and Windows picks the wrong streamlit.exe.

Fix: Use python -m streamlit ... from the active venv, or delete the stray venv:

Remove-Item -Recurse -Force ".\project\.venv"

4) Streamlit secrets error (StreamlitSecretNotFoundError)

Older snippet used st.secrets['_tmpdir']. The current app does not require secrets.

If you still see it, you’re running an old file. Restart with this README’s command.

5) PyArrow error: “Expected bytes / Duplicate column names”

Caused by nested lists or duplicate columns (top_products, top1_benefit, etc.).

The app now flattens and de-dups columns before display/export.

If you somehow reintroduce columns with the same name, the app drops later duplicates automatically.

6) Vosk model error: “Folder does not contain model files”

Path is wrong or the folder is empty/misaligned.

Fix checklist:

Ensure the model is unzipped here:

project/src/bcc_voice_assistant/models/vosk-model


and that inside you have:

.../vosk-model/am
.../vosk-model/conf


Optionally set env var before running:

$env:VOSK_MODEL_PATH = (Resolve-Path ".\project\src\bcc_voice_assistant\models\vosk-model").Path


Voice tab prints “Vosk model path resolved to: …” so you can confirm.

7) Audio works but voice reply is gibberish

pyttsx3 uses your OS voices. If RU text is spoken with EN voice, pronunciation sounds weird.

Fixes:

On Windows, install a Russian voice pack (Settings → Time & language → Speech → Manage voices).

Or set voice.py to pick a RU voice by id if installed (optional tweak).

8) Chat only replies once / repeats same answer

Ensure Ollama is running (ollama serve started by the desktop app) and a model is pulled (ollama pull llama3.1).

The app shows LLM status in the sidebar. If not OK, it falls back to a simple rules engine (deterministic).

9) “app can’t import after changing files” (stale caches)
Get-ChildItem -Recurse -Include "__pycache__" -Directory . | Remove-Item -Recurse -Force


Restart Streamlit.

🧩 Configuration

Products & parameters: src/config.py → PRODUCT_PARAMS

Categories & keywords: src/config.py → BROAD_CATEGORY_KEYWORDS

Results folder: src/config.py → RESULTS_DIR (default ../results)

Push generation: src/push_generator.py (TOV structure)

🛡️ Notes

Data: do not commit real customer data. Use the provided hackathon examples.

Models: Vosk model is not committed; keep it local.

LLM: Ollama runs locally; no keys required. If absent, the app still works (rules fallback).

🧭 Development tips

Sanity check Streamlit itself:

python -m streamlit hello


Run app with explicit Python (no activation needed):

".\.venv\Scripts\python.exe" -m streamlit run ".\project\src\bcc_voice_assistant\app.py"


Log prints: use st.caption(...) / st.write(...) sparingly to keep UI clean.