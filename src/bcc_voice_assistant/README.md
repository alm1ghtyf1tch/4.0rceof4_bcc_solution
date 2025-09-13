# BCC Voice & Chat Assistant (Hackathon Demo)

- Uses **your existing** `src/` code: benefit calc, ranking, pipeline.
- Streamlit UI: data upload → run recommender → show Top-N + push texts.
- Chatbot that can fill a **foreign-currency transfer form** from free text.
- Optional **offline voice** (Vosk STT + pyttsx3 TTS).
- Optional **local LLM** via **Ollama** (llama3.1) – free, no keys.

### Run
```bash
pip install -r requirements.txt
streamlit run app.py
