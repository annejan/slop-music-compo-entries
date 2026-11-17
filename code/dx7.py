"""A DX7-style FM synthesizer in numpy: six sine operators, the DX7's 32 algorithms, one operator that feeds back
on itself, and a 4-rate / 4-level envelope per operator.

A float port of the numpy replica in ~/Projects/npu/iron/fun/dx7.py (the same synth runs as 512 voices on the
Ryzen AI NPU there). The algorithms follow the chart in the DX7 manual. The patches are made up, not Yamaha's.

    note("epiano", midi, seconds, velocity) -> mono float array at engine.SR, cached per note
"""
import functools
import math

import numpy as np

from engine import SR

OPS = 6
BLOCK = 256                 # the envelopes move per block of 256 samples, as on the DX7 port; linear in between

# algorithm: (modulators of each operator, carriers, the operator with feedback)
ALGOS = {
    1: ({1: [2], 3: [4], 4: [5], 5: [6]}, [1, 3], 6),
    2: ({1: [2], 3: [4], 4: [5], 5: [6]}, [1, 3], 2),
    3: ({1: [2], 2: [3], 4: [5], 5: [6]}, [1, 4], 6),
    4: ({1: [2], 2: [3], 4: [5], 5: [6]}, [1, 4], 4),
    5: ({1: [2], 3: [4], 5: [6]}, [1, 3, 5], 6),
    6: ({1: [2], 3: [4], 5: [6]}, [1, 3, 5], 5),
    7: ({1: [2], 3: [4, 5], 5: [6]}, [1, 3], 6),
    8: ({1: [2], 3: [4, 5], 5: [6]}, [1, 3], 4),
    9: ({1: [2], 3: [4, 5], 5: [6]}, [1, 3], 2),
    10: ({1: [2], 2: [3], 4: [5, 6]}, [1, 4], 3),
    11: ({1: [2], 2: [3], 4: [5, 6]}, [1, 4], 6),
    12: ({1: [2], 3: [4, 5, 6]}, [1, 3], 2),
    13: ({1: [2], 3: [4, 5, 6]}, [1, 3], 6),
    14: ({1: [2], 3: [4], 4: [5, 6]}, [1, 3], 6),
    15: ({1: [2], 3: [4], 4: [5, 6]}, [1, 3], 2),
    16: ({1: [2, 3, 5], 3: [4], 5: [6]}, [1], 6),
    17: ({1: [2, 3, 5], 3: [4], 5: [6]}, [1], 2),
    18: ({1: [2, 3, 4], 4: [5], 5: [6]}, [1], 3),
    19: ({1: [2], 2: [3], 4: [6], 5: [6]}, [1, 4, 5], 6),
    20: ({1: [3], 2: [3], 4: [5, 6]}, [1, 2, 4], 3),
    21: ({1: [3], 2: [3], 4: [6], 5: [6]}, [1, 2, 4, 5], 3),
    22: ({1: [2], 3: [6], 4: [6], 5: [6]}, [1, 3, 4, 5], 6),
    23: ({2: [3], 4: [6], 5: [6]}, [1, 2, 4, 5], 6),
    24: ({3: [6], 4: [6], 5: [6]}, [1, 2, 3, 4, 5], 6),
    25: ({4: [6], 5: [6]}, [1, 2, 3, 4, 5], 6),
    26: ({2: [3], 4: [5, 6]}, [1, 2, 4], 6),
    27: ({2: [3], 4: [5, 6]}, [1, 2, 4], 3),
    28: ({1: [2], 3: [4], 4: [5]}, [1, 3, 6], 5),
    29: ({3: [4], 5: [6]}, [1, 2, 3, 5], 6),
    30: ({3: [4], 4: [5]}, [1, 2, 3, 6], 5),
    31: ({5: [6]}, [1, 2, 3, 4, 5], 6),
    32: ({}, [1, 2, 3, 4, 5, 6], 6),
}
MOD_TURNS = 6.0             # phase deviation (in turns) of a modulator at output level 99 and full envelope
FB_TURNS = {k: 0.0 if k == 0 else 0.06 * 2 ** (k - 1) for k in range(8)}   # feedback 0..7 -> turns at full level


