"""Bas-konus (F8) dongusu + Claude computer-use agent loop.

Akis: F8 basili tut -> Turkce konus -> Deepgram STT -> (onayli mod) sesli onay
-> Claude computer-use agent dongusu (ekrani gorur, fare/klavye surer)
-> edge-tts ile Turkce sesli sonuc.
"""
import sys
import time

# Windows konsolu cp1252 olabilir; Turkce karakter print'i cokmesin diye UTF-8'e zorla.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import keyboard
from anthropic import Anthropic

import config
import stt
import tts
import safety
from computer_tool import ComputerTool


def _final_text(content_blocks) -> str:
    parts = [b.text for b in content_blocks if getattr(b, "type", None) == "text" and b.text]
    return " ".join(parts).strip()


def _blocks_to_dicts(content_blocks):
    """SDK blok nesnelerini messages'a eklemek icin dict'e cevir."""
    out = []
    for b in content_blocks:
        t = getattr(b, "type", None)
        if t == "text":
            out.append({"type": "text", "text": b.text})
        elif t == "tool_use":
            out.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
        # diger blok tipleri (thinking vb.) gerekirse burada eklenir
    return out


def run_command(client: Anthropic, computer: ComputerTool, command: str) -> str:
    messages = [{"role": "user", "content": command}]
    tool = computer.tool_param()
    last_text = ""

    for _ in range(config.MAX_ITERS):
        resp = client.beta.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=config.SYSTEM_PROMPT,
            tools=[tool],
            messages=messages,
            betas=[config.COMPUTER_USE_BETA],
        )

        text = _final_text(resp.content)
        if text:
            last_text = text
            print(f"   [MODEL] {text}")

        messages.append({"role": "assistant", "content": _blocks_to_dicts(resp.content)})

        tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        if not tool_uses or resp.stop_reason != "tool_use":
            break

        tool_results = []
        for tu in tool_uses:
            if tu.name == "computer":
                result = computer.execute(tu.id, tu.input)
            else:
                result = {
                    "type": "tool_result", "tool_use_id": tu.id, "is_error": True,
                    "content": [{"type": "text", "text": f"Bilinmeyen arac: {tu.name}"}],
                }
            tool_results.append(result)

        messages.append({"role": "user", "content": tool_results})

    return last_text or "İşlem tamamlandı."


def handle_turn(client, computer):
    # 1) Komutu dinle
    command = stt.listen()
    if not command:
        tts.speak("Sizi duyamadım.")
        return
    print(f"[KOMUT] {command}")

    # 2) Onay: sadece riskli (yikici/geri alinamaz) komutlarda sesli onay iste
    risky = config.CONFIRM_MODE and safety.is_risky(command)
    if risky:
        print("[RISKLI] Onay gerekiyor.")
        tts.speak(f"{command}. Bu işlem geri alınamayabilir, onaylıyor musun?")
        print("[ONAY] F8 ile evet/hayir soyleyin...")
        # Onay icin tekrar F8 bekle
        if not _wait_hotkey(timeout=15):
            tts.speak("Onay alamadım, iptal ettim.")
            return
        answer = stt.listen()
        print(f"[ONAY METNI] {answer}")
        if not safety.is_approval(answer):
            tts.speak("İptal ettim.")
            return
        tts.speak("Tamam, yapıyorum.")
    else:
        tts.speak("Tamam.")

    # 3) Agent dongusu
    try:
        result = run_command(client, computer, command)
    except Exception as e:
        print(f"[HATA] {e}")
        tts.speak("Bir hata oluştu.")
        return

    print(f"[SONUC] {result}")
    tts.speak(result)


def _wait_hotkey(timeout=None) -> bool:
    """Hotkey basilana kadar bekler. timeout (sn) varsa zaman asiminda False."""
    start = time.monotonic()
    while True:
        if keyboard.is_pressed(config.PTT_HOTKEY):
            return True
        if timeout is not None and (time.monotonic() - start) > timeout:
            return False
        time.sleep(0.03)


def main():
    if not config.ANTHROPIC_API_KEY:
        print("HATA: ANTHROPIC_API_KEY .env dosyasinda tanimli degil.")
        sys.exit(1)
    if not config.DEEPGRAM_API_KEY:
        print("HATA: DEEPGRAM_API_KEY .env dosyasinda tanimli degil.")
        sys.exit(1)

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    computer = ComputerTool()
    print(f"Ekran: {computer.real_w}x{computer.real_h} -> gonderilen {computer.sent_w}x{computer.sent_h} "
          f"(scale={computer.scale:.4f}), model={config.MODEL}")
    print(f"Bas-konus tusu: {config.PTT_HOTKEY.upper()} | Onayli mod: {'acik' if config.CONFIRM_MODE else 'kapali'}")
    print("Imleci ekranin sol-ust kosesine goturursen ACIL DURUR (failsafe).")

    tts.speak("Hazırım.")
    print("Hazirim. F8'e basili tutup Turkce konusun. Cikis: Ctrl+C")

    try:
        while True:
            if keyboard.is_pressed(config.PTT_HOTKEY):
                handle_turn(client, computer)
                # Tus birakilana kadar bekle (cift tetiklemeyi onle)
                while keyboard.is_pressed(config.PTT_HOTKEY):
                    time.sleep(0.05)
                print("\nHazirim. (F8)")
            time.sleep(0.03)
    except KeyboardInterrupt:
        print("\nKapatiliyor.")


if __name__ == "__main__":
    main()
