"""Tus dedektoru: bastigin tusun/butonun adini ve scancode'unu yazar.

Bunu KENDI terminalinde calistir, sonra mikrofon butonuna bas.
Cikan 'name=' veya 'sc<kod>' degerini .env icindeki PTT_HOTKEY'e yazariz.
Cikis: ESC.
"""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import keyboard


def main():
    print("=== Tus Dedektoru ===")
    print("Bir tusa ya da mikrofon butonuna bas. Her basis burada gorunur.")
    print("Cikis: ESC\n")

    def on_event(e):
        if e.event_type == "down":
            name = e.name if e.name else "<isimsiz>"
            print(f"  name={name!r}   scancode={e.scan_code}   ->  .env'de PTT_HOTKEY={name!r} "
                  f"(ya da scancode icin 'sc{e.scan_code}') olarak kullanabilirsin")

    keyboard.hook(on_event)
    keyboard.wait("esc")
    print("\nCikiliyor.")


if __name__ == "__main__":
    main()
