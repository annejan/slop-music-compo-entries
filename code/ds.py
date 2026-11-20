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

    def render(self, bank="hanami", voice="Fragrance", lang="en", seed=1, level=.12, pitch="free", timbre=None):
        """The part as mono audio from second 0, the sung parts at about `level` RMS (like voice.sing).
        pitch: "free" (the bank's pitch model), "hard" (flat notes, the model off: the voice locks to the synths),
        or a number 0..1, the model's expressiveness (0.5: half its own scoops and overshoots).
        timbre: another singer for the same performance (convert()): a voice.CAST name or voice ("maya_diva",
        "qwen_diva", ...) or a WAV of the voice. The notes, words and timing stay the score's."""
        y = self._sing(bank, voice, lang, seed, pitch)
        if timbre:
            y = convert(y, timbre)
        env = np.sqrt(np.convolve(y ** 2, np.ones(2048) / 2048, "same"))
        sung = env > .1 * env.max()
        rms = np.sqrt(np.mean(y[sung] ** 2)) if sung.any() else 1.0
        return y * (level / (rms + 1e-9))

    def _sing(self, bank, voice, lang, seed, pitch):
        """warble's raw take of the part (cached)."""
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
        return y


def find_bank(name):
    """A bank folder (with dsconfig.yaml) under BANKS whose path contains `name`, case-insensitive; or a path."""
    if os.path.isdir(name):
        return os.path.abspath(name)
    for root, dirs, files in sorted(os.walk(BANKS)):
        if "dsconfig.yaml" in files and "character.yaml" in files and name.lower() in root.lower():
            return root
    raise FileNotFoundError(f"no DiffSinger bank matching {name!r} under {BANKS}")


# ---------------------------------------------------------------- another singer for the same performance
# SoulX-Singer SVC (audio.cpp, Vulkan, behind the GPU lock): the take's pitch, timing and words, the reference's
# voice. The reference of a TTS voice is a spoken clip of it (SVC takes the timbre, not the manner). 24 kHz out.
SVC_CLI = os.path.expanduser("~/Projects/audiocpp-src/build/bin/audiocpp_cli")
SVC_MODEL = os.path.expanduser("~/Projects/audiocpp-models/SoulX-Singer-SVC-GGUF/soulx-singer-svc-q8_0.gguf")
SVC_STEPS = 32
REF_TEXT = ("Tonight the lights are low, and the music takes me home. I can feel it in my heart, every beat, every "
            "word, every single night.")


def reference(timbre):
    """A WAV of the voice: the path itself, or REF_TEXT said by a voice.CAST name or voice (cached)."""
    if os.path.exists(timbre):
        return timbre
    import voice as V
    key = hashlib.sha1(f"{timbre}|{REF_TEXT}".encode()).hexdigest()[:16]
    path = os.path.join(CACHE, f"ref{key}.wav")
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        _write(path, V._finish(V.tts(REF_TEXT, timbre)))
    return path


def convert(y, timbre, steps=SVC_STEPS):
    """The take `y` (mono, SR) sung again in the voice of `timbre` (reference()): SoulX-Singer SVC; cached."""
    import ace
    ref = reference(timbre)
    key = hashlib.sha1(y.tobytes() + open(ref, "rb").read() + str(steps).encode()).hexdigest()[:16]
    path = os.path.join(CACHE, f"svc{key}.npy")
    if os.path.exists(path):
        return np.load(path)
    peak = np.abs(y).max() + 1e-9
    z = np.zeros(len(y))
    for i, j in sung(y):        # only the sung stretches: a song's part is mostly silence, and SVC time is length
        with tempfile.TemporaryDirectory() as tmp:
            src, out, log = (os.path.join(tmp, n) for n in ("src.wav", "out.wav", "svc.log"))
            _write(src, y[i:j] / peak * .8)
            if not ace.gpu([SVC_CLI, "--task", "svc", "--family", "soulx_singer", "--model", SVC_MODEL, "--backend",
                            "vulkan", "--device", "0", "--threads", "8", "--audio", src, "--voice-ref", ref,
                            "--request-option", f"num_steps={steps}", "--out", out], log, 3600):
                raise RuntimeError(f"SoulX SVC failed:\n{open(log, errors='replace').read()[-2000:]}")
            seg = _read(out)
        z[i:j] = np.pad(seg, (0, max(0, j - i - len(seg))))[:j - i]
    z = z * (peak / .8)
    os.makedirs(CACHE, exist_ok=True)
    np.save(path, z)
    return z


def sung(y, gap=2.0, pad=.3):
    """(from, to) sample ranges where `y` sings: silences longer than `gap` seconds left out, `pad` s kept around."""
    env = np.sqrt(np.convolve(y ** 2, np.ones(2205) / 2205, "same"))
    on = np.flatnonzero(env > .01 * (env.max() + 1e-12))
    if not len(on):
        return []
    spans, a, b = [], on[0], on[0]
    for k in on[1:]:
        if k - b > gap * SR:
            spans.append((a, b))
            a = k
        b = k
    spans.append((a, b))
    p = int(pad * SR)
    return [(max(0, a - p), min(len(y), b + p)) for a, b in spans]


def _write(path, y):
    z = (np.clip(y, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(z.tobytes())


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
