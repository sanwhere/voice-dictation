"""Bas-konus kayit + Deepgram (Turkce) STT.

Mikrofon SUREKLI acik tutulur (soguk baslangic ve bas/son kirpilmasi olmasin).
Arka planda kucuk bir 'preroll' tamponu doner; F8'e basinca basistan biraz
oncesinden itibaren kayit alinir, birakinca kisa bir kuyruk eklenir."""
import collections
import io
import threading
import wave

import numpy as np
import sounddevice as sd
import keyboard
import requests

import config

# Basistan once yakalanacak sure ve birakildiktan sonra eklenecek kuyruk
_PREROLL_SEC = 0.35
_TAIL_SEC = 0.20

_lock = threading.Lock()
_stream = None
_active = False                       # F8 basili -> kayit modu
_recording = []                       # aktifken biriken parcalar
_preroll = collections.deque(maxlen=int(config.SAMPLE_RATE * _PREROLL_SEC))
_session = requests.Session()         # keep-alive: her cagride yeniden baglanma


def _callback(indata, frames_count, time_info, status):
    mono = indata[:, 0].copy()
    with _lock:
        if _active:
            _recording.append(mono)
        else:
            _preroll.extend(mono)


def start_stream():
    """Mikrofonu acar (bir kez). Baslangicta cagrilirsa ilk kayit gecikmez."""
    global _stream
    with _lock:
        if _stream is not None:
            return
    s = sd.InputStream(samplerate=config.SAMPLE_RATE, channels=config.CHANNELS,
                       dtype="int16", callback=_callback, blocksize=0)
    s.start()
    with _lock:
        _stream = s


def _to_wav_bytes(audio: np.ndarray) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(config.CHANNELS)
        wf.setsampwidth(2)  # int16
        wf.setframerate(config.SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()


def transcribe_wav(wav_bytes: bytes) -> str:
    """WAV baytlarini Deepgram'e gonderir, transcript dondurur."""
    params = {
        "model": config.DEEPGRAM_MODEL,
        "smart_format": "true",
        "punctuate": "true",
    }
    lang = (config.DEEPGRAM_LANGUAGE or "tr").strip().lower()
    if lang in ("auto", "", "multi", "detect"):
        params["detect_language"] = "true"   # dili otomatik tespit et (TR/EN/...)
    else:
        params["language"] = lang
    headers = {
        "Authorization": f"Token {config.DEEPGRAM_API_KEY}",
        "Content-Type": "audio/wav",
    }
    resp = _session.post(config.DEEPGRAM_URL, params=params, headers=headers,
                         data=wav_bytes, timeout=(5, 30))
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
    except (KeyError, IndexError):
        return ""


def record_while_held(hotkey: str = None) -> np.ndarray:
    """Hotkey basili oldugu surece kaydeder, birakinca SES'i dondurur (ag yok).

    Bu fonksiyon tus birakilir birakilmaz doner; transkript (ag) ayri yapilir,
    boylece kayit gostergesi/sayac ag beklemesi boyunca calismaz."""
    global _active, _recording
    hotkey = hotkey or config.PTT_HOTKEY
    start_stream()

    with _lock:
        pre = np.array(_preroll, dtype="int16")
        _recording = [pre] if pre.size else []
        _active = True

    while keyboard.is_pressed(hotkey):
        sd.sleep(15)
    sd.sleep(int(_TAIL_SEC * 1000))

    with _lock:
        _active = False
        parts = _recording
        _recording = []

    if not parts:
        return np.zeros((0,), dtype="int16")
    return np.concatenate(parts)


def is_too_short(audio: np.ndarray) -> bool:
    return audio is None or audio.shape[0] < int(config.SAMPLE_RATE * 0.2)


def transcribe(audio: np.ndarray) -> str:
    """Kaydedilmis sesi Deepgram'e gonderip metin dondurur (ag adimi)."""
    if is_too_short(audio):
        return ""
    return transcribe_wav(_to_wav_bytes(audio))


def listen(hotkey: str = None) -> str:
    """Kaydet + transkript (eski uyumlu API; dictate.py bunu kullanir)."""
    return transcribe(record_while_held(hotkey))
