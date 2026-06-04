"""edge-tts (bedava Turkce noral ses) + pygame ile oynatma. ffmpeg gerektirmez."""
import asyncio
import os
import tempfile

import edge_tts
import pygame

import config

_mixer_ready = False


def _ensure_mixer():
    global _mixer_ready
    if not _mixer_ready:
        pygame.mixer.init()
        _mixer_ready = True


async def _synthesize(text: str, path: str):
    communicate = edge_tts.Communicate(text, config.TTS_VOICE, rate=config.TTS_RATE)
    await communicate.save(path)


def speak(text: str):
    """Metni Turkce seslendirir ve bitene kadar bekler."""
    if not text:
        return
    text = text.strip()[: config.TTS_MAX_CHARS]
    if not text:
        return

    _ensure_mixer()
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        asyncio.run(_synthesize(text, path))
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(20)
        pygame.mixer.music.unload()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
