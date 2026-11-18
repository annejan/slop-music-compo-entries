#!/usr/bin/env python3
"""Master a finished song from another generator (ACE-Step) for the DJ, the same way engine.py masters ours:
the beat grid moved to sample 0, 44.1 kHz, the loudness target under a true-peak ceiling, 16-bit with dither.

master.py IN.wav OUT.wav --bpm 120 [--lufs -10] [--ceiling -1.2] [--era 90s] [--dj-from OURS.wav --bars 120]

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


def lag_to(x, sr, ours, start=30.0, seconds=90.0):
    """Seconds by which x (at sr) runs late against ours (at engine.SR), negative if early: the cross-correlation of
    the onset strength (the rise of the log envelope) of the kick band, 1 ms frames, `seconds` long from `start` (after
    the DJ intro: ACE-Step's intro may not follow ours)."""
    def env(a, rate):
        seg = a[int(start * rate):int((start + seconds) * rate)].mean(1)
        lo = signal.sosfilt(signal.butter(4, [40, 150], btype="band", fs=rate, output="sos"), seg)
        h = rate // 1000
        v = np.log(np.sqrt(np.add.reduceat(lo ** 2, np.arange(0, len(lo) - h, h)) / h) + 1e-6)
        d = np.maximum(np.diff(v), 0)
        return d - d.mean()
    if sr != e.SR:                                  # the same frame length on both sides (44 samples is not 1 ms)
        g = np.gcd(sr, e.SR)
        x = signal.resample_poly(x[:int((start + seconds + 1) * sr)], e.SR // g, sr // g, axis=0)
    a, b = env(x, e.SR), env(ours, e.SR)
    c = signal.correlate(a, b, "full", method="fft")
    lags = np.arange(-len(b) + 1, len(a))
    ok = np.abs(lags) < 250
    return lags[ok][np.argmax(c[ok])] / 1000


def splice_dj(x, ours, bpm, bars, dj_bars=16):
    """The DJ intro and outro (drums only) from our own render, the other take in between: ACE-Step does not keep
    to "drums only" and sometimes drops out in the intro. Both start on the beat grid at sample 0. Ours is matched
    to the take's level around each join, with a one-beat equal-power crossfade on the downbeat."""
    beat = 60 / bpm
    f = int(round(beat * e.SR))
    n = min(len(x), len(ours))
    x, ours = x[:n].copy(), ours[:n]
    rms = lambda a, i0, i1: np.sqrt(np.mean(a[max(i0, 0):i1] ** 2) + 1e-12)
    u = np.linspace(0, 1, f)[:, None]
    fade_out, fade_in = np.cos(u * np.pi / 2), np.sin(u * np.pi / 2)
    span = int(8 * beat * e.SR)
    j = int(round(dj_bars * 4 * beat * e.SR))                      # the intro: ours up to bar dj_bars
    g = min(rms(x, j - span, j) / rms(ours, j - span, j), rms(x, j, j + span) / rms(ours, j, j + span))
    x[:j - f] = ours[:j - f] * g
    x[j - f:j] = ours[j - f:j] * g * fade_out + x[j - f:j] * fade_in
    j = int(round((bars - dj_bars) * 4 * beat * e.SR))             # the outro: ours from bar bars - dj_bars
    g = rms(x, j - span, j) / rms(ours, j - span, j)
    x[j:j + f] = x[j:j + f] * fade_out + ours[j:j + f] * g * fade_in
    x[j + f:] = ours[j + f:] * g
    return x


def era_90s(x):
    """Make a modern-sounding mix sit in a 90s club: a narrower stereo image, less of the deep sub, the top end
    rolled off from about 15 kHz (DAT, CD and radio of the time, and samplers at 32 kHz), a soft tape saturation."""
    mid, side = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    side = e.highpass(side, 200) * .65                             # narrower, and the lows in the middle
    x = np.stack([mid + side, mid - side], 1)
    sub = e.lowpass(x, 45, order=2)
    x = x - .45 * sub                                              # the sub below 45 Hz down by about 5 dB
    x = e.lowpass(x, 15500, order=4)                               # no air above 15 kHz
    x = e.highpass(x, 28)
    peak = np.abs(x).max() + 1e-9
    drive = 1.6
    return np.tanh(drive * x / peak) / np.tanh(drive) * peak       # tape: the peaks rounded off, a little warmth


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
    ap.add_argument("--era", choices=["90s"], help="90s: narrower, less sub, no air, tape (and -11 LUFS)")
    ap.add_argument("--dj-from", help="our own render of the song: its DJ intro and outro replace the take's")
    ap.add_argument("--bars", type=int, help="the song's length in bars (for --dj-from)")
    a = ap.parse_args()
    x, sr = read(a.src)
    ours = None
    if a.dj_from:
        ours, sr2 = read(a.dj_from)
        if sr2 != e.SR or not a.bars:
            raise ValueError(f"--dj-from needs a {e.SR} Hz render (this one: {sr2} Hz) and --bars")
        phase = lag_to(x, sr, ours, start=16 * 240 / a.bpm)   # line up with our render, from bar 16 on
    else:
        phase = beat_phase(x, sr, a.bpm)
    if phase >= 0:
        x = x[int(round(phase * sr)):]
    else:                                           # the take runs early: silence in front
        x = np.concatenate([np.zeros((int(round(-phase * sr)), 2)), x])
    if sr != e.SR:
        g = np.gcd(sr, e.SR)
        x = signal.resample_poly(x, e.SR // g, sr // g, axis=0)
    k = int(.004 * e.SR)
    x[:k] *= np.linspace(0, 1, k)[:, None]
    if ours is not None:
        x = splice_dj(x, ours, a.bpm, a.bars)
    if a.era == "90s":
        x = era_90s(x)
        if a.lufs == -10.0:
            a.lufs = -11.0
    x = master(x, a.lufs, a.ceiling)
    write(a.dst, x)
    tp = 20 * np.log10(e.true_peak(x).max())
    m, s = divmod(len(x) / e.SR, 60)
    print(f"wrote {a.dst}: {int(m)}:{s:04.1f}, grid moved {phase * 1000:.0f} ms, "
          f"{e.integrated_lufs(x):.1f} LUFS, {tp:+.1f} dBTP")
