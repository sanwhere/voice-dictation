"""Windows acilisinda otomatik baslatma (HKCU Run anahtari, yonetici gerekmez)."""
import os
import sys
import winreg

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "VoiceDictate"


def _command() -> str:
    """Acilista calistirilacak komut (tirnakli)."""
    if getattr(sys, "frozen", False):
        # PyInstaller exe
        return f'"{sys.executable}"'
    # Kaynaktan calisiyorsa: pythonw + tray_app.py (konsolsuz)
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    exe = pyw if os.path.exists(pyw) else sys.executable
    script = os.path.abspath(os.path.join(os.path.dirname(__file__), "tray_app.py"))
    return f'"{exe}" "{script}"'


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            val, _ = winreg.QueryValueEx(k, APP_NAME)
            return bool(val)
    except (FileNotFoundError, OSError):
        return False


def enable():
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
        winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _command())


def disable():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, APP_NAME)
    except (FileNotFoundError, OSError):
        pass


def set_enabled(on: bool):
    enable() if on else disable()
