#!/usr/bin/env python3
"""Vocal effects for a dry sung part (ds.Part.render, a converted singer, an ACE take): the producer's rack.

    y = vfx.vocoder(voice, S, chords)          the voice's formants on a saw-chord carrier: the 80s/90s vocoder
    y = vfx.autotune(voice, chords, bpm)       retuned onto the chords: "hard" (the Cher effect) or "natural"
    y = vfx.harmony(voice, [12, 7])            stacked copies a fixed interval up (+) or down (-), Rubber Band
    st = vfx.stack([(lead, .5, 1, 0), (double, .15, .5, 12), (double2, .85, .5, 19)])   doubles and stacks, stereo

All take and return mono arrays at engine.SR, from second 0 of the song (like ds.Part.render), so they drop into
S.put("vox", 0.0, y, ...). The CLI renders an A/B file: vfx.py IN.wav --bpm 134 --chords "Em C G D" --vocoder.
"""
import os
import subprocess
import sys
import tempfile

import numpy as np
from scipy import signal

import engine as e

SR = e.SR


def _bands(n=28, lo=80.0, hi=12000.0):
    """Band edges, evenly spaced on the mel scale."""
    mel = lambda f: 2595 * np.log10(1 + f / 700)      # noqa: E731
    imel = lambda m: 700 * (10 ** (m / 2595) - 1)       # noqa: E731
    return imel(np.linspace(mel(lo), mel(hi), n + 1))


def carrier(chords, bpm, seconds, key_of=None, lo=48, hi=72, detune=.12):
    """A bright saw-chord pad, one chord a bar from second 0 (chords repeat): the vocoder's instrument. Every chord
    tone between midi `lo` and `hi`, three slightly detuned saws each."""
    bar = 240 / bpm
    n = int(seconds * SR)
    out = np.zeros(n)
    t0 = 0
    k = 0
    while t0 < n:
        t1 = min(n, int((k + 1) * bar * SR))
        c = chords[k % len(chords)]
        root, iv = e.chord(*c) if isinstance(c, tuple) else e.chord(c)     # a name, or (name, key shift)
        notes = sorted({m for m in range(lo, hi + 1) if (m - root) % 12 in {i % 12 for i in iv}})
        t = np.arange(t1 - t0) / SR
        seg = np.zeros(t1 - t0)
        for m in notes:
            f = 440 * 2 ** ((m - 69) / 12)
            for d in (-detune, 0, detune):
                ph = (f * 2 ** (d / 12) * t + np.random.rand()) % 1
                seg += 2 * ph - 1
        out[t0:t1] = seg / max(1, len(notes))
        t0, k = t1, k + 1
    return out


def vocoder(voice, chords, bpm, bands=28, sibilance=.35, carrier_wav=None):
    """A channel vocoder: the voice's band envelopes (mel bands, 80 Hz-12 kHz) shape a carrier (default: a saw
    chord pad on `chords`, one a bar). The voice's own hiss above 5 kHz is mixed back so consonants stay clear."""
    voice = np.asarray(voice, float)
    car = carrier(chords, bpm, len(voice) / SR) if carrier_wav is None else carrier_wav[:len(voice)]
    car = np.pad(car, (0, len(voice) - len(car)))
    edges = _bands(bands)
    env_lp = signal.butter(2, 50, "low", fs=SR, output="sos")
    out = np.zeros(len(voice))
    for a, b in zip(edges[:-1], edges[1:]):
        sos = signal.butter(4, [a, min(b, SR / 2 - 100)], "band", fs=SR, output="sos")
        v = signal.sosfilt(sos, voice)
        c = signal.sosfilt(sos, car)
        env = signal.sosfilt(env_lp, np.abs(v))
        cen = signal.sosfilt(env_lp, np.abs(c)) + 1e-4
        out += c * env / cen
    hiss = signal.sosfilt(signal.butter(4, 5000, "high", fs=SR, output="sos"), voice)
    out += sibilance * hiss
    return out * (np.sqrt(np.mean(voice ** 2)) / (np.sqrt(np.mean(out ** 2)) + 1e-9))


