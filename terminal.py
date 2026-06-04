"""Kalici PowerShell oturumu. Komut gonderir, ciktiyi sentinel ile toplar.

Ekran/fare yok; komutlar dogrudan bir PowerShell alt sureci uzerinden calisir.
cd, degiskenler, ortam oturum boyunca korunur (gercek bir terminal gibi)."""
import os
import queue
import shutil
import subprocess
import threading
import time

_SENTINEL = "<<<__CMD_DONE_8f3a2c__>>>"


class TerminalSession:
    def __init__(self, cwd=None):
        self.exe = shutil.which("pwsh") or shutil.which("powershell") or "powershell"
        self.proc = subprocess.Popen(
            [self.exe, "-NoLogo", "-NoProfile"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd or os.path.expanduser("~"),
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        self._q = queue.Queue()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self._init_session()

    def _read_loop(self):
        for line in self.proc.stdout:
            self._q.put(line.rstrip("\r\n"))
        self._q.put(None)  # EOF

    def _send(self, text):
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def _init_session(self):
        # Prompt'u sustur, ilerleme cubuklarini kapat, UTF-8 cikti
        self._send("function prompt { '' }")
        self._send("$ProgressPreference = 'SilentlyContinue'")
        self._send("[Console]::OutputEncoding = [System.Text.Encoding]::UTF8")
        # Kurulum ciktisini bosalt (sentinel'e kadar oku, at)
        self.run("Write-Output 'hazir'", timeout=15)

    def run(self, command: str, timeout: int = 60) -> str:
        """Komutu calistirir, ciktiyi (stdout+stderr) string olarak dondurur."""
        self._send(command)
        # Komuttan sonra cikis kodu + sentinel yaz
        self._send(f"Write-Output ('{_SENTINEL}:' + [string]$LASTEXITCODE)")

        lines = []
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                lines.append("[zaman asimi: komut hala calisiyor olabilir]")
                break
            try:
                line = self._q.get(timeout=min(remaining, 0.5))
            except queue.Empty:
                continue
            if line is None:
                lines.append("[oturum kapandi]")
                break
            if line.startswith(_SENTINEL):
                break
            lines.append(line)

        # Bos prompt satirlarini kirp
        out = "\n".join(lines).strip("\n")
        return out.strip()

    def close(self):
        try:
            self._send("exit")
        except Exception:
            pass
        try:
            self.proc.terminate()
        except Exception:
            pass
