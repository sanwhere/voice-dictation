"""Sistem tepsisi (system tray) sesli dikte uygulamasi.

- Tepsi ikonu: durum (mavi=hazir, kirmizi=dinliyor).
- Sag tik menusu: Ayarlar (Deepgram anahtari, bas-konus tusu, dil, otomatik
  yapistir/Enter), otomatik secenekleri ac/kapa, Cikis.
- Arka planda: bas-konus tusunu basili tut -> Turkce konus -> metin odakli
  pencereye yapistirilir.
"""
import ctypes
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import keyboard
import pyperclip
import pyautogui
import winsound
import pystray
from PIL import Image, ImageDraw

import config
import stt
import settings_store
from i18n import t

pyautogui.FAILSAFE = False
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

_running = True
_listening = False
_settings_open = False
_icon = None


# ---------- Tepsi ikonu cizimi ----------
def make_icon(active=False):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = (230, 70, 70) if active else (70, 160, 225)
    d.rounded_rectangle([25, 10, 39, 38], radius=7, fill=color)          # mikrofon govdesi
    d.arc([18, 24, 46, 52], start=0, end=180, fill=color, width=4)        # stand kavisi
    d.line([32, 52, 32, 58], fill=color, width=4)                        # sap
    d.line([24, 58, 40, 58], fill=color, width=4)                        # taban
    return img


def _set_active(active):
    global _listening
    _listening = active
    if _icon is not None:
        _icon.icon = make_icon(active)


def _beep_ok():
    try:
        winsound.Beep(880, 110)
    except Exception:
        pass


def _beep_err():
    try:
        winsound.Beep(330, 180)
    except Exception:
        pass


# ---------- Dikte islemi ----------
def _handle_text(text):
    if not text:
        _beep_err()
        return
    pyperclip.copy(text)
    _beep_ok()
    if config.DICTATE_AUTO_PASTE:
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "v")
        if config.DICTATE_AUTO_ENTER:
            time.sleep(0.05)
            pyautogui.press("enter")


def _listen_loop():
    try:
        stt.start_stream()
    except Exception:
        pass
    while _running:
        try:
            if config.DEEPGRAM_API_KEY and keyboard.is_pressed(config.PTT_HOTKEY):
                _set_active(True)
                try:
                    text = stt.listen()
                    _handle_text(text)
                finally:
                    _set_active(False)
                while keyboard.is_pressed(config.PTT_HOTKEY):
                    time.sleep(0.05)
        except Exception:
            _set_active(False)
        time.sleep(0.03)


# ---------- Ayarlar penceresi (Tkinter) ----------
def _open_settings():
    global _settings_open
    if _settings_open:
        return
    _settings_open = True
    threading.Thread(target=_settings_window, daemon=True).start()


