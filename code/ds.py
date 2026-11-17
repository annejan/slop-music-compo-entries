"""DiffSinger voices: a whole vocal part sung by a DiffSinger voicebank, through warble (a small singing engine,
MIT, https://github.com/erz0r/warble) and its ONNX models, on the CPU.

Not part of the repository's setup: warble and the voicebanks live outside it (see README, "DiffSinger"). Set
WARBLE to warble's executable and WARBLE_BANKS to the folder with the banks, or keep the defaults below.

    part = ds.Part(bpm=132)
    part.note(t_seconds, midi, seconds, "segfault")   # a word on a note
    part.note(t, midi, seconds, "+")                  # the word goes on over the next note
    y = part.render(bank="hanami", voice="Fragrance")  # mono, 44.1 kHz, from second 0 of the song

The voicebank's own duration and pitch models place the consonants before the note and shape the pitch between
the notes, so the vowel lands on the beat. The result is cached in .cache/.
"""
import hashlib
import os
import subprocess
import tempfile
import wave

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".cache")
HOME = os.path.expanduser("~/Projects/diffsinger")
WARBLE = os.environ.get("WARBLE", os.path.join(HOME, "warble", ".venv", "bin", "warble"))
BANKS = os.environ.get("WARBLE_BANKS", os.path.join(HOME, "banks"))
SR = 44100
NAMES = "C C# D D# E F F# G G# A A# B".split()


def note_name(m):
    m = int(round(m))
    return f"{NAMES[m % 12]}{m // 12 - 1}"


class Part:
    def __init__(self, bpm):
        self.bpm = bpm
        self.notes = []          # (t, midi, seconds, word)

    def note(self, t, midi, seconds, word):
        self.notes.append((float(t), int(midi), float(seconds), word))

    def score(self, bank, voice, lang="en"):
        """warble's plain-text score: every note and rest in milliseconds, from second 0."""
        lines = [f"bpm {self.bpm}", "track lead", f"bank {bank}", f"lang {lang}", f"voice {voice}"]
        notes = []                            # [start, midi, seconds, word]; gaps under 30 ms join the note before
        for t, m, d, w in sorted(self.notes):
            if notes:
                p = notes[-1]
                gap = t - (p[0] + p[2])
                if gap < .03:                 # a tiny gap (or an overlap): the earlier note ends where this begins
                    p[2] = max(t - p[0], .01)
            notes.append([t, m, d, w])
        now = 0.0
        for t, m, d, w in notes:
            if t > now + .0005:
                lines.append(f"r {(t - now) * 1000:.1f}ms")
            lines.append(f"{w} {note_name(m)} {d * 1000:.1f}ms")
            now = t + d
        return "\n".join(lines) + "\n"

    def render(self, bank="hanami", voice="Fragrance", lang="en", seed=1, level=.12):
        """The part as mono audio from second 0, the sung parts at about `level` RMS (like voice.sing)."""
        text = self.score(bank, voice, lang)
        key = hashlib.sha1(f"{text}|{seed}".encode()).hexdigest()[:16]
        path = os.path.join(CACHE, f"ds{key}.npy")
        if os.path.exists(path):
            y = np.load(path)
        else:
            with tempfile.TemporaryDirectory() as tmp:
                src, out = os.path.join(tmp, "part.txt"), os.path.join(tmp, "part.wav")
                with open(src, "w") as fh:
                    fh.write(text)
                env = dict(os.environ, WARBLE_BANKS=BANKS)
                r = subprocess.run([WARBLE, "sing", src, "-o", out, "--seed", str(seed)], env=env,
                                   capture_output=True, text=True)
                if r.returncode:
                    raise RuntimeError(f"warble failed:\n{r.stderr[-2000:]}\n{r.stdout[-2000:]}")
                y = _read(out)
            os.makedirs(CACHE, exist_ok=True)
            np.save(path, y)
        env = np.sqrt(np.convolve(y ** 2, np.ones(2048) / 2048, "same"))
        sung = env > .1 * env.max()
        rms = np.sqrt(np.mean(y[sung] ** 2)) if sung.any() else 1.0
        return y * (level / (rms + 1e-9))


def _read(path):
    with wave.open(path) as w:
        sr, ch, n, width = w.getframerate(), w.getnchannels(), w.getnframes(), w.getsampwidth()
        raw = w.readframes(n)
    if width == 2:
        x = np.frombuffer(raw, "<i2").astype(np.float64) / 32768
    elif width == 4:
        x = np.frombuffer(raw, "<i4").astype(np.float64) / 2 ** 31
    else:
        raise ValueError(f"{path}: {width * 8}-bit audio")
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    if sr != SR:
        g = np.gcd(sr, SR)
        x = signal.resample_poly(x, SR // g, sr // g)
    return x
