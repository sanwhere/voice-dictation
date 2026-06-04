"""Ekran goruntusu + tum computer-use aksiyonlari + koordinat olcekleme + keysym map.

Windows'a ozgu:
- SetProcessDPIAware: mss ve pyautogui fiziksel pikseli ayni gormeli.
- Ekran goruntusu mss ile (monitors[1] = birincil).
- type: TR karakterler icin pyperclip + ctrl+v (config ile kapatilabilir).
- Claude X-keysym dondurebilir; pyautogui tuslarina cevrilir.
"""
import base64
import ctypes
import io
import time

import mss
import pyautogui
import pyperclip
from PIL import Image

import config

pyautogui.FAILSAFE = True  # imleci kose'ye goturunce acil dur
pyautogui.PAUSE = 0.05

# DPI farkindaligi (tiklamalar kaymasin)
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

# X keysym -> pyautogui tus adi
KEYSYM_MAP = {
    "Return": "enter", "KP_Enter": "enter",
    "Escape": "esc",
    "BackSpace": "backspace",
    "Tab": "tab",
    "space": "space", "Space": "space",
    "Delete": "delete",
    "Insert": "insert",
    "Home": "home", "End": "end",
    "Page_Up": "pageup", "Prior": "pageup",
    "Page_Down": "pagedown", "Next": "pagedown",
    "Up": "up", "Down": "down", "Left": "left", "Right": "right",
    "super": "win", "Super_L": "win", "Super_R": "win", "Meta_L": "win",
    "Control_L": "ctrl", "Control_R": "ctrl", "ctrl": "ctrl", "control": "ctrl",
    "Alt_L": "alt", "Alt_R": "alt", "alt": "alt",
    "Shift_L": "shift", "Shift_R": "shift", "shift": "shift",
    "Caps_Lock": "capslock",
    "Menu": "apps",
    "Print": "printscreen",
    "minus": "-", "plus": "+", "equal": "=",
    "comma": ",", "period": ".", "slash": "/", "backslash": "\\",
    "semicolon": ";", "apostrophe": "'",
    "bracketleft": "[", "bracketright": "]",
}
for _i in range(1, 25):
    KEYSYM_MAP[f"F{_i}"] = f"f{_i}"


def _map_key(k: str) -> str:
    return KEYSYM_MAP.get(k, k.lower() if len(k) > 1 else k)