def op(coarse=1, fine=0, detune=0, level=99, rates=(99, 50, 30, 50), levels=(99, 80, 0, 0), fixed=False, vel=0.0):
    return dict(coarse=coarse, fine=fine, detune=detune, level=level, rates=rates, levels=levels, fixed=fixed, vel=vel)


PATCHES = {
    # operators 1..6
    "epiano": dict(algo=5, feedback=5, gain=2.2, ops=[
        op(1, 0, 0, 99, (95, 25, 20, 60), (99, 85, 0, 0), vel=0.4),      # 1 carrier: body
        op(1, 0, 0, 80, (95, 30, 20, 60), (99, 80, 0, 0), vel=0.9),      # 2 -> 1: tine edge, velocity
        op(1, 0, 3, 90, (90, 20, 20, 60), (99, 90, 0, 0), vel=0.3),      # 3 carrier
        op(14, 0, 0, 74, (99, 60, 60, 70), (99, 0, 0, 0), vel=1.0),      # 4 -> 3: the bell-like attack
        op(1, 0, -3, 80, (95, 22, 20, 60), (99, 80, 0, 0), vel=0.3),     # 5 carrier, detuned
        op(1, 0, 0, 76, (95, 22, 20, 60), (99, 85, 0, 0), vel=0.6),      # 6 -> 5
    ]),
    "bass": dict(algo=2, feedback=6, gain=.5, ops=[
        op(1, 0, 0, 99, (99, 40, 20, 60), (99, 90, 0, 0), vel=0.5),
        op(1, 0, 0, 90, (99, 45, 40, 70), (99, 85, 0, 0), vel=0.9),      # 2 -> 1 with feedback: growl
        op(1, 0, 0, 90, (99, 35, 20, 60), (99, 90, 0, 0), vel=0.5),
        op(2, 0, 0, 78, (99, 60, 40, 70), (99, 60, 0, 0), vel=0.8),
        op(1, 0, 0, 0, (99, 50, 20, 50), (99, 0, 0, 0)),
        op(1, 0, 0, 0, (99, 50, 20, 50), (99, 0, 0, 0)),
    ]),
    "bells": dict(algo=5, feedback=0, gain=.4, ops=[
        op(1, 0, 0, 99, (99, 20, 15, 40), (99, 90, 0, 0)),
        op(3, 50, 0, 80, (99, 25, 15, 40), (99, 85, 0, 0)),              # 2 -> 1: ratio 3.5, inharmonic
        op(2, 0, 4, 85, (99, 18, 15, 40), (99, 90, 0, 0)),
        op(7, 0, 0, 72, (99, 30, 15, 40), (99, 80, 0, 0)),
        op(5, 0, -4, 70, (99, 15, 15, 40), (99, 90, 0, 0)),
        op(11, 0, 0, 66, (99, 35, 20, 40), (99, 70, 0, 0)),
    ]),
    "brass": dict(algo=18, feedback=6, gain=.6, ops=[
        op(1, 0, 0, 99, (70, 50, 40, 55), (99, 85, 85, 0), vel=0.4),
        op(1, 0, 2, 86, (65, 50, 40, 55), (99, 88, 88, 0), vel=0.8),
        op(1, 0, -2, 84, (68, 50, 40, 55), (99, 88, 88, 0), vel=0.8),    # 3 -> 1, feedback: buzz
        op(1, 0, 0, 80, (72, 50, 40, 55), (99, 85, 85, 0), vel=0.6),
        op(2, 0, 0, 72, (72, 50, 40, 55), (99, 80, 80, 0), vel=0.6),
        op(1, 0, 0, 0, (99, 50, 40, 50), (99, 0, 0, 0)),
    ]),
    "pad": dict(algo=32, feedback=6, gain=.2, ops=[
        op(1, 0, 0, 90, (40, 30, 30, 35), (99, 99, 99, 0)),
        op(2, 0, 3, 80, (38, 30, 30, 35), (99, 99, 99, 0)),
        op(3, 0, -3, 70, (36, 30, 30, 35), (99, 99, 99, 0)),
        op(1, 0, 5, 85, (42, 30, 30, 35), (99, 99, 99, 0)),
        op(2, 0, -5, 75, (40, 30, 30, 35), (99, 99, 99, 0)),
        op(4, 0, 0, 55, (34, 30, 30, 35), (99, 99, 99, 0)),
    ]),
}


