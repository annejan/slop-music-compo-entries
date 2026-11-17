#!/usr/bin/env python3
"""Master a finished song from another generator (ACE-Step) for the DJ, the same way engine.py masters ours:
the beat grid moved to sample 0, 44.1 kHz, the loudness target under a true-peak ceiling, 16-bit with dither.

master.py IN.wav OUT.wav --bpm 120 [--lufs -10] [--ceiling -1.2]

The beat is found from the kick: the onsets of the 40-120 Hz band, folded onto one beat. The start is cut to the
first beat (a few ms fade in), so the grid starts at sample 0, as in our own renders.
"""
import argparse
import wave

import numpy as np
from scipy import signal

import engine as e


def read(path):
    with wave.open(path) as w:
        sr, ch, n, width = w.getframerate(), w.getnchannels(), w.getnframes(), w.getsampwidth()
        raw = w.readframes(n)
    if width != 2:
        raise ValueError(f"{path}: {width * 8}-bit, expected 16-bit")
    x = np.frombuffer(raw, "<i2").astype(np.float64).reshape(-1, ch) / 32768
    if ch == 1:
        x = np.repeat(x, 2, axis=1)
    return x[:, :2], sr


def beat_phase(x, sr, bpm):
    """Seconds from the start to the first beat of the grid, from the kick onsets."""
    hop = sr // 200
    lo = signal.sosfilt(signal.butter(4, [40, 120], btype="band", fs=sr, output="sos"), x.mean(1))
    env = np.sqrt(np.add.reduceat(lo ** 2, np.arange(0, len(lo) - hop, hop)) / hop)
    onset = np.maximum(np.diff(env), 0)
    beat = 60 / bpm
    t = (np.arange(len(onset)) + 1) * hop / sr
    hist, edges = np.histogram(t % beat, bins=200, range=(0, beat), weights=onset)
    hist = np.convolve(np.r_[hist[-3:], hist, hist[:3]], np.ones(5) / 5, "same")[3:-3]
    return (edges[np.argmax(hist)] + edges[1] / 2) % beat


def master(x, lufs=-10.0, ceiling_db=-1.2):
    ceiling = 10 ** (ceiling_db / 20)
    level = e.integrated_lufs(x)
    for _ in range(4):
        x = e.limit(x * 10 ** ((lufs - level) / 20), ceiling)
        level = e.integrated_lufs(x)
        if abs(level - lufs) < .1:
            break
    for _ in range(3):
        x = e.limit(x, ceiling)
    return x


def write(path, x):
    q = 1 / 32767
    out = np.round((x + (e.rng.random(x.shape) - e.rng.random(x.shape)) * q) * 32767)
    out = np.clip(out, -32767, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(e.SR)
        w.writeframes(out.tobytes())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--bpm", type=float, required=True)
    ap.add_argument("--lufs", type=float, default=-10.0)
    ap.add_argument("--ceiling", type=float, default=-1.2)
    a = ap.parse_args()
    x, sr = read(a.src)
    phase = beat_phase(x, sr, a.bpm)
    x = x[int(round(phase * sr)):]
    if sr != e.SR:
        g = np.gcd(sr, e.SR)
        x = signal.resample_poly(x, e.SR // g, sr // g, axis=0)
    k = int(.004 * e.SR)
    x[:k] *= np.linspace(0, 1, k)[:, None]
    x = master(x, a.lufs, a.ceiling)
    write(a.dst, x)
    tp = 20 * np.log10(e.true_peak(x).max())
    m, s = divmod(len(x) / e.SR, 60)
    print(f"wrote {a.dst}: {int(m)}:{s:04.1f}, grid moved {phase * 1000:.0f} ms, "
          f"{e.integrated_lufs(x):.1f} LUFS, {tp:+.1f} dBTP")
