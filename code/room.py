"""A simulated room for the reverb: a 3-D finite-difference (FDTD) wave simulation of the air in a box, with a
pulse at a source and two "ears" that record the pressure. What they record is the room's stereo impulse
response, and the mixdown convolves the reverb send with it.

A numpy port of ~/Projects/npu/iron/fun/room.py (the same simulation runs on the 32 cores of the Ryzen AI NPU
there). Per step, for every cell:

    p_next = g * (2 p - p_prev + lambda^2 * (sum of the 6 neighbours - 6 p)),   lambda = c dt / dx = 0.5

The walls are pressure-release (p = 0 just outside the box). The damping g sets the reverb time. The grid runs
at 8 kHz (a cell is 8.6 cm), so the reverb has nothing above 4 kHz: a dark, warm room. The result is cached.

    impulse_response(size=(7, 5, 3), rt60=1.8) -> (samples, 2) float array at engine.SR
"""
import hashlib
import os

import numpy as np
from scipy import signal

from engine import SR

FS = 8000
LAMBDA = 0.5
C = 343.0
DX = C / FS / LAMBDA        # 8.6 cm
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")


def simulate(size, rt60, src=(.35, .45, .4), ears=(.6, .55, .45), seconds=None):
    """The raw simulation at FS: size in metres (x, y, z); src and ears as fractions of the size. Returns (steps, 2)."""
    nx, ny, nz = (max(int(round(s / DX)), 4) for s in size)
    g = np.float32(10 ** (-6 / (rt60 * FS)))      # a mode's amplitude falls by sqrt(g) per step: -60 dB after rt60
    l2 = np.float32(LAMBDA ** 2)
    c0 = np.float32(2 - 6 * LAMBDA ** 2)
    p = np.zeros((nx + 2, ny + 2, nz + 2), np.float32)      # a ring of zero cells: the walls
    pp = np.zeros_like(p)
    sx, sy, sz = (int(f * n) + 1 for f, n in zip(src, (nx, ny, nz)))
    ex, ey, ez = (int(f * n) + 1 for f, n in zip(ears, (nx, ny, nz)))
    half = max(int(round(.1 / DX)), 1)              # ears about 17 cm apart, along x
    rx = [(ex - half, ey, ez), (ex + half, ey, ez)]
    steps = int((seconds or rt60 * 1.1) * FS)
    ir = np.zeros((steps, 2), np.float32)
    inner = (slice(1, -1),) * 3
    for i in range(steps):
        if i < 14:
            p[sx, sy, sz] += np.exp(-((i - 6) / 2.5) ** 2) * .5
        s = (p[:-2, 1:-1, 1:-1] + p[2:, 1:-1, 1:-1] + p[1:-1, :-2, 1:-1] + p[1:-1, 2:, 1:-1]
             + p[1:-1, 1:-1, :-2] + p[1:-1, 1:-1, 2:])
        nxt = np.zeros_like(p)
        nxt[inner] = g * (c0 * p[inner] - pp[inner] + l2 * s)
        pp, p = p, nxt
        ir[i] = p[rx[0]], p[rx[1]]
    return ir


def impulse_response(size=(7.0, 5.0, 3.0), rt60=1.8, **kw):
    """The room's stereo impulse response at SR, without the direct sound (the dry signal is already in the mix),
    each channel at unit energy."""
    key = hashlib.sha1(repr((size, rt60, sorted(kw.items()), FS, 2)).encode()).hexdigest()[:16]
    path = os.path.join(CACHE, f"room{key}.npy")
    if os.path.exists(path):
        return np.load(path)
    ir = simulate(size, rt60, **kw).astype(np.float64)
    # the direct sound is the first strong peak: start just after it, with a short fade in
    first = int(np.argmax(np.abs(ir).max(1) > .3 * np.abs(ir).max()))
    ir = ir[first + int(.004 * FS):]
    ir[:16] *= np.linspace(0, 1, 16)[:, None]
    ir = signal.resample_poly(ir, SR // 100, FS // 100, axis=0)
    ir -= ir.mean(0)
    ir /= np.sqrt(np.sum(ir ** 2, axis=0))
    os.makedirs(CACHE, exist_ok=True)
    np.save(path, ir)
    return ir


if __name__ == "__main__":
    import time
    t0 = time.perf_counter()
    h = impulse_response()
    e = np.cumsum(h[::-1, 0] ** 2)[::-1]
    db = 10 * np.log10(e / e[0] + 1e-12)
    i5, i25 = np.argmax(db < -5), np.argmax(db < -25)
    print(f"{len(h) / SR:.2f} s, {time.perf_counter() - t0:.1f} s to make; RT60 (Schroeder) ~ {(i25 - i5) / SR * 3:.2f} s")