def _tmp_wav(y, path):
    import master
    master.write(path, np.repeat((np.clip(y, -1, 1))[:, None], 2, axis=1))


def autotune(voice, chords, bpm, mode="hard", offset=0):
    """The voice retuned onto the chords with fit.snap (WORLD): "hard" (flat notes, the Cher effect) or "natural"
    (each note moved, its vibrato kept). bpm: the song's; the chords one a bar from second 0."""
    import fit
    import takes
    peak = np.abs(voice).max() + 1e-9
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "in.wav"), os.path.join(d, "out.wav")
        _tmp_wav(voice / peak * .8, src)
        fit.snap(src, chords, bpm, dst, mode=mode, offset=offset)
        y = takes.mono(dst)
    y = np.pad(y, (0, max(0, len(voice) - len(y))))[:len(voice)]
    return y * peak / .8


def harmony(voice, intervals=(12,), amps=None, formant=True):
    """The voice plus copies `intervals` semitones away (Rubber Band, formants kept: no chipmunks), each at its
    amp (default .5)."""
    import takes
    amps = amps or [.5] * len(intervals)
    out = np.array(voice, float)
    peak = np.abs(voice).max() + 1e-9
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "in.wav")
        _tmp_wav(voice / peak * .8, src)
        for iv, a in zip(intervals, amps):
            dst = os.path.join(d, f"h{iv}.wav")
            subprocess.run(["rubberband", "-3", "-q", "-p", str(iv)] + (["-F"] if formant else []) + [src, dst],
                           check=True, capture_output=True)
            y = takes.mono(dst)
            out += a * np.pad(y, (0, max(0, len(voice) - len(y))))[:len(voice)] * peak / .8
    return out


def stack(layers, sr=SR):
    """Voices stacked into one stereo part: layers of (mono, pan 0..1, amp, delay ms). Real doubles are other takes
    (ds.Part.render(seed=2), another timbre), not copies: a copy only phases. A few ms of delay and a wide pan keep
    them apart; the lead in the middle, louder."""
    n = max(len(y) + int(abs(d) * sr / 1000) for y, _, _, d in layers)
    out = np.zeros((n, 2))
    for y, pan, amp, d in layers:
        k = int(d * sr / 1000)
        g = np.array([np.cos(pan * np.pi / 2), np.sin(pan * np.pi / 2)]) * amp
        out[k:k + len(y)] += np.asarray(y)[:, None] * g
    return out


def main():
    import argparse
    import master
    import takes
    ap = argparse.ArgumentParser(description="a vocal effect on a dry WAV, written next to it")
    ap.add_argument("wav")
    ap.add_argument("--bpm", type=float, required=True)
    ap.add_argument("--chords", required=True, help='one a bar from the start: "Em C G D"')
    ap.add_argument("--vocoder", action="store_true")
    ap.add_argument("--autotune", choices=["hard", "natural"])
    ap.add_argument("--harmony", help="semitones, comma separated: 12,7")
    a = ap.parse_args()
    y = takes.mono(a.wav)
    tag = ""
    if a.autotune:
        y, tag = autotune(y, a.chords.split(), a.bpm, a.autotune), tag + "_tune" + a.autotune
    if a.vocoder:
        y, tag = vocoder(y, a.chords.split(), a.bpm), tag + "_vocoder"
    if a.harmony:
        y, tag = harmony(y, [int(v) for v in a.harmony.split(",")]), tag + "_harm"
    out = a.wav[:-4] + (tag or "_dry") + ".wav"
    master.write(out, np.repeat((y / (np.abs(y).max() + 1e-9) * .8)[:, None], 2, axis=1))
    print(out)


if __name__ == "__main__":
    sys.exit(main())