class ComputerTool:
    def __init__(self):
        with mss.mss() as sct:
            mon = sct.monitors[1]  # birincil ekran
            self.real_w = mon["width"]
            self.real_h = mon["height"]
            self.mon = dict(mon)

        long_edge = max(self.real_w, self.real_h)
        if long_edge > config.MAX_LONG_EDGE:
            self.scale = config.MAX_LONG_EDGE / long_edge
        else:
            self.scale = 1.0
        self.sent_w = round(self.real_w * self.scale)
        self.sent_h = round(self.real_h * self.scale)

    # --- API'ye gonderilecek arac tanimi ---
    def tool_param(self):
        return {
            "type": config.COMPUTER_TOOL_TYPE,
            "name": "computer",
            "display_width_px": self.sent_w,
            "display_height_px": self.sent_h,
            "display_number": 1,
            "enable_zoom": True,
        }

    # --- Koordinat cevrimi: olceklenmis (Claude) -> gercek ekran pikseli ---
    def _to_real(self, x, y):
        if self.scale == 0:
            return int(x), int(y)
        rx = int(round(x / self.scale))
        ry = int(round(y / self.scale))
        rx = max(0, min(self.real_w - 1, rx))
        ry = max(0, min(self.real_h - 1, ry))
        return rx, ry

    # --- Ekran goruntusu (olceklenmis PNG base64) ---
    def screenshot_b64(self, region=None) -> str:
        with mss.mss() as sct:
            shot = sct.grab(self.mon)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        if region:
            # region gercek piksel: (left, top, w, h)
            l, t, w, h = region
            img = img.crop((l, t, l + w, t + h))
        if self.scale != 1.0 and not region:
            img = img.resize((self.sent_w, self.sent_h), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")

    def _image_result(self, tool_use_id, b64):
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": [{
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": b64},
            }],
        }

    # --- Tek bir aksiyonu calistir, sonuc olarak yeni screenshot dondur ---
    def execute(self, tool_use_id, action_input: dict):
        action = action_input.get("action")
        text = action_input.get("text")
        coord = action_input.get("coordinate")
        modifiers = self._modifiers(text)

        # Hata ayiklama: ajanin gercekte ne yaptigini terminale yaz
        _info = action
        if coord:
            _info += f" @{tuple(coord)}->{self._to_real(*coord)}"
        if text:
            _info += f" text={text!r}"
        print(f"   [ACTION] {_info}")

        try:
            if action == "screenshot":
                pass

            elif action == "mouse_move":
                x, y = self._to_real(*coord)
                pyautogui.moveTo(x, y)

            elif action in ("left_click", "right_click", "middle_click",
                            "double_click", "triple_click"):
                if coord:
                    x, y = self._to_real(*coord)
                    pyautogui.moveTo(x, y)
                button = {"left_click": "left", "right_click": "right",
                          "middle_click": "middle", "double_click": "left",
                          "triple_click": "left"}[action]
                clicks = {"double_click": 2, "triple_click": 3}.get(action, 1)
                self._with_mods(modifiers, lambda: pyautogui.click(button=button, clicks=clicks))

            elif action == "left_click_drag":
                start = action_input.get("start_coordinate")
                if start:
                    sx, sy = self._to_real(*start)
                    pyautogui.moveTo(sx, sy)
                ex, ey = self._to_real(*coord)
                self._with_mods(modifiers, lambda: pyautogui.dragTo(ex, ey, duration=0.3, button="left"))

            elif action == "left_mouse_down":
                if coord:
                    x, y = self._to_real(*coord)
                    pyautogui.moveTo(x, y)
                pyautogui.mouseDown(button="left")

            elif action == "left_mouse_up":
                if coord:
                    x, y = self._to_real(*coord)
                    pyautogui.moveTo(x, y)
                pyautogui.mouseUp(button="left")

            elif action == "type":
                self._type(text or "")

            elif action == "key":
                self._key(text or "")

            elif action == "hold_key":
                duration = float(action_input.get("duration", 1))
                k = _map_key((text or "").strip())
                pyautogui.keyDown(k)
                time.sleep(duration)
                pyautogui.keyUp(k)

            elif action == "scroll":
                if coord:
                    x, y = self._to_real(*coord)
                    pyautogui.moveTo(x, y)
                direction = action_input.get("scroll_direction", "down")
                amount = int(action_input.get("scroll_amount", 3))
                clicks = amount * 100
                self._with_mods(modifiers, lambda: self._do_scroll(direction, clicks))

            elif action == "wait":
                duration = float(action_input.get("duration", 1))
                time.sleep(min(duration, 5))

            elif action == "zoom":
                region = self._zoom_region(action_input)
                b64 = self.screenshot_b64(region=region)
                return self._image_result(tool_use_id, b64)

            else:
                # Bilinmeyen aksiyon: yine de screenshot don
                pass

            time.sleep(0.4)  # UI'nin oturmasi icin
            b64 = self.screenshot_b64()
            return self._image_result(tool_use_id, b64)

        except Exception as e:
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "is_error": True,
                "content": [{"type": "text", "text": f"Aksiyon hatasi ({action}): {e}"}],
            }

    # --- Yardimcilar ---
    def _modifiers(self, text):
        """Tiklama/scroll'da gelen modifier 'text' alanini ayikla."""
        if not text:
            return []
        mods = []
        for part in str(text).replace("+", " ").split():
            m = _map_key(part)
            if m in ("ctrl", "shift", "alt", "win"):
                mods.append(m)
        return mods

    def _with_mods(self, mods, fn):
        for m in mods:
            pyautogui.keyDown(m)
        try:
            fn()
        finally:
            for m in reversed(mods):
                pyautogui.keyUp(m)

    def _do_scroll(self, direction, clicks):
        if direction == "up":
            pyautogui.scroll(clicks)
        elif direction == "down":
            pyautogui.scroll(-clicks)
        elif direction == "left":
            pyautogui.hscroll(-clicks)
        elif direction == "right":
            pyautogui.hscroll(clicks)

    def _type(self, text):
        if config.TYPE_VIA_CLIPBOARD:
            old = None
            try:
                old = pyperclip.paste()
            except Exception:
                pass
            pyperclip.copy(text)
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.1)
            if old is not None:
                try:
                    pyperclip.copy(old)
                except Exception:
                    pass
        else:
            pyautogui.write(text, interval=0.01)

    def _key(self, text):
        # "ctrl+s" gibi kombolar
        parts = [_map_key(p) for p in str(text).split("+") if p]
        if not parts:
            return
        if len(parts) == 1:
            pyautogui.press(parts[0])
        else:
            pyautogui.hotkey(*parts)

    def _zoom_region(self, action_input):
        # region [x,y,w,h] olceklenmis gelebilir; coordinate merkez olabilir
        region = action_input.get("region")
        if region and len(region) == 4:
            l, t, w, h = region
            return (int(l / self.scale), int(t / self.scale),
                    int(w / self.scale), int(h / self.scale))
        coord = action_input.get("coordinate")
        if coord:
            cx, cy = self._to_real(*coord)
            half_w, half_h = self.real_w // 4, self.real_h // 4
            l = max(0, cx - half_w)
            t = max(0, cy - half_h)
            return (l, t, min(half_w * 2, self.real_w - l), min(half_h * 2, self.real_h - t))
        return None