def level_amp(level):
    """DX7 output level 0..99 -> linear amplitude (0.75 dB per step, 99 = 1.0, 0 = silence)."""
    return 0.0 if level <= 0 else 10 ** (-0.75 * (99 - level) / 20)


def rate_seconds(rate):
    """Seconds for a full 0..99 swing at DX7 rate 0..99 (99: ~2 ms, 50: ~0.2 s, 0: ~30 s). Approximate."""
    return 30.0 * 2 ** (-rate / 7.0)


def op_freq(o, note_hz):
    if o["fixed"]:
        return 10.0 ** (o["coarse"] % 4) * (1 + o["fine"] / 100.0)
    ratio = (0.5 if o["coarse"] == 0 else float(o["coarse"])) * (1 + o["fine"] / 100.0)
    return note_hz * ratio + o["detune"] * 0.3


def envelope(o, n_on, n_total):
    """One operator's envelope per sample: segments 1-3 while the key is down (holding at level 3), then the
    release (rate 4 to level 4). Moves in dB, attacks three times as fast; per block, linear in between."""
    def target(s):
        lv = o["levels"][s]
        return -120.0 if lv <= 0 else -0.75 * (99 - lv)

    def step(s, db):
        per = 74.25 / rate_seconds(o["rates"][s]) * (BLOCK / SR)
        return per * (3.0 if target(s) > db else 1.0)

    blocks = n_total // BLOCK + 2
    amp = np.zeros(blocks)
    db, seg = -120.0, 0
    for b in range(blocks):
        if b * BLOCK >= n_on and seg < 3:
            seg = 3
        if seg < 4:
            t = target(seg)
            db += float(np.clip(t - db, -step(seg, db), step(seg, db)))
            if abs(t - db) < 1e-9:
                seg = seg + 1 if seg < 2 else (4 if seg == 3 else seg)
        amp[b] = 0.0 if db <= -119.0 else 10 ** (db / 20)
    curve = np.interp(np.arange(n_total), np.arange(blocks) * BLOCK + BLOCK, amp, left=0.0)
    return curve


@functools.lru_cache(maxsize=4096)
def _note(patch, midi, n_on, velocity, tail):
    p = PATCHES[patch]
    mods, carriers, fbop = ALGOS[p["algo"]]
    n = n_on + tail
    hz = 440.0 * 2 ** ((midi - 69) / 12)
    t = np.arange(n) / SR
    out = {}
    for k in range(OPS, 0, -1):     # operator 6 first: the modulators before the carriers
        o = p["ops"][k - 1]
        scale = level_amp(o["level"]) * (1 - o["vel"] * (1 - velocity))
        if scale == 0.0:
            out[k] = np.zeros(n)
            continue
        env = envelope(o, n_on, n) * scale
        phase = op_freq(o, hz) * t + sum(out[s] for s in mods.get(k, [])) * MOD_TURNS
        fb = FB_TURNS[p.get("feedback", 0)] if k == fbop else 0.0
        if fb:                       # the feedback operator: its own last two outputs move its phase, per sample
            y = np.empty(n)
            y1 = y2 = 0.0
            tau = 2 * math.pi
            ph, ev = phase.tolist(), env.tolist()
            for i in range(n):
                v = math.sin(tau * (ph[i] + fb * (y1 + y2) * .5)) * ev[i]
                y[i] = v
                y2, y1 = y1, v
            out[k] = y
        else:
            out[k] = np.sin(2 * np.pi * phase) * env
    y = sum(out[c] for c in carriers) * p.get("gain", .5) / len(carriers)
    y.flags.writeable = False
    return y


def note(patch, midi, seconds, velocity=1.0, tail=.5):
    """One note: the key held for `seconds`, then `tail` seconds of release. Velocity 0..1."""
    return _note(patch, int(midi), max(int(seconds * SR), 1), round(float(velocity), 2), int(tail * SR)).copy()
