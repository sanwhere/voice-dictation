"""Ayarlari %APPDATA%\\VoiceDictate\\settings.json icinde tutar ve config'e uygular.

exe olarak paketlendiginde .env yerine bu kullanilir; kullanici tepsi menusunden
Deepgram anahtarini ve diger ayarlari guncelleyebilir."""
import json
import os

import config

APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "VoiceDictate")
SETTINGS_PATH = os.path.join(APP_DIR, "settings.json")

DEFAULTS = {
    # Deepgram anahtarini tepsi menusu > Ayarlar'dan gir (ya da settings.json'a yaz).
    "deepgram_api_key": "",
    "hotkey": "f8",
    "language": "tr",          # konusulan dil: "tr","en",... ya da "auto"
    "ui_language": "tr",        # arayuz dili: "tr" / "en"
    "auto_paste": True,
    "auto_enter": False,
    "auto_start": False,        # Windows acilisinda otomatik baslat
    "show_overlay": True,       # kayit sirasinda ekran gostergesi
}


def load() -> dict:
    data = dict(DEFAULTS)
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            data.update({k: saved[k] for k in DEFAULTS if k in saved})
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return data


def save(data: dict):
    os.makedirs(APP_DIR, exist_ok=True)
    clean = {k: data.get(k, DEFAULTS[k]) for k in DEFAULTS}
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)


def apply_to_config(data: dict):
    """Ayarlari calisan config modulune yansitir (stt/dictate bunlari okur)."""
    config.DEEPGRAM_API_KEY = (data.get("deepgram_api_key") or "").strip()
    config.PTT_HOTKEY = (data.get("hotkey") or "f8").strip()
    config.DEEPGRAM_LANGUAGE = (data.get("language") or "tr").strip()
    config.UI_LANGUAGE = (data.get("ui_language") or "tr").strip()
    config.DICTATE_AUTO_PASTE = bool(data.get("auto_paste", True))
    config.DICTATE_AUTO_ENTER = bool(data.get("auto_enter", False))
    config.SHOW_OVERLAY = bool(data.get("show_overlay", True))
