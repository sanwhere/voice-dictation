"""Sesli dikte: F8 bas-konus -> Deepgram (TR) -> transkripti odakli pencereye yaz.

Kullanim: Bunu KENDI terminalinde calistir (Claude Code'un disinda normal bir
PowerShell/Windows Terminal). Sonra Claude Code penceresine tikla, F8'i basili
tutup Turkce konus, birak. Metin panoya kopyalanir ve Ctrl+V ile yapistirilir.

Enjeksiyon (otomatik yapistirma) sende calismazsa metin yine panoda olur;
sadece elle Ctrl+V yaparsin.
"""
import sys
import time

# Windows konsolu cp1252 olabilir; Turkce print cokmesin diye UTF-8'e zorla.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import ctypes
import winsound

import keyboard
import pyperclip
import pyautogui

import config
import stt

try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

pyautogui.FAILSAFE = False  # dikte sirasinda imlec kosesi takintisi olmasin


def _beep_ok():
    try:
        winsound.Beep(880, 120)
    except Exception:
        pass


def _beep_err():
    try:
        winsound.Beep(330, 200)
    except Exception:
        pass


def handle_dictation():
    text = stt.listen()  # F8 basili oldugu surece kaydeder, birakinca Deepgram'e yollar
    if not text:
        print("[BOS] Bir sey duyulmadi.")
        _beep_err()
        return

    print(f"[METIN] {text}")
    pyperclip.copy(text)
    _beep_ok()

    if config.DICTATE_AUTO_PASTE:
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "v")
        if config.DICTATE_AUTO_ENTER:
            time.sleep(0.05)
            pyautogui.press("enter")
        print("   -> yapistirildi" + (" + Enter" if config.DICTATE_AUTO_ENTER else ""))
    else:
        print("   -> panoya kopyalandi (Ctrl+V ile yapistir)")


def main():
    if not config.DEEPGRAM_API_KEY:
        print("HATA: DEEPGRAM_API_KEY .env'de tanimli degil.")
        sys.exit(1)

    print("=== Sesli Dikte (Turkce) ===")
    print(f"Bas-konus tusu: {config.PTT_HOTKEY.upper()}")
    print(f"Otomatik yapistir: {'acik' if config.DICTATE_AUTO_PASTE else 'kapali'} | "
          f"Otomatik Enter: {'acik' if config.DICTATE_AUTO_ENTER else 'kapali'}")
    print("Hedef pencereye (orn. Claude Code) tikla, F8'i basili tutup konus, birak.")
    print("Cikis: Ctrl+C")

    # Mikrofonu simdiden ac (soguk baslangic ilk kaydi yememeli)
    try:
        stt.start_stream()
    except Exception as e:
        print("UYARI: mikrofon acilamadi:", e)
    _beep_ok()

    try:
        while True:
            if keyboard.is_pressed(config.PTT_HOTKEY):
                handle_dictation()
                while keyboard.is_pressed(config.PTT_HOTKEY):
                    time.sleep(0.05)
            time.sleep(0.03)
    except KeyboardInterrupt:
        print("\nKapatiliyor.")


if __name__ == "__main__":
    main()
