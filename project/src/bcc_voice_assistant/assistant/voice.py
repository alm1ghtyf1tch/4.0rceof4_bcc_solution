from __future__ import annotations
import io, os
from pathlib import Path
from typing import Optional
import re
MODEL_DIR = Path(r"C:\Users\Zhangir\Desktop\Hackathon AI voice assistant\4.0rceof4_bcc_solution\src\bcc_voice_assistant\models\vosk-model")

# ---------- robust model path detection ----------
THIS_DIR = Path(__file__).resolve().parent

def _valid_model_dir(p: Path) -> bool:
    try:
        return (
            isinstance(p, Path)
            and p.exists()
            and (p / "conf").exists()
            and (p / "am").exists()
        )
    except Exception:
        return False

# Only use env var if it's non-empty AND points to a real Vosk model folder
_env = os.getenv("VOSK_MODEL_PATH", "").strip()


# ---------- STT / TTS ----------
def stt_vosk(audio_bytes: bytes) -> Optional[str]:
    """Return recognized text with Vosk, or None if unavailable."""
    try:
        import vosk, json, soundfile as sf, numpy as np
    except Exception:
        return None
    if not MODEL_DIR:
        return None
    try:
        # read wav -> mono float32
        data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=False)
        if hasattr(data, "ndim") and data.ndim > 1:
            data = data.mean(axis=1)

        # resample to 16 kHz (simple)
        TARGET_SR = 16000
        if sr != TARGET_SR and sr > 0:
            x = np.linspace(0, 1, num=len(data), endpoint=False, dtype="float32")
            y = np.linspace(0, 1, num=int(len(data) * TARGET_SR / sr), endpoint=False, dtype="float32")
            data = np.interp(y, x, data).astype("float32")
            sr = TARGET_SR

        # float32 -> int16 PCM
        pcm16 = (np.clip(data, -1.0, 1.0) * 32767.0).astype("int16").tobytes()

        # recognize
        model = vosk.Model(str(MODEL_DIR))
        rec = vosk.KaldiRecognizer(model, sr)
        step = int(sr * 0.25) * 2  # 0.25s chunks, 2 bytes/sample
        for i in range(0, len(pcm16), step):
            rec.AcceptWaveform(pcm16[i:i+step])

        # collect text
        out = []
        part = rec.Result()
        if part:
            try:
                out.append(__import__("json").loads(part).get("text", ""))
            except Exception:
                pass
        final = rec.FinalResult()
        if final:
            try:
                out.append(__import__("json").loads(final).get("text", ""))
            except Exception:
                pass
        return " ".join([t for t in out if t]).strip()
    except Exception:
        return None


import re

def _has_cyrillic(s: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", s))

def _normalize_tts_text(text: str, lang: str) -> str:
    s = text.strip()

    # Common cleanups
    s = s.replace(" / ", " и ").replace("/", " и ")
    s = s.replace("&", " и ").replace(" + ", " и ")
    s = re.sub(r"\s*[\(\)\[\]\{\}]\s*", ", ", s)        # remove brackets
    s = re.sub(r"[-–—]{2,}", " — ", s)                 # collapse long dashes
    s = re.sub(r"\s+", " ", s)

    if lang == "ru":
        # Currency & banking terms to speak naturally in RU
        repl = [
            (r"USD", "доллары США"),
            (r"EUR|€", "евро"),
            (r"KZT|₸", "тенге"),
            (r"GBP|£", "фунты стерлингов"),
            (r"RUB|₽", "рубли"),
            (r"FX\b", "обмен валюты"),
            (r"\bSWIFT\b", "свифт"),
            (r"\bIBAN\b", "ай-бан"),
        ]
        for pat, rep in repl:
            s = re.sub(pat, rep, s, flags=re.IGNORECASE)
        # Fix “доллары США и евро” case when it came from USD/EUR
        s = re.sub(r"доллары США\s*и\s*евро", "доллары США и евро", s)
    else:
        # English tweaks
        s = s.replace("₸", "tenge")
        s = re.sub(r"\bKZT\b", "tenge", s)
        s = s.replace("€", "euro").replace("£", "pounds").replace("₽", "rubles")
        s = re.sub(r"\bFX\b", "currency exchange", s)

    return s.strip()

def _pick_voice(engine, lang: str):
    """
    Try to pick a voice that matches the language.
    RU examples on Windows: 'Microsoft Irina Desktop - Russian', 'Microsoft Pavel'
    EN examples: 'Microsoft Zira', 'Microsoft David'
    """
    voices = engine.getProperty("voices")

    # Helper to check a voice for a language
    def is_lang(voice, needle):
        # voice.languages is not always populated on Windows, so check name/id too
        lang_codes = getattr(voice, "languages", []) or []
        ok_langcode = any((isinstance(x, (bytes, bytearray)) and needle.encode() in x) or (isinstance(x, str) and needle in x)
                          for x in lang_codes)
        name_id = (voice.name or "").lower() + " " + (voice.id or "").lower()
        ok_name = ("russian" in name_id or "irina" in name_id or "pavel" in name_id) if needle == "ru" else ("zira" in name_id or "david" in name_id or "english" in name_id or "en-us" in name_id)
        return ok_langcode or ok_name

    # 1st pass: exact language
    for v in voices:
        if lang == "ru" and is_lang(v, "ru"):
            return v.id
        if lang == "en" and is_lang(v, "en"):
            return v.id
    # 2nd pass: some reasonable default
    if voices:
        return voices[0].id
    return None

def tts_pyttsx3(text: str) -> Optional[bytes]:
    """Synthesize speech to WAV (bytes) with pyttsx3, with language/normalization."""
    try:
        import pyttsx3, tempfile, os

        # Detect language from text
        lang = "ru" if _has_cyrillic(text) else "en"
        say = _normalize_tts_text(text, lang)

        engine = pyttsx3.init()
        voice_id = _pick_voice(engine, lang)
        if voice_id:
            engine.setProperty("voice", voice_id)

        # Slightly slower for clarity
        rate = engine.getProperty("rate") or 200
        engine.setProperty("rate", int(rate * 0.9))
        engine.setProperty("volume", 1.0)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            fname = tmp.name
        engine.save_to_file(say, fname)
        engine.runAndWait()
        with open(fname, "rb") as f:
            data = f.read()
        os.remove(fname)
        return data
    except Exception:
        return None
