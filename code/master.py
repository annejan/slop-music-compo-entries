#!/usr/bin/env python3
"""Master a finished song from another generator (ACE-Step) for the DJ, the same way engine.py masters ours:
the beat grid moved to sample 0, 44.1 kHz, the loudness target under a true-peak ceiling, 16-bit with dither.

master.py IN.wav OUT.wav --bpm 120 [--lufs -10] [--ceiling -1.2] [--era 90s] [--dj-from OURS.wav --bars 120]
          [--match 0.7]

The beat is found from the onsets (40-8000 Hz), folded onto one beat (see beat_phase). The start is cut to the
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
    """Seconds from the start to the first beat of the grid: the onset strength (the rise of the log envelope,
    40-8000 Hz, 1 ms frames) folded onto one beat. Calibrated on our own renders (on the grid by construction):
    within 1.3 ms. The kick band alone reads 10-40 ms late (our kicks sweep down into it)."""
    hop = sr // 1000
    band = signal.sosfilt(signal.butter(4, [40, 8000], btype="band", fs=sr, output="sos"), x.mean(1))
    v = np.log(np.sqrt(np.add.reduceat(band ** 2, np.arange(0, len(band) - hop, hop)) / hop) + 1e-6)
    onset = np.maximum(np.diff(v), 0)
    beat = 60 / bpm
    t = (np.arange(len(onset)) + 1) * hop / sr
    hist, edges = np.histogram(t % beat, bins=400, range=(0, beat), weights=onset)
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


THIRDS = 1000 * 2 ** (np.arange(-16, 13) / 3)                    # third-octave centres, 25 Hz to 16 kHz


def _thirds_db(m):
    """The level of a mono signal per third-octave band (dB, long-term average)."""
    f, p = signal.welch(m.astype(np.float32), e.SR, nperseg=16384)
    return np.array([10 * np.log10(p[(f >= c * 2 ** (-1 / 6)) & (f < c * 2 ** (1 / 6))].sum() + 1e-20)
                     for c in THIRDS])


def _side_db(x):
    """How loud the sides are against the middle above 150 Hz (dB): the width of the stereo image."""
    hp = e.highpass(x, 150)
    return 10 * np.log10(np.mean((hp[:, 0] - hp[:, 1]) ** 2) / (np.mean((hp[:, 0] + hp[:, 1]) ** 2) + 1e-20) + 1e-20)


def match_tone(x, ref, strength=.7, max_db=8.0, body=None):
    """Give x the tonal balance and stereo width of ref: the difference of their long-term spectra per third octave
    (smoothed, at most max_db either way, times strength) as one static zero-phase EQ, and the sides scaled to the
    reference width. For a take of ACE-Step against our own render of the song: the arrangement and the voices from
    the take, the colour of the code (ACE-Step adds deep sub, a dark top and a wide image: the "too modern" sound).
    body: (i0, i1) samples to measure in (not the DJ intro and outro). Returns (y, report)."""
    i0, i1 = body or (0, min(len(x), len(ref)))
    a, b = x[i0:i1], ref[i0:i1]
    d = _thirds_db(b.mean(1)) - _thirds_db(a.mean(1))
    d = np.convolve(np.r_[d[0], d, d[-1]], np.ones(3) / 3, "valid")    # smooth over three bands
    d = np.clip(d - np.median(d), -max_db, max_db) * strength          # the shape only: the loudness comes later
    f = np.fft.rfftfreq(len(x), 1 / e.SR)
    g = 10 ** (np.interp(np.log(np.maximum(f, 1)), np.log(THIRDS), d) / 20)
    y = np.stack([np.fft.irfft(np.fft.rfft(x[:, c]) * g, len(x)) for c in range(2)], 1)
    w = np.clip(_side_db(b) - _side_db(a), -9, 3) * strength
    mid, side = (y[:, 0] + y[:, 1]) / 2, (y[:, 0] - y[:, 1]) / 2 * 10 ** (w / 20)
    y = np.stack([mid + side, mid - side], 1)
    at = lambda hz: d[np.argmin(np.abs(THIRDS - hz))]
    report = (f"tone matched: 31 Hz {at(31):+.1f} dB, 62 Hz {at(62):+.1f}, 250 Hz {at(250):+.1f}, "
              f"1 kHz {at(1000):+.1f}, 4 kHz {at(4000):+.1f}, 10 kHz {at(10000):+.1f}; sides {w:+.1f} dB")
    return y, report


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


def process(src, dst, bpm, lufs=None, ceiling=-1.2, era=None, dj_from=None, bars=None, match=0.0):
    """The whole job: read, line up (with our render, else by the kick), 44.1 kHz, the tone of our render (match,
    0-1), the DJ intro and outro from our render, the era, the loudness, write. lufs None: -10, or -11 with era 90s.
    Returns a one-line report."""
    x, sr = read(src)
    ours = None
    if dj_from:
        ours, sr2 = read(dj_from)
        if sr2 != e.SR or not bars:
            raise ValueError(f"dj_from needs a {e.SR} Hz render (this one: {sr2} Hz) and bars")
        phase = lag_to(x, sr, ours, start=16 * 240 / bpm)   # line up with our render, from bar 16 on
    else:
        phase = beat_phase(x, sr, bpm)
    if phase >= 0:
        x = x[int(round(phase * sr)):]
    else:                                           # the take runs early: silence in front
        x = np.concatenate([np.zeros((int(round(-phase * sr)), 2)), x])
    if sr != e.SR:
        g = np.gcd(sr, e.SR)
        x = signal.resample_poly(x, e.SR // g, sr // g, axis=0)
    k = int(.004 * e.SR)
    x[:k] *= np.linspace(0, 1, k)[:, None]
    tone = ""
    if match and ours is not None:
        body = (int(16 * 240 / bpm * e.SR), int((bars - 16) * 240 / bpm * e.SR))
        x, tone = match_tone(x, ours, match, body=body)
        tone = "; " + tone
    if ours is not None:
        x = splice_dj(x, ours, bpm, bars)
    if era == "90s":
        x = era_90s(x)
    if lufs is None:
        lufs = -11.0 if era == "90s" else -10.0
    x = master(x, lufs, ceiling)
    write(dst, x)
    tp = 20 * np.log10(e.true_peak(x).max())
    m, s = divmod(len(x) / e.SR, 60)
    return (f"wrote {dst}: {int(m)}:{s:04.1f}, grid moved {phase * 1000:.0f} ms, "
            f"{e.integrated_lufs(x):.1f} LUFS, {tp:+.1f} dBTP{tone}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--bpm", type=float, required=True)
    ap.add_argument("--lufs", type=float, help="default -10, or -11 with --era 90s")
    ap.add_argument("--ceiling", type=float, default=-1.2)
    ap.add_argument("--era", choices=["90s"], help="90s: narrower, less sub, no air, tape (and -11 LUFS)")
    ap.add_argument("--dj-from", help="our own render of the song: its DJ intro and outro replace the take's")
    ap.add_argument("--bars", type=int, help="the song's length in bars (for --dj-from)")
    ap.add_argument("--match", type=float, default=0.0,
                    help="0-1: give the take the tonal balance and width of our render (needs --dj-from)")
    a = ap.parse_args()
    print(process(a.src, a.dst, a.bpm, a.lufs, a.ceiling, a.era, a.dj_from, a.bars, a.match))
