"""Irminsul read aloud: the Kokoro voice helper (28 Oct 2026). Started by src/speech.js with Kokoro's own Python.

Works like Piper's --output_dir mode, so the extension treats both the same: read one sentence per line on stdin,
write it as a WAV file in --output_dir, print the file's path on stdout. The voice model loads once, at the start.
"""
import argparse
import os
import sys

import soundfile as sf
from kokoro_onnx import Kokoro


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--voices', required=True)
    ap.add_argument('--voice', default='af_sky')
    ap.add_argument('--speed', type=float, default=1.0)
    ap.add_argument('--lang', default='en-us')
    ap.add_argument('--output_dir', required=True)
    a = ap.parse_args()
    os.makedirs(a.output_dir, exist_ok=True)
    k = Kokoro(a.model, a.voices)
    speed = min(2.0, max(0.5, a.speed))
    n = 0
    for line in sys.stdin:
        text = line.strip()
        if not text:
            continue
        audio, rate = k.create(text, voice=a.voice, speed=speed, lang=a.lang)
        path = os.path.join(a.output_dir, 'kokoro-%d-%d.wav' % (os.getpid(), n))
        n += 1
        sf.write(path, audio, rate)
        sys.stdout.write(path + '\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
