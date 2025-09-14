
# BCC Voice & Chat Assistant

AI assistant for the BCC hackathon that:

* **Analyzes client spend & transfers** → recommends the best **bank products** (cards, FX, deposit) and **push-messages**.
* **Chats casually** (RU/EN) to guide customers.
* **Fills an FX transfer application** (“заявление на перевод в иностранной валюте”) from natural language.
* **Optional voice**: offline **speech-to-text** (Vosk) and **text-to-speech** (pyttsx3).

The recommender reuses the project’s existing `src/` pipeline (features → benefit → rank) and supports **time-decayed/recency-aware** signals so offers are relevant **now**.

---

## 🗂 Project layout (important bits)

```
.
├─ data/                      # (optional) local test files
├─ results/                   # pipeline outputs (features.csv, recommendations.csv)
├─ notebooks/                 # scratch / analysis (optional)
├─ src/
│  ├─ __init__.py
│  ├─ config.py               # categories, product params, defaults
│  ├─ data_loader.py          # ZIP/CSV → per-client tables
│  ├─ feature_engineering.py  # build features (totals, % by category, recency, etc.)
│  ├─ benefit_calculator.py   # estimate benefit per product
│  ├─ ranking.py              # pick top-N products
│  ├─ push_generator.py       # rubric-aligned push texts (TOV)
│  └─ bcc_voice_assistant/
│     ├─ app.py               # ⭐ Streamlit app (UI)
│     ├─ assistant/
│     │  ├─ llm.py            # chat via Ollama (fallback rules if not running)
│     │  ├─ slot_filling.py   # extract FX transfer fields from free text
│     │  ├─ forms.py          # Streamlit form + export buttons
│     │  ├─ voice.py          # Vosk STT + pyttsx3 TTS
│     │  └─ knowledge.py      # short product blurbs & TOV hints
│     └─ models/              # (optional) put Vosk model here as: models/vosk-model/...
├─ requirements.txt
└─ README.md
```

---

## 🧰 Requirements

* **Python** 3.10+
* **pip** (latest)
* (Optional) **Ollama** for local LLM chat: [https://ollama.com](https://ollama.com)
* (Optional) **Vosk** offline STT model (RU or EN), unzipped

### Python deps

```bash
# minimal app
streamlit>=1.37
pandas>=2.0
numpy>=1.24
python-dateutil
pydantic>=2.7
requests

# optional voice/chat extras
pyttsx3          # TTS
vosk             # STT (needs a local model folder)
soundfile        # WAV I/O for Vosk
pywin32          # Windows TTS backend (on Windows)
audio-recorder-streamlit  # mic in Streamlit
```

Install all via the provided `requirements.txt`.

---

## 🚀 Quick start

### 1) Clone & set up a venv

**Windows (PowerShell)**

```powershell
git clone <YOUR_REPO_URL>.git
cd <repo>

py -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux**

```bash
git clone <YOUR_REPO_URL>.git
cd <repo>

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) (Optional but recommended) Enable real chat with **Ollama**

1. Install Ollama, then pull a model (small & fast):

   ```bash
   ollama pull llama3.1
   ```
2. Run the app after the pull completes. The sidebar shows:
   `LLM: ✅ Ollama – llama3.1 @ http://localhost:11434`
   If needed, set:

   ```bash
   # Windows PowerShell
   $env:OLLAMA_URL   = "http://localhost:11434"
   $env:OLLAMA_MODEL = "llama3.1"
   ```

> No Ollama? The assistant **still works** using a rule-based fallback for answers.

### 3) (Optional) Voice mode (offline)

* Download and **unzip** a Vosk model:

  * Russian: `vosk-model-small-ru-0.22`
  * English: `vosk-model-small-en-us-0.15`
* Either:

  1. **Place it inside the repo** as:

     ```
     src/bcc_voice_assistant/models/vosk-model/
       am/
       conf/
       ...
     ```

     (Note: `conf/` and `am/` must be **directly** under `vosk-model/`, not nested deeper.)
  2. **Or** set an env var to wherever you unzipped it:

     ```bash
     # Windows PowerShell
     $env:VOSK_MODEL_PATH = "C:\full\path\to\vosk-model"
     # macOS/Linux
     export VOSK_MODEL_PATH="/full/path/to/vosk-model"
     ```

The app prints **“Vosk model path resolved to: …”** on the Voice tab so you can verify it.

> We **do not** hardcode any machine-specific paths. `voice.py` looks for `VOSK_MODEL_PATH` first and then tries `src/bcc_voice_assistant/models/vosk-model/`.

