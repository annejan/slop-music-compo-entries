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
import json
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
class Part:
    def __init__(self, bpm):
        self.bpm = bpm
        self.notes = []          # (t, midi, seconds, word)

    def note(self, t, midi, seconds, word):
        self.notes.append((float(t), int(midi), float(seconds), word))

    def score(self, bank, voice, lang="en", hard=False, expr=None, vibrato="5.6:30:250"):
        """warble's JSON score: every note at its own tick (480 a beat), so a lyric can be any word (in the text
        format, a word such as "time" is read as a directive)."""
        notes = []                            # [start, midi, seconds, word]; gaps under 30 ms join the note before
        for t, m, d, w in sorted(self.notes):
            if notes:
                p = notes[-1]
                if t - (p[0] + p[2]) < .03:    # a tiny gap (or an overlap): the earlier note ends where this begins
                    p[2] = max(t - p[0], .01)
            notes.append([t, m, d, w])
        tick = self.bpm / 60 * 480
        out = []
        for t, m, d, w in notes:
            pos = int(round(t * tick))
            n = {"lyric": w, "tone": m, "position": pos, "duration": max(int(round((t + d) * tick)) - pos, 1)}
            if hard:   # hard tuned: the pitch model off, flat on the note (a vibrato on the long ones), like voice.sing
                n["controls"] = {"pts": f"0:0:io,{d * 1000:.0f}:0:io", "snap": 0}
                if d > .3 and vibrato:
                    n["controls"]["vib"] = vibrato
            elif expr is not None:   # the pitch model's expressiveness: 1 its own melody, 0 close to the notes
                n["controls"] = {"expr": float(expr)}
            out.append(n)
        return {"bpm": self.bpm, "tracks": [{"name": "lead", "bank": find_bank(bank), "lang": lang, "voice": voice,
                                             "notes": out}]}

    def render(self, bank="hanami", voice="Fragrance", lang="en", seed=1, level=.12, pitch="free"):
        """The part as mono audio from second 0, the sung parts at about `level` RMS (like voice.sing).
        pitch: "free" (the bank's pitch model), "hard" (flat notes, the model off: the voice locks to the synths),
        or a number 0..1, the model's expressiveness (0.5: half its own scoops and overshoots)."""
        hard = pitch == "hard"
        expr = None if pitch in ("hard", "free") else float(pitch)
        text = json.dumps(self.score(bank, voice, lang, hard=hard, expr=expr), ensure_ascii=False)
        key = hashlib.sha1(f"{text}|{seed}".encode()).hexdigest()[:16]
        path = os.path.join(CACHE, f"ds{key}.npy")
        if os.path.exists(path):
            y = np.load(path)
        else:
            with tempfile.TemporaryDirectory() as tmp:
                src, out = os.path.join(tmp, "part.json"), os.path.join(tmp, "part.wav")
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


def find_bank(name):
    """A bank folder (with dsconfig.yaml) under BANKS whose path contains `name`, case-insensitive; or a path."""
    if os.path.isdir(name):
        return os.path.abspath(name)
    for root, dirs, files in sorted(os.walk(BANKS)):
        if "dsconfig.yaml" in files and "character.yaml" in files and name.lower() in root.lower():
            return root
    raise FileNotFoundError(f"no DiffSinger bank matching {name!r} under {BANKS}")


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
