#!/usr/bin/env python3
"""Weave the slop through the slop: our own instrumental, unchanged, under a blend of our vocals (Piper and WORLD,
the machine flow) and the same vocals cleaned up by another generator (ACE-Step's cover of our vocal stem).

weave.py INST.wav OURVOX.wav OTHERVOX.wav FULL.wav OUT.wav --bpm 134 [--ace 0.5] [--lufs -9]

INST and OURVOX are our stems (SOLO=drums,perc,bass,pads,keys,lead,fx and SOLO=vox), FULL our full render; OTHERVOX
the other generator's take of OURVOX (any sample rate). The other take is lined up to ours by cross-correlation and
gated by our vocal envelope, so it adds nothing where our voices are silent. The balance of vocals against music
is fitted to FULL. --ace sets the share of the other take in the vocals (0: ours only, 1: the other only).
"""
import argparse

import numpy as np
from scipy import signal

import engine as e
import master


def envelope_lag(x, ours, start=30.0, seconds=90.0, lo=200, hi=4000):
    """Seconds by which x runs late against ours (both at engine.SR): the cross-correlation of the onset strength
    of the vocal band, 1 ms frames."""
    def env(a):
        seg = a[int(start * e.SR):int((start + seconds) * e.SR)].mean(1)
        band = signal.sosfilt(signal.butter(4, [lo, hi], btype="band", fs=e.SR, output="sos"), seg)
        h = e.SR // 1000
        v = np.log(np.sqrt(np.add.reduceat(band ** 2, np.arange(0, len(band) - h, h)) / h) + 1e-6)
        d = np.maximum(np.diff(v), 0)
        return d - d.mean()
    a, b = env(x), env(ours)
    c = signal.correlate(a, b, "full", method="fft")
    lags = np.arange(-len(b) + 1, len(a))
    ok = np.abs(lags) < 250
    return lags[ok][np.argmax(c[ok])] / 1000


def gate(x, ours, release=.15):
    """x only where ours sings: our vocal envelope (fast attack, `release` seconds of release) as a gain, 0..1."""
    lv = np.abs(ours).max(1)
    a = int(.003 * e.SR)
    env = np.convolve(lv, np.ones(a) / a, "same")
    # held open for `release` after our voice, then smoothed: open on our voice, close soon after it stops
    hold = int(release * e.SR)
    held = signal.convolve(env > .02 * env.max(), np.ones(hold), "full")[:len(env)] > 0
    g = e.one_pole(held.astype(float), .01)
    return x * g[:, None]


def fit_gains(full, inst, vox):
    """a, b with full ~ a * inst + b * vox (least squares over the whole song)."""
    A = np.stack([inst.ravel(), vox.ravel()], 1)
    (a, b), *_ = np.linalg.lstsq(A, full.ravel(), rcond=None)
    return a, b


def process(inst, ourvox, othervox, full, out, bpm, ace=.5, lufs=-9.0):
    """The whole job (see the module docstring). Returns a one-line report."""
    inst, _ = master.read(inst)
    ours, _ = master.read(ourvox)
    full, _ = master.read(full)
    other, sr = master.read(othervox)
    if sr != e.SR:
        g = np.gcd(sr, e.SR)
        other = signal.resample_poly(other, e.SR // g, sr // g, axis=0)
    lag = envelope_lag(other, ours, start=16 * 240 / bpm)
    other = other[int(round(lag * e.SR)):] if lag >= 0 else np.concatenate([np.zeros((int(round(-lag * e.SR)), 2)), other])
    n = min(len(inst), len(ours), len(full))
    other = np.concatenate([other, np.zeros((max(n - len(other), 0), 2))])[:n]
    inst, ours, full = inst[:n], ours[:n], full[:n]
    other = gate(other, ours)
    other *= np.sqrt(np.mean(ours ** 2) / (np.mean(other ** 2) + 1e-12))     # the same loudness as our vocals
    ka, kb = fit_gains(full, inst, ours)
    mix = master.master(ka * inst + kb * ((1 - ace) * ours + ace * other), lufs)
    master.write(out, mix)
    tp = 20 * np.log10(e.true_peak(mix).max())
    return (f"wrote {out}: other take {lag * 1000:+.0f} ms, vocals {ace:.0%} other, {e.integrated_lufs(mix):.1f} LUFS, "
            f"{tp:+.1f} dBTP")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for name in ("inst", "ourvox", "othervox", "full", "out"):
        ap.add_argument(name)
    ap.add_argument("--bpm", type=float, required=True)
    ap.add_argument("--ace", type=float, default=.5, help="share of the other take in the vocals, 0..1")
    ap.add_argument("--lufs", type=float, default=-9.0)
    a = ap.parse_args()
    print(process(a.inst, a.ourvox, a.othervox, a.full, a.out, a.bpm, a.ace, a.lufs))