### 4) Run Streamlit

```bash
# Windows
streamlit run .\src\bcc_voice_assistant\app.py

# macOS/Linux
streamlit run ./src/bcc_voice_assistant/app.py
```

Open the printed URL (usually [http://localhost:8501](http://localhost:8501)).

---

## 💡 How to use the app

### Recommender

* **Sidebar → Input type**: upload one **ZIP** with all CSVs **or** multiple CSVs.
* Press **Run recommender**.
  You’ll see:

  * `features_streamlit.csv`
  * `recommendations_streamlit.csv`
  * a **push** text for each client’s top product (TOV: personal → benefit → single CTA).

### Chat

Ask in RU/EN; examples:

* “Часто трачу на рестораны и такси — какую карту посоветуешь?”
* “Перевести 2 400 USD завтра. Получатель University of Toronto… SWIFT ROYCCAT2…”
* “I usually spend online and on groceries. Compare Shopper vs Everyday.”

⚙️ The assistant:

* auto-fills the **FX transfer application** from what you type/say,
* then you can tweak fields and **download JSON/TXT** of the filled draft.

### Voice (optional)

* Press/hold the mic button, speak, release.
* You’ll see **“Распознано: …”** and hear the answer.
* The same slot-filling logic updates the FX form.

---

## 🧠 What’s inside (tech)

* **Feature engineering** (`feature_engineering.py`): totals, **category shares**, inflow/outflow, **recency signals**.
* **Benefit model** (`benefit_calculator.py`): estimates per product (cashback categories, deposit interest, etc.).
* **Ranking** (`ranking.py`): top-N by estimated monthly benefit.
* **Push generation** (`push_generator.py`): follows rubric:

  1. personal context → 2) benefit → 3) **single CTA**, TOV-conformant (180–220 chars, no caps).
* **Chat/LLM** (`assistant/llm.py`): uses **Ollama** if available; otherwise a lightweight ruleset.
* **Form fill** (`assistant/slot_filling.py`): robust regex/heuristics + optional LLM JSON extraction.

---

## 🔧 Troubleshooting

**1) “Vosk model path resolved to: .” / “Folder '.' does not contain model files”**
→ The model path is empty/invalid. Fix by either:

* putting the unzipped model at `src/bcc_voice_assistant/models/vosk-model/` (must contain `conf/` and `am/`), **or**
* setting `VOSK_MODEL_PATH` to the absolute model folder before running Streamlit.

**2) Voice hears nothing / RU speech with EN model**
Use the model that matches your language. For Russian: `vosk-model-small-ru-0.22`.
For English: `vosk-model-small-en-us-0.15`.

**3) TTS sounds weird (reads “USD/EUR” literally)**
We normalize text for TTS and try to pick a RU/EN voice.
On Windows, install a **Russian voice** (Settings → Language & region → Russian → Speech).
You can also install **RHVoice** for higher-quality RU.

**4) Chat gives the same canned answer**
Ollama isn’t reachable. Make sure:

```bash
ollama pull llama3.1
curl http://localhost:11434/api/tags   # should list llama3.1
```

Sidebar should show `LLM: ✅ Ollama – llama3.1`.

**5) CSV upload error (secrets)**
We don’t require `secrets.toml`. Temporary files are written to the OS temp folder.

**6) Dataframe / Arrow error on `top_products`**
Handled by flattening nested lists into scalar columns before display/export.

---

## 🧪 Demo lines (handy)

* “Хочу выгодный обмен валюты, часто плачу в USD и EUR.”
* “Часто рестораны и такси — какую карту лучше?”
* “Перевод 2 150 USD 25.09.2025. Получатель John Smith. Банк: JPMorgan Chase, США. SWIFT CHASUS33. IBAN US12… Назначение: Tuition Fall 2025.”

---

## 🔐 Privacy

All processing is **local** (your browser ↔ local Streamlit; Ollama runs locally).
No data is sent to external services unless you change the LLM endpoint.

---

## 📝 License

Hackathon/demo use. Adapt as needed.

---

### Notes for contributors

* Please keep **no hardcoded absolute paths** in the repo.
* For voice, use `VOSK_MODEL_PATH` or drop a model under `src/bcc_voice_assistant/models/vosk-model/`.
* If you add new product rules, reflect them in `config.py` and `benefit_calculator.py`.
* Keep pushes aligned with the rubric (personal context → benefit → 1 CTA; TOV).

---

That’s it—drop this as `README.md` in the repo root.