def _settings_window():
    global _settings_open
    s = settings_store.load()

    root = tk.Tk()
    root.title(t("set_title"))
    root.resizable(False, False)
    try:
        root.iconphoto(True, tk.PhotoImage(width=1, height=1))
    except Exception:
        pass

    frm = ttk.Frame(root, padding=16)
    frm.grid()

    ttk.Label(frm, text=t("lbl_key")).grid(row=0, column=0, sticky="w", pady=4)
    key_var = tk.StringVar(value=s["deepgram_api_key"])
    key_entry = ttk.Entry(frm, textvariable=key_var, width=46, show="*")
    key_entry.grid(row=0, column=1, columnspan=2, sticky="we", pady=4)
    show_var = tk.BooleanVar(value=False)

    def toggle_show():
        key_entry.config(show="" if show_var.get() else "*")
    ttk.Checkbutton(frm, text=t("chk_show"), variable=show_var, command=toggle_show).grid(row=1, column=1, sticky="w")

    ttk.Label(frm, text=t("lbl_hotkey")).grid(row=2, column=0, sticky="w", pady=4)
    hk_var = tk.StringVar(value=s["hotkey"])
    ttk.Entry(frm, textvariable=hk_var, width=20).grid(row=2, column=1, sticky="w", pady=4)

    capture_btn = ttk.Button(frm, text=t("btn_capture"))

    def capture_key():
        capture_btn.config(text=t("btn_capturing"), state="disabled")

        def grab():
            try:
                ev = keyboard.read_event(suppress=False)
                while ev.event_type != "down":
                    ev = keyboard.read_event(suppress=False)
                name = ev.name or f"sc{ev.scan_code}"
                root.after(0, lambda: hk_var.set(name))
            except Exception:
                pass
            root.after(0, lambda: capture_btn.config(text=t("btn_capture"), state="normal"))
        threading.Thread(target=grab, daemon=True).start()
    capture_btn.config(command=capture_key)
    capture_btn.grid(row=2, column=2, sticky="w", padx=6)

    # Konusulan dil ("auto" = Deepgram dil tespiti, TR/EN vb. otomatik)
    ttk.Label(frm, text=t("lbl_spoken")).grid(row=3, column=0, sticky="w", pady=4)
    lang_var = tk.StringVar(value=s["language"])
    ttk.Combobox(frm, textvariable=lang_var, width=14,
                 values=["auto", "tr", "en", "en-US", "de", "fr", "es", "ar", "ru", "it"]).grid(row=3, column=1, sticky="w", pady=4)
    ttk.Label(frm, text=t("opt_auto"), foreground="#888").grid(row=3, column=2, sticky="w")

    # Arayuz dili
    ttk.Label(frm, text=t("lbl_ui")).grid(row=4, column=0, sticky="w", pady=4)
    ui_var = tk.StringVar(value=s.get("ui_language", "tr"))
    ttk.Combobox(frm, textvariable=ui_var, width=14, state="readonly",
                 values=["tr", "en"]).grid(row=4, column=1, sticky="w", pady=4)

    paste_var = tk.BooleanVar(value=s["auto_paste"])
    enter_var = tk.BooleanVar(value=s["auto_enter"])
    ttk.Checkbutton(frm, text=t("chk_paste"), variable=paste_var).grid(row=5, column=0, columnspan=2, sticky="w", pady=2)
    ttk.Checkbutton(frm, text=t("chk_enter"), variable=enter_var).grid(row=6, column=0, columnspan=2, sticky="w", pady=2)

    info = ttk.Label(frm, text="", foreground="#2a7")
    info.grid(row=8, column=0, columnspan=3, sticky="w", pady=(6, 0))

    def do_save(close=True):
        new = {
            "deepgram_api_key": key_var.get().strip(),
            "hotkey": (hk_var.get().strip() or "f8"),
            "language": (lang_var.get().strip() or "tr"),
            "ui_language": (ui_var.get().strip() or "tr"),
            "auto_paste": bool(paste_var.get()),
            "auto_enter": bool(enter_var.get()),
        }
        settings_store.save(new)
        settings_store.apply_to_config(new)
        if _icon is not None:
            _icon.update_menu()
        if close:
            root.destroy()
        else:
            info.config(text=t("msg_saved"))
            root.after(1500, lambda: info.config(text=""))

    btns = ttk.Frame(frm)
    btns.grid(row=7, column=0, columnspan=3, sticky="e", pady=(12, 0))
    ttk.Button(btns, text=t("btn_apply"), command=lambda: do_save(False)).grid(row=0, column=0, padx=4)
    ttk.Button(btns, text=t("btn_saveclose"), command=lambda: do_save(True)).grid(row=0, column=1, padx=4)

    def on_close():
        global _settings_open
        _settings_open = False
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)

    root.eval("tk::PlaceWindow . center")
    root.attributes("-topmost", True)
    root.mainloop()
    globals()["_settings_open"] = False


# ---------- Tepsi menusu ----------
def _toggle_paste(icon, item):
    config.DICTATE_AUTO_PASTE = not config.DICTATE_AUTO_PASTE
    _persist_runtime()


def _toggle_enter(icon, item):
    config.DICTATE_AUTO_ENTER = not config.DICTATE_AUTO_ENTER
    _persist_runtime()


def _persist_runtime():
    s = settings_store.load()
    s["auto_paste"] = config.DICTATE_AUTO_PASTE
    s["auto_enter"] = config.DICTATE_AUTO_ENTER
    settings_store.save(s)


def _quit(icon, item):
    global _running
    _running = False
    icon.stop()


def _menu():
    return pystray.Menu(
        pystray.MenuItem(lambda i: t("menu_hotkey", key=config.PTT_HOTKEY.upper()), None, enabled=False),
        pystray.MenuItem(lambda i: t("menu_settings"), lambda i, it: _open_settings()),
        pystray.MenuItem(lambda i: t("menu_autopaste"), _toggle_paste, checked=lambda i: config.DICTATE_AUTO_PASTE),
        pystray.MenuItem(lambda i: t("menu_autoenter"), _toggle_enter, checked=lambda i: config.DICTATE_AUTO_ENTER),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(lambda i: t("menu_quit"), _quit),
    )


def main():
    global _icon
    settings_store.apply_to_config(settings_store.load())

    threading.Thread(target=_listen_loop, daemon=True).start()

    _icon = pystray.Icon("VoiceDictate", make_icon(False), t("app_name"), _menu())
    _beep_ok()
    _icon.run()


if __name__ == "__main__":
    main()
