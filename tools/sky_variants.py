"""Irminsul: brighter, fairy-like versions of Kokoro Sky (28 Oct 2026). Our own sound shaping, no game audio.

The trick: Kokoro speaks Sky a little slower, then the whole clip is raised in pitch, which also brings the speed back to normal.
Speech stays natural (no chipmunk), and the voice sounds smaller and brighter, like a little companion.
    "%LOCALAPPDATA%\\Irminsul\\kokoro\\venv\\Scripts\\python.exe" tools\\sky_variants.py
"""
import os
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

BASE = Path(os.environ['LOCALAPPDATA']) / 'Irminsul'
OUT = BASE / 'samples'
LINE = ('Irminsul is your own theme for Visual Studio Code. The world tree holds all knowledge, '
        'and tonight, it reads aloud for you. Next up: go over real files together.')

# (file name, semitones higher). 2 semitones is a small lift; 6 is a small, bright fairy.
VARIANTS = [('sky-brighter', 2), ('sky-fairy', 4), ('sky-tiny-fairy', 6)]


def pitch_up(audio, semitones):
    """Raise pitch (and speed) by resampling in the frequency domain, which keeps it clean: no aliasing hiss."""
    f = 2 ** (semitones / 12)
    n = len(audio)
    new_n = int(round(n / f))
    spec = np.fft.rfft(audio)
    out = np.fft.irfft(spec[:new_n // 2 + 1], new_n) * (new_n / n)
    return out.astype(np.float32)


def shape(audio, semitones, rate):
    """Raise the pitch and add a tiny brightness lift above 2.5 kHz, then fade the ends so nothing clicks."""
    out = pitch_up(audio, semitones)
    spec = np.fft.rfft(out)
    freqs = np.fft.rfftfreq(len(out), 1 / rate)
    spec *= 1 + 0.12 * np.clip((freqs - 2500) / 4000, 0, 1) * semitones / 4
    out = np.fft.irfft(spec, len(out))
    fade = int(rate * 0.01)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(out)) or 1
    return (out / peak * 0.89).astype(np.float32)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    k = Kokoro(str(BASE / 'kokoro' / 'kokoro-v1.0.onnx'), str(BASE / 'kokoro' / 'voices-v1.0.bin'))
    for name, st in VARIANTS:
        speed = 1 / 2 ** (st / 12)  # spoken slower by exactly what the pitch step speeds it up
        audio, rate = k.create(LINE, voice='af_sky', speed=speed, lang='en-us')
        out = shape(audio, st, rate)
        sf.write(OUT / (name + '.wav'), out, rate)
        print('%s: +%d semitones, %.1f s' % (name, st, len(out) / rate))


if __name__ == '__main__':
    main()
