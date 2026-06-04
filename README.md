# Voice Dictation

Push-to-talk voice dictation for Windows. Hold a key, speak, and your speech is
transcribed (Deepgram) and pasted into whatever window is focused — terminal,
editor, chat, anything. Runs quietly in the **system tray**. Spoken language and
UI language are both selectable.

## Download
Grab the ready-to-run **`VoiceDictate.exe`** from the
[**latest release**](https://github.com/sanwhere/voice-dictation/releases/latest)
— no Python needed. Run it, then right-click the tray icon → Settings to enter your
own Deepgram API key.

> 💸 **Cost:** Deepgram gives **$200 of free credit** to new accounts, and dictation
> usage is tiny — talking all day costs roughly a cent. There is **no LLM/API cost** at all.

## Features
- 🎙️ Push-to-talk dictation (default key **F8**, configurable, with a "capture key" button)
- 📋 Pastes into the focused window via clipboard (handles non-ASCII/Turkish chars cleanly)
- 🌍 Spoken language selectable, including **auto-detect** (e.g. mixed Turkish/English)
- 🇹🇷/🇬🇧 UI language: Turkish or English
- 🖥️ System tray app — right-click to change settings, no console window
- 🔴 On-screen recording indicator while you speak — draggable, with a live seconds counter
- 🚀 Optional "Start with Windows" autostart
- 🔑 No Anthropic/LLM cost — only uses Deepgram for speech-to-text ($200 free credit for new Deepgram accounts; real usage is a tiny fraction of a cent)

## Languages

**Interface (UI) languages:** Turkish (`tr`) and English (`en`) — switchable in Settings.

**Spoken / recognized languages:** powered by Deepgram. Set a specific language or
pick **`auto`** to let Deepgram detect it automatically (great when you mix, e.g.,
Turkish and English). Languages selectable in the app include:

`auto` · English (`en`, `en-US`, `en-GB`) · Turkish (`tr`) · Spanish (`es`, `es-419`) ·
French (`fr`, `fr-CA`) · German (`de`) · Italian (`it`) · Portuguese (`pt`, `pt-BR`) ·
Dutch (`nl`) · Russian (`ru`) · Ukrainian (`uk`) · Polish (`pl`) · Swedish (`sv`) ·
Danish (`da`) · Norwegian (`no`) · Finnish (`fi`) · Czech (`cs`) · Slovak (`sk`) ·
Greek (`el`) · Hungarian (`hu`) · Romanian (`ro`) · Indonesian (`id`) · Malay (`ms`) ·
Hindi (`hi`) · Japanese (`ja`) · Korean (`ko`) · Chinese (`zh`) · Arabic (`ar`)

Deepgram supports more languages than the preset list above — see the
[Deepgram languages overview](https://developers.deepgram.com/docs/models-languages-overview)
for the full set. With `auto`, detection works across the supported languages without
changing the setting.

## Quick start (from source)
```powershell
git clone <repo-url>
cd voice-windows-agent
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python tray_app.py
```
On first run, right-click the tray icon → **Settings / Ayarlar** and paste your
Deepgram API key (free tier available at https://console.deepgram.com/).

## Build a standalone .exe
```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name VoiceDictate `
  --collect-all sounddevice --collect-submodules pystray tray_app.py
```
Output: `dist\VoiceDictate.exe` (no Python needed to run it).

## Usage
1. Launch the app (tray icon turns blue = idle).
2. Focus the target window.
3. Hold the push-to-talk key, speak, release. Icon turns **red** while listening;
   a beep means the transcript is ready.
4. Text is pasted (and optionally Enter is pressed). Settings are saved to
   `%APPDATA%\VoiceDictate\settings.json`.

## Settings (tray → Settings)
| Setting | Description |
|--------|-------------|
| Deepgram API key | Your Deepgram key (stored locally only) |
| Push-to-talk key | Any key; use **Capture** to detect a button (`detect_key.py` also helps) |
| Spoken language | `tr`, `en`, … or `auto` (Deepgram language detection) |
| Interface language | `tr` / `en` |
| Auto-paste / Auto-Enter | Paste automatically, optionally submit with Enter |
| Recording indicator | Show a draggable on-screen "● REC" timer while recording |
| Start with Windows | Launch automatically at login (per-user, no admin) |

## Files
| File | Purpose |
|------|---------|
| `tray_app.py` | System-tray app (icon, settings dialog, dictation loop) |
| `dictate.py` | Minimal CLI version (no tray) |
| `stt.py` | Microphone capture + Deepgram transcription |
| `settings_store.py` | Loads/saves settings in `%APPDATA%` |
| `i18n.py` | UI translations (tr/en) |
| `detect_key.py` | Prints the name/scancode of any key you press |
| `config.py` | Defaults and env loading |

`agent.py`, `terminal.py`, `computer_tool.py` are an optional experimental
voice→assistant agent and are **not** needed for dictation.

## Notes
- Global hotkey works regardless of focused window (via the `keyboard` library).
- Run the app from your own interactive session (synthetic paste does not work
  from sandboxed/non-interactive contexts).

## License
MIT
