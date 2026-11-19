#!/usr/bin/env python3
"""ACE-voiced sampler chops: the 1990s house vocal stab, all AI-made. Words cut from an ACE-Step a cappella take
(faster-whisper's word times), each tuned with WORLD to the tone of the bar's chord nearest its own pitch, played
from a 16-step pattern like a sampler's pads (a chop stops where the next one starts). research/toolkit-2026-11-19.md.

  b = chops.bank("renders/ace/takes/menu/house-diva_s1_68d3f1ab.wav", {"hold", "on", "tight", "night"})
  chops.play(S, bar, b, "hold . . on . . tight . . . night . . . . .", chord="Am9")

chops.py TAKE.wav       the words faster-whisper hears in a take, with their times
"""
import functools
import sys
from math import gcd

import numpy as np
import pyworld as pw
from scipy import signal

import engine as e
import master


@functools.lru_cache(maxsize=None)
def words(wav):
    """[(word, start s, end s)] of a take, lower case, without punctuation (faster-whisper base.en, CPU)."""
    from faster_whisper import WhisperModel
    m = WhisperModel("base.en", device="cpu", compute_type="int8")
    x, sr = master.read(wav)                # as an array: our av rejects faster-whisper's file-open arguments
    g = gcd(sr, 16000)
    y = signal.resample_poly(x.mean(1), 16000 // g, sr // g).astype(np.float32)
    segs, _ = m.transcribe(y, word_timestamps=True)
    return [(w.word.strip(" ,.!?;:'\"").lower(), w.start, w.end) for s in segs for w in s.words]


def bank(wav, want=None, pad=.03):
    """{word: mono audio at our rate}: the first time each word is sung in the take (only the words in `want`, if
    given), with `pad` seconds either side and 5 ms fades."""
    x, sr = master.read(wav)
    x = x.mean(1).astype(np.float64)
    if sr != e.SR:
        g = gcd(sr, e.SR)
        x = signal.resample_poly(x, e.SR // g, sr // g)
    out = {}
    for w, t0, t1 in words(wav):
        if (want and w not in want) or w in out:
            continue
        a, b = int(max(t0 - pad, 0) * e.SR), int(min(t1 + pad, len(x) / e.SR) * e.SR)
        y = x[a:b].copy()
        f = min(int(.005 * e.SR), len(y) // 2)
        if f:
            y[:f] *= np.linspace(0, 1, f)
            y[-f:] *= np.linspace(1, 0, f)
        out[w] = y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * .1
    return out


def _world(y):
    f0, t = pw.dio(y, e.SR, f0_floor=90, f0_ceil=1100, frame_period=5)
    f0 = pw.stonemask(y, f0, t, e.SR)
    return f0, pw.cheaptrick(y, f0, t, e.SR), pw.d4c(y, f0, t, e.SR)


def pitch(y):
    """The chop's median pitch (MIDI), or None when nothing in it is voiced."""
    f0, _, _ = _world(y)
    v = f0 > 0
    return float(np.median(69 + 12 * np.log2(f0[v] / 440))) if v.any() else None


_TUNED = {}


def tune(word, y, midi):
    """The chop moved so that its median pitch sits on `midi` (WORLD; its own vibrato and scoops kept, the length
    kept). Cached per word and note."""
    k = (word, len(y), round(midi))
    if k not in _TUNED:
        f0, sp, ap = _world(y)
        v = f0 > 0
        if not v.any():
            _TUNED[k] = y
        else:
            cur = np.median(69 + 12 * np.log2(f0[v] / 440))
            z = pw.synthesize(f0 * 2 ** ((round(midi) - cur) / 12), sp, ap, e.SR, frame_period=5)
            z = np.pad(z, (0, max(0, len(y) - len(z))))[:len(y)]
            _TUNED[k] = z * (np.sqrt(np.mean(y ** 2)) / (np.sqrt(np.mean(z ** 2)) + 1e-9))
    return _TUNED[k]


def target(own, chord, key=0):
    """The tone of the chord nearest the chop's own pitch (a chop moves at most a tritone)."""
    root, iv = e.chord(chord, key)
    tones = {(root + i) % 12 for i in iv}
    return min((n for n in range(int(own) - 6, int(own) + 7) if n % 12 in tones), key=lambda n: abs(n - own))


def play(S, bar, chops, pattern, chord, key=0, amp=1.0, pan=.5, wet=.25, echo=.2, bus="vox", swing=0.0):
    """One bar of a chop pattern: 16 tokens, "." a rest, a word plays its chop from that sixteenth, tuned to the
    chord; a chop is cut (8 ms fade) where the next token starts, so the stabs stay tight. swing: seconds late for
    the off sixteenths (a swung song's own swing)."""
    if not S.live(bar):
        return
    toks = pattern.split()
    assert len(toks) == 16, pattern
    hits = [(k, w) for k, w in enumerate(toks) if w != "."]
    for n, (k, w) in enumerate(hits):
        y = chops.get(w)
        if y is None:
            continue
        own = pitch(y)
        z = tune(w, y, target(own, chord, key)) if own is not None else y
        nxt = hits[n + 1][0] if n + 1 < len(hits) else 16 + (hits[0][0] if hits else 0)
        cut = int((nxt - k) * S.step * e.SR)
        z = z[:cut].copy()
        f = min(int(.008 * e.SR), len(z) // 2)
        if f:
            z[-f:] *= np.linspace(1, 0, f)
        S.put(bus, S.at(bar) + k * S.step + (swing if k % 2 else 0.0), z, pan, amp, wet=wet, echo=echo)


if __name__ == "__main__":
    for w, t0, t1 in words(sys.argv[1]):
        print(f"{t0:6.2f}-{t1:6.2f}  {w}")
