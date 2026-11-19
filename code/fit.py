#!/usr/bin/env python3
"""How a free ACE-Step take fits our band: its sung notes (pyworld's f0, loudness-weighted) against the band's chord
tones bar by bar, for key shifts and whole-bar offsets; and whether it ends mid-word. Offline, CPU, about 2 s a take.

fit.py TAKE.wav [TAKE.wav ...] --bpm 104 --chords "Bm Em A F#"
fit.py TAKE.wav --bpm 128 --chords "Bm Em A F#" --snap natural|hard [--shift 0 --offset 0]   retune onto the chords

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


def snap(wav, chords, bpm, out, mode="natural", shift=0, offset=0, scale_only=False):
    """The take retuned onto the band (WORLD: f0 changed, spectral envelope and aperiodicity kept, the length frame-
    exact, so the take stays on the grid). Each steady note (the nearest semitone of the smoothed f0 held for 30 ms
    or more) moves to the nearest tone of the chord of the bar under it (a long note) or of the song's scale (a short
    one, under an eighth), at most 2 semitones; glides between notes follow. mode "natural": the note moves as a
    whole and keeps its own vibrato and scoops; "hard": the pitch sits flat on the target note and jumps between
    notes (the "Cher" eurodance effect, retune speed 0). shift: semitones first (fit.py's key shift); offset: whole
    bars (the take placed that many bars later against the chords). Returns `out`."""
    from scipy.ndimage import median_filter
    x, sr = master.read(wav)
    x = x.mean(1).astype(np.float64)
    fp = 5.0
    f0, t = pw.dio(x, sr, f0_floor=90, f0_ceil=1100, frame_period=fp)
    f0 = pw.stonemask(x, f0, t, sr)
    sp = pw.cheaptrick(x, f0, t, sr)
    ap = pw.d4c(x, f0, t, sr)
    v = f0 > 0
    m = np.full(len(f0), np.nan)
    m[v] = 69 + 12 * np.log2(f0[v] / 440) + shift
    ms = m.copy()
    if v.any():
        ms[v] = median_filter(m[v], 9)
    bar = 240 / bpm
    member = [chord_pcs(c) for c in chords]
    scale = set().union(*member)
    # segments: runs of frames on one nearest semitone (blips of up to 20 ms ignored)
    segs, i = [], 0
    while i < len(ms):
        if np.isnan(ms[i]):
            i += 1
            continue
        cur, j = round(ms[i]), i
        while j + 1 < len(ms) and not np.isnan(ms[j + 1]) and round(ms[j + 1]) == cur:
            j += 1
        segs.append((i, j))
        i = j + 1
    delta = np.full(len(ms), np.nan)
    target = np.full(len(ms), np.nan)
    eighth = 60 / bpm / 2 * .85
    for i, j in segs:
        length = (j - i + 1) * fp / 1000
        if length < .03:
            continue
        centre = float(np.median(m[i:j + 1]))
        k = (int(t[(i + j) // 2] / bar) + offset) % len(chords)
        allowed = scale if (length < eighth or scale_only) else member[k]
        cands = [n for n in range(int(round(centre)) - 2, int(round(centre)) + 3) if n % 12 in allowed]
        if not cands:
            continue
        tgt = min(cands, key=lambda n: abs(n - centre))
        delta[i:j + 1] = tgt - centre
        target[i:j + 1] = tgt
    # frames between segments (glides, short blips) take the delta of their neighbours, interpolated
    have = ~np.isnan(delta)
    if have.any():
        idx = np.arange(len(delta))
        delta = np.interp(idx, idx[have], delta[have])
        target_f = np.interp(idx, idx[have], target[have])
    else:
        delta = np.zeros(len(ms))
        target_f = ms
    if mode == "hard":
        new = np.where(have, target, np.round(target_f))
    else:
        new = m + delta
    f0n = np.where(v, 440 * 2 ** ((new - 69) / 12), 0.0)
    y = pw.synthesize(f0n, sp, ap, sr, frame_period=fp)
    y = np.pad(y, (0, max(0, len(x) - len(y))))[:len(x)]
    y = y * (np.sqrt(np.mean(x ** 2)) / (np.sqrt(np.mean(y ** 2)) + 1e-9))
    _write(out, y, sr)
    return out


def _write(path, y, sr):
    """Mono 16-bit WAV at the take's own rate (master.write writes our 44.1 kHz)."""
    import wave
    z = (np.clip(y, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(z.tobytes())


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
    ap.add_argument("--snap", choices=["natural", "hard"], help="retune each take onto the chords (WORLD), "
                    "written next to it as <take>_snap_<mode>.wav")
    ap.add_argument("--shift", type=int, default=0, help="snap: semitones first")
    ap.add_argument("--offset", type=int, default=0, help="snap: whole bars")
    a = ap.parse_args()
    if a.snap:
        for t in a.takes:
            print(snap(t, a.chords.split(), a.bpm, f"{t[:-4]}_snap_{a.snap}.wav", a.snap, a.shift, a.offset))
        return
    for r in rank(a.takes, a.chords.split(), a.bpm):
        print(f"{r[0].split('/')[-1]}: {describe(r)}")


if __name__ == "__main__":
    main()
