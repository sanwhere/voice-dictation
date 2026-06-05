"""Kayit gostergesi: surukleneblir, saniye sayacli, ust uste duran kucuk pencere.

- O an AKTIF olan monitorde (on plandaki pencerenin bulundugu ekran) belirir.
- Bir kosesine sabitlenir (sag-ust, sol-ust, ...); surukleyince hangi kose +
  ne kadar bosluk istedigini hatirlar ve sonraki seferlerde AKTIF monitorde ayni
  koseye yerlesir.
- Pencere odagi ASLA almaz (WS_EX_NOACTIVATE) -> yapistirma hedef pencereye gider.
- Kendi thread'inde bir Tk root calistirir; show()/hide() thread-guvenli."""
import ctypes
from ctypes import wintypes
import threading
import time
import tkinter as tk

import config
import settings_store
from i18n import t

_user32 = ctypes.windll.user32

# Win32 imza tanimlari (64-bit handle'lar dogru gecsin)
_HWND = ctypes.c_void_p
_user32.GetAncestor.restype = _HWND
_user32.GetAncestor.argtypes = [_HWND, ctypes.c_uint]
_user32.SetWindowPos.restype = ctypes.c_bool
_user32.SetWindowPos.argtypes = [_HWND, _HWND, ctypes.c_int, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_int, ctypes.c_uint]
_HWND_TOPMOST = ctypes.c_void_p(-1)
_SWP_NOSIZE = 0x0001
_SWP_NOACTIVATE = 0x0010

_GWL_EXSTYLE = -20
_WS_EX_NOACTIVATE = 0x08000000
_WS_EX_TOOLWINDOW = 0x00000080
_GA_ROOT = 2
_MONITOR_DEFAULTTONEAREST = 2


class _RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class _MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", _RECT),
                ("rcWork", _RECT), ("dwFlags", ctypes.c_ulong)]


def _work_rect(hmon):
    mi = _MONITORINFO()
    mi.cbSize = ctypes.sizeof(_MONITORINFO)
    if _user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
        r = mi.rcWork
        return (r.left, r.top, r.right, r.bottom)
    return (0, 0, _user32.GetSystemMetrics(0), _user32.GetSystemMetrics(1))


def _active_monitor_rect():
    """On plandaki pencerenin bulundugu monitorun calisma alani."""
    hwnd = _user32.GetForegroundWindow()
    hmon = _user32.MonitorFromWindow(hwnd, _MONITOR_DEFAULTTONEAREST)
    return _work_rect(hmon)


def _point_monitor_rect(x, y):
    pt = wintypes.POINT(int(x), int(y))
    hmon = _user32.MonitorFromPoint(pt, _MONITOR_DEFAULTTONEAREST)
    return _work_rect(hmon)


class RecordingOverlay:
    def __init__(self):
        self._state = "idle"   # idle | rec | proc
        self._start = 0.0
        self._proc_start = 0.0
        self._root = None
        self._hwnd = None
        self._target_rect = None
        # Kose + bosluk (ayarlardan; surukleyince guncellenir)
        self._corner = getattr(config, "OVERLAY_CORNER", "br")
        self._inset = (getattr(config, "OVERLAY_INSET_X", 40),
                       getattr(config, "OVERLAY_INSET_Y", 90))
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
            w.bind("<ButtonRelease-1>", self._end_move)

        self._root.after(50, self._apply_noactivate)
        self._ready.set()
        self._tick()
        self._root.mainloop()

    def _apply_noactivate(self):
        try:
            hwnd = _user32.GetAncestor(self._root.winfo_id(), _GA_ROOT)
            self._hwnd = hwnd
            style = _user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
            _user32.SetWindowLongW(hwnd, _GWL_EXSTYLE, style | _WS_EX_NOACTIVATE | _WS_EX_TOOLWINDOW)
        except Exception:
            pass

    def _move_hwnd(self, x, y):
        """Pencereyi mutlak (negatif olabilir) ekran konumuna tasi - Win32 ile."""
        hwnd = self._hwnd
        if not hwnd:
            try:
                hwnd = _user32.GetAncestor(self._root.winfo_id(), _GA_ROOT)
            except Exception:
                hwnd = None
        if hwnd:
            try:
                _user32.SetWindowPos(hwnd, _HWND_TOPMOST, int(x), int(y), 0, 0,
                                     _SWP_NOSIZE | _SWP_NOACTIVATE)
                return
            except Exception:
                pass
        try:
            self._root.geometry(f"+{int(x)}+{int(y)}")
        except Exception:
            pass

    # ---- surukleme: canli tasi, birakinca kose+boslugu hatirla ----
    def _start_move(self, e):
        self._dx = e.x_root - self._root.winfo_x()
        self._dy = e.y_root - self._root.winfo_y()

    def _on_move(self, e):
        x = e.x_root - self._dx
        y = e.y_root - self._dy
        self._move_hwnd(x, y)

    def _end_move(self, e):
        x = self._root.winfo_x()
        y = self._root.winfo_y()
        w = self._root.winfo_width()
        h = self._root.winfo_height()
        left, top, right, bottom = _point_monitor_rect(x + w // 2, y + h // 2)
        horiz = "l" if (x + w / 2 - left) < (right - (x + w / 2)) else "r"
        vert = "t" if (y + h / 2 - top) < (bottom - (y + h / 2)) else "b"
        self._corner = vert + horiz   # "tl","tr","bl","br"
        mx = (x - left) if horiz == "l" else (right - (x + w))
        my = (y - top) if vert == "t" else (bottom - (y + h))
        self._inset = (max(0, int(mx)), max(0, int(my)))
        self._persist()

    def _persist(self):
        try:
            s = settings_store.load()
            s["overlay_corner"] = self._corner
            s["overlay_inset_x"], s["overlay_inset_y"] = self._inset
            settings_store.save(s)
            config.OVERLAY_CORNER = self._corner
            config.OVERLAY_INSET_X, config.OVERLAY_INSET_Y = self._inset
        except Exception:
            pass

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
        # AKTIF monitoru SIMDI yakala (overlay gosterilmeden once)
        try:
            self._target_rect = _active_monitor_rect()
        except Exception:
            self._target_rect = None
        # ayarlardan guncel kose/boslugu al
        self._corner = getattr(config, "OVERLAY_CORNER", self._corner)
        self._inset = (getattr(config, "OVERLAY_INSET_X", self._inset[0]),
                       getattr(config, "OVERLAY_INSET_Y", self._inset[1]))
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
        rect = self._target_rect or (0, 0, self._root.winfo_screenwidth(), self._root.winfo_screenheight())
        left, top, right, bottom = rect
        mx, my = self._inset
        x = (left + mx) if "l" in self._corner else (right - w - mx)
        y = (top + my) if "t" in self._corner else (bottom - h - my)
        self._root.attributes("-topmost", True)
        self._move_hwnd(x, y)
        # pencere tam map olduktan sonra bir kez daha uygula (ilk cagri tutmayabilir)
        self._root.after(20, lambda: self._move_hwnd(x, y))

    def hide(self):
        self._state = "idle"
        if self._root:
            self._root.after(0, self._root.withdraw)
