"""Kayit gostergesi: surukleneblir, saniye sayacli, ust uste duran kucuk pencere.

Onemli: pencere odagi ASLA almaz (WS_EX_NOACTIVATE) -> yapistirma hedef pencereye
gider. Kendi thread'inde bir Tk root calistirir; show()/hide() thread-guvenli."""
import ctypes
import threading
import time
import tkinter as tk

from i18n import t

_GWL_EXSTYLE = -20
_WS_EX_NOACTIVATE = 0x08000000
_WS_EX_TOOLWINDOW = 0x00000080
_GA_ROOT = 2


class RecordingOverlay:
    def __init__(self):
        self._state = "idle"   # idle | rec | proc
        self._start = 0.0
        self._proc_start = 0.0
        self._root = None
        self._pos = None  # (x, y) oturum boyunca hatirlanan konum
        self._ready = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()
        self._ready.wait(timeout=5)

    # ---- Tk thread'i ----
    def _run(self):
        self._root = tk.Tk()
        self._root.withdraw()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        try:
            self._root.attributes("-alpha", 0.92)
        except Exception:
            pass

        frame = tk.Frame(self._root, bg="#1e1e1e", highlightthickness=2, highlightbackground="#e64545")
        frame.pack()
        self._dot = tk.Label(frame, text="●", fg="#e64545", bg="#1e1e1e", font=("Segoe UI", 15, "bold"))
        self._dot.pack(side="left", padx=(12, 6), pady=8)
        self._label = tk.Label(frame, text="REC  0.0s", fg="#ffffff", bg="#1e1e1e", font=("Segoe UI", 12))
        self._label.pack(side="left", padx=(0, 14))

        for w in (frame, self._dot, self._label):
            w.bind("<Button-1>", self._start_move)
            w.bind("<B1-Motion>", self._on_move)

        self._root.after(50, self._apply_noactivate)
        self._ready.set()
        self._tick()
        self._root.mainloop()

    def _apply_noactivate(self):
        try:
            hwnd = ctypes.windll.user32.GetAncestor(self._root.winfo_id(), _GA_ROOT)
            style = ctypes.windll.user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, _GWL_EXSTYLE, style | _WS_EX_NOACTIVATE | _WS_EX_TOOLWINDOW)
        except Exception:
            pass

    # ---- surukleme ----
    def _start_move(self, e):
        self._dx = e.x_root - self._root.winfo_x()
        self._dy = e.y_root - self._root.winfo_y()

    def _on_move(self, e):
        x = e.x_root - self._dx
        y = e.y_root - self._dy
        self._root.geometry(f"+{x}+{y}")
        self._pos = (x, y)

    # ---- her 100ms: duruma gore goster ----
    def _tick(self):
        if self._state == "rec":
            elapsed = time.monotonic() - self._start
            self._label.config(text=f"REC  {elapsed:0.1f}s")
            on = int(elapsed * 2) % 2 == 0
            self._dot.config(fg="#e64545" if on else "#5a1f1f")  # kirmizi, yanip soner
        elif self._state == "proc":
            n = 1 + int((time.monotonic() - self._proc_start) * 3) % 3
            self._label.config(text=t("ov_processing") + "." * n)
            on = int((time.monotonic() - self._proc_start) * 3) % 2 == 0
            self._dot.config(fg="#e0a020" if on else "#5a4410")  # amber, dones
        self._root.after(100, self._tick)

    # ---- dis API (thread-guvenli) ----
    def show(self):
        self._start = time.monotonic()
        self._state = "rec"
        if self._root:
            self._root.after(0, self._show_window)

    def processing(self):
        """Tus birakildi -> transkript bekleniyor (pencere acik kalir)."""
        self._proc_start = time.monotonic()
        self._state = "proc"

    def _show_window(self):
        self._root.deiconify()
        self._root.update_idletasks()
        w = self._root.winfo_width()
        h = self._root.winfo_height()
        if self._pos:
            x, y = self._pos
        else:
            sw = self._root.winfo_screenwidth()
            sh = self._root.winfo_screenheight()
            x, y = sw - w - 40, sh - h - 90
        self._root.geometry(f"+{x}+{y}")
        self._root.attributes("-topmost", True)

    def hide(self):
        self._state = "idle"
        if self._root:
            self._root.after(0, self._root.withdraw)
