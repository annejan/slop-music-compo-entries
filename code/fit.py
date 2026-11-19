#!/usr/bin/env python3
"""How a free ACE-Step take fits our band: its sung notes (pyworld's f0, loudness-weighted) against the band's chord
tones bar by bar, for key shifts and whole-bar offsets; and whether it ends mid-word. Offline, CPU, about 2 s a take.

fit.py TAKE.wav [TAKE.wav ...] --bpm 104 --chords "Bm Em A F#"

Why (research/toolkit-2026-11-19.md): ACE-Step gets the key only as text, so a take comes back in the asked key about
one time in five (22 % of 166 takes), and an a cappella take never hears the chords. Today's Hi-NRG take sat on the
kit's chord tones 4-5 % of its long notes as laid, and 75 % one bar earlier. A number is not the ear: Uptime Fever's
approved take measures poorly. So the ranking decides what the user hears FIRST, never what is used.

--bpm is the tempo the take was SUNG at (with takes.py --lift: the slower one); the chords are one a bar, repeating
from the take's first downbeat. A shift of s moves the take s semitones up (Rubber Band -p s); an offset of -1 places
the take one bar earlier against the chords.
"""
import argparse
from math import gcd

import numpy as np
import pyworld as pw
from scipy import signal

import engine as e
import master

FS = 16000
_TRACKS = {}


def pitch_track(wav):
    """(t seconds, midi note per 10 ms frame (nan where unvoiced), loudness weight), tuned to the nearest semitone
    grid (a take a few cents sharp counts as in tune). Cached per path."""
    if wav in _TRACKS:
        return _TRACKS[wav]
    x, sr = master.read(wav)
    x = x.mean(1).astype(np.float64)
    g = gcd(sr, FS)
    y = signal.resample_poly(x, FS // g, sr // g)
    f0, t = pw.dio(y, FS, f0_floor=90, f0_ceil=1100, frame_period=10)
    f0 = pw.stonemask(y, f0, t, FS)
    hop = FS // 100
    w = np.array([np.sqrt(np.mean(y[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(y) else 0 for i in range(len(t))])
    v = f0 > 0
    m = np.full(len(t), np.nan)
    m[v] = 69 + 12 * np.log2(f0[v] / 440)
    if v.any():
        cents = (m[v] - np.round(m[v])) * 100
        tune = np.degrees(np.angle(np.mean(np.exp(1j * np.radians(cents * 3.6))))) / 3.6
        m[v] -= tune / 100
    _TRACKS[wav] = (t, m, np.where(v, w, 0.0))
    return _TRACKS[wav]


def chord_pcs(name):
    """The chord's pitch classes (engine.chord: "Bm", "F#", "Em9", "Dm7", ...)."""
    root, iv = e.chord(name)
    return {(root + i) % 12 for i in iv}


def steady_notes(wav, min_frames=6):
    """The take's steady notes: (mid time s, length s, midi, loudness), where the nearest semitone of the median-
    smoothed f0 holds for at least `min_frames` 10 ms frames (blips under 40 ms ignored). Glides, consonants and
    vibrato swings drop out: every voiced frame counted, the fit drowned in noise (19 November)."""
    from scipy.ndimage import median_filter
    t, m, w = pitch_track(wav)
    v = ~np.isnan(m)
    ms = m.copy()
    if v.any():
        ms[v] = median_filter(m[v], 5)
    notes, i = [], 0
    while i < len(ms):
        if np.isnan(ms[i]):
            i += 1
            continue
        cur, j = round(ms[i]), i
        while j + 1 < len(ms) and not np.isnan(ms[j + 1]):
            if round(ms[j + 1]) != cur:
                k = j + 1
                while k < len(ms) and k - j <= 4 and not np.isnan(ms[k]) and round(ms[k]) != cur:
                    k += 1
                if k - j > 4 or k >= len(ms) or np.isnan(ms[k]):
                    break
            j += 1
        if j - i + 1 >= min_frames:
            notes.append(((t[i] + t[j]) / 2, (j - i + 1) * .01, cur, float(w[i:j + 1].mean())))
        i = j + 1
    return notes


def band_fit(wav, chords, bpm, shifts=range(-5, 7), offsets=(-1, 0, 1)):
    """How the take's steady notes (weighted by length and loudness) sit on the band. Two measures that must agree:
    the SCALE fit (on any of the song's notes) picks the key shift, then the CHORD fit (on the tones of the chord of
    the bar under the note) picks the whole-bar offset at that shift. Returns a dict: best (shift, offset), fit (the
    chord fit there), as_is (shift 0, offset 0), scale (the scale fit at the shift), table {(s, o): chord fit}."""
    notes = steady_notes(wav)
    if not notes:
        return dict(best=(0, 0), fit=0.0, as_is=0.0, scale=0.0, table={}, notes=0)
    bar = 240 / bpm
    member = np.zeros((len(chords), 12))
    for k, c in enumerate(chords):
        member[k, list(chord_pcs(c))] = 1
    scale = member.max(0)
    mid = np.array([n[0] for n in notes])
    pitch = np.array([n[2] for n in notes])
    wt = np.array([n[1] * n[3] for n in notes])
    wt = wt / wt.sum()
    bars = np.floor(mid / bar).astype(int)
    table, on_scale = {}, {}
    for s in shifts:
        pc = (pitch + s) % 12
        on_scale[s] = float(wt @ scale[pc])
        for o in offsets:
            table[(s, o)] = float(wt @ member[(bars + o) % len(chords), pc])
    s = max(on_scale, key=lambda k: on_scale[k] - .015 * abs(k))
    o = max(offsets, key=lambda k: table[(s, k)] - .03 * abs(k))
    return dict(best=(s, o), fit=table[(s, o)], as_is=table[(0, 0)], scale=on_scale[s], table=table,
                notes=len(notes))


def cut_end(wav, tail=.25):
    """True when the take is still loud in its last `tail` seconds: ACE-Step stopped mid-word (it truncates the
    duration to whole seconds and the LM stops about 0.8 s early; 14 of 137 takes on disk)."""
    x, sr = master.read(wav)
    x = x.mean(1)
    hop = sr // 100
    env = np.sqrt(np.add.reduceat(x ** 2, np.arange(0, len(x) - hop, hop)) / hop)
    loud = np.percentile(env, 90) + 1e-9
    return float(env[-int(tail * 100):].mean() / loud) > .3


def rank(wavs, chords, bpm, **kw):
    """The takes best-first: (wav, band_fit dict, cut_end), a cut word costing 5 points of fit."""
    rows = [(w, band_fit(w, chords, bpm, **kw), cut_end(w)) for w in wavs]
    return sorted(rows, key=lambda r: -(r[1]["fit"] - .05 * r[2]))


def describe(r):
    w, f, cut = r
    s, o = f["best"]
    where = {0: "", -1: ", one bar earlier", 1: ", one bar later"}.get(o, f", {o:+d} bars")
    return (f"fit {f['fit']:.0%} at {s:+d} st{where} (as made {f['as_is']:.0%}; on the scale {f['scale']:.0%})"
            f"{'; ENDS MID-WORD' if cut else ''}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("takes", nargs="+")
    ap.add_argument("--bpm", type=float, required=True, help="the tempo the take was sung at")
    ap.add_argument("--chords", required=True, help='one a bar, repeating: "Bm Em A F#"')
    a = ap.parse_args()
    for r in rank(a.takes, a.chords.split(), a.bpm):
        print(f"{r[0].split('/')[-1]}: {describe(r)}")


if __name__ == "__main__":
    main()
