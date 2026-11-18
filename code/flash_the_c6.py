#!/usr/bin/env python3
"""Flash The C Six: digital hardcore, 174 BPM, F minor. A bonus for the surprise themes, made from template.py.

flash_the_c6.py [OUT.wav]          PREVIEW=48-64 flash_the_c6.py: only bars 48 to 63, for a quick listen
                                   GLITCH=0: no glitch pass (to hear what the glitches edit)

The whole song is one shout, "Flash the C six!", hammered over a distorted breakbeat and a gabber kick, noise
guitars from distorted saws, sirens and chip bleeps. The polite MC of the Rhythm of the Badge says "Do not flash the
C six"; the room shouts him down, he caves, and the glitches play what then happens to a Tanmatsu. Every glitch
(loops, stutters, crushes, tape stops, cuts) is an edit of what is already rendered, made on the buses (and on the
reverb and delay sends) after every put and before the mixdown. The beat grid never moves: a glitch happens inside
its bars and the next bar starts on time. The first and last 16 bars (drums only, for the DJ) are never touched.

  bars   0-15  intro: the break, the gabber from bar 8 (drums only)
        16-31  the band arrives behind the filter: feedback, the siren, chip arps, the chop teaser; the count-in
        32-47  riot A: the shout, called and answered, then everyone; a tape stop
        48-55  the authority: half time, the siren, the terrace chant; a cut
        56-63  the flash: the plug, esptool's dots, a flaky cable, the accelerando, the reset
        64-71  the crash: the boot ROM at the wrong baud rate, Guru Meditation, panic, the boot loop
        72-79  riot B: the grievances, the name call
        80-87  terrace
        88-95  the authority caves; the count-in
        96-111 riot C, the biggest
       112-119 terrace final, the room alone
       120-127 the boot loop, a cut, "Told you."
       128-143 outro: drums only (for the DJ)
"""
import math
import os
import re
import wave

import numpy as np

import engine as e
import parts
import room
import voice as V

# ---------------------------------------------------------------- the knobs
TITLE = "Flash The C Six"
DAY = "Bonus: digital hardcore"
BPM, BARS = 174, 144
KEY = "Fm"
KEY_CHANGE = 0
PROG = ["Fm", "Fm", "Db", "Eb"]        # one chord a bar, repeating
LUFS = -9.0

e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)
P = parts.Band(S, PROG, scale="minor", tonic="F")
SR, ST, BT = e.SR, S.step, S.beat
EARLY = .025                            # every shout 25 ms early: the consonant lands on the step
LO, HI = S.at(16), S.at(128)            # the glitches stay between the DJ's drums-only ends

# ---------------------------------------------------------------- small tools
def fade(x, ms=2.0):
    x = np.array(x, dtype=np.float64)
    r = min(int(ms / 1000 * SR), len(x) // 2)
    if r:
        ramp = np.linspace(0, 1, r)
        if x.ndim == 2:
            ramp = ramp[:, None]
        x[:r] *= ramp
        x[len(x) - r:] *= ramp[::-1]
    return x


def bitcrush(x, bits, hold=1):
    """Sample-and-hold every `hold` samples, then quantise to `bits` (relative to the piece's own peak, so the
    crunch does not depend on the level). 1 bit: the sign only, a square buzz."""
    x = np.asarray(x, dtype=np.float64)
    if len(x) == 0:
        return x
    y = x[(np.arange(len(x)) // hold) * hold]
    pk = np.abs(y).max()
    if pk == 0:
        return y
    if bits <= 1:
        return np.sign(y) * pk * .35
    q = 2 ** (bits - 1)
    return np.round(y / pk * q) / q * pk


def octave_up(x):
    return np.asarray(x)[::2]


def repitch(x, semis):
    """Read x faster (a sampler: shorter and higher)."""
    r = 2 ** (semis / 12)
    pos = np.arange(int(len(x) / r)) * r
    idx = np.arange(len(x))
    if x.ndim == 1:
        return np.interp(pos, idx, x)
    return np.stack([np.interp(pos, idx, x[:, c]) for c in range(x.shape[1])], 1)


def pad_sum(*xs):
    n = max(len(x) for x in xs)
    out = np.zeros(n)
    for x in xs:
        out[:len(x)] += x
    return out


DRY = [(S.at(55), S.at(56)), (S.at(62, 2), S.at(64)), (S.at(126), S.at(128))]   # the bars before the cuts


def put(bus, t, g, pan=.5, amp=1.0, wet=.15, echo=0.0):
    """S.put, dry in the bars before the cuts: no reverb or delay tail rings over a hole."""
    if any(a - .05 <= t < b for a, b in DRY):
        wet = echo = 0.0
    S.put(bus, t, g, pan, amp, wet=wet, echo=echo)


# ---------------------------------------------------------------- voices
# every distinct (text, voice, seconds, pitch) once: V.rap re-runs WORLD on every call
_takes, _dirty = {}, {}


def take(text, secs, voice, pitch):
    k = (text, voice, round(secs, 4), round(pitch, 4))
    if k not in _takes:
        _takes[k] = V.rap(text, secs, voice=voice, pitch=pitch)
    return _takes[k]


def dirty(text, secs, voice, pitch):
    """The distorted copy: band-passed 250-4500 Hz, then tanh(4x), at the clean take's RMS."""
    k = (text, voice, round(secs, 4), round(pitch, 4))
    if k not in _dirty:
        y = take(text, secs, voice, pitch)
        d = np.tanh(4 * e.bandpass(y, 250, 4500))
        _dirty[k] = d * (np.sqrt(np.mean(y ** 2)) / (np.sqrt(np.mean(d ** 2)) + 1e-9))
    return _dirty[k]


# SHOUT M was Ryan: the ear heard none of his one-word shouts, alone or in the mix, at any pitch ("Six!": "hit us",
# "let us", "take us"; "One!": "what?"). HFC male at the same strained pitch: "six six six", "1 1 1", "Flash, Flash".
# Ryan takes his place in the gang.
SHOUTERS = {"M": dict(voice="en_US-hfc_male-medium", pitch=1.12, pan=.42, dpan=.3),
            "F": dict(voice="en_GB-cori-high", pitch=1.2, pan=.58, dpan=.7)}
GANG = [("en_US-joe-medium", .15), ("en_US-john-medium", .85), ("en_US-bryce-medium", .3),
        ("en_US-norman-medium", .7), ("en_US-ryan-high", .5),
        ("en_US-amy-medium", .2), ("en_US-kristin-medium", .8), ("en_GB-jenny_dioco-medium", .4),
        ("en_US-hfc_female-medium", .6)]
AUTHORITY = "en_GB-alan-medium"         # the MC of the Rhythm of the Badge: V.rap(text, 1.68 s, pitch=.84)
READOUT = "en_US-lessac-high"


DIRT = .45         # the shouters' dirty copies (at .3 the ear heard no more words: 68 % against 75 %)
ALL_DIRT = .25     # the shouters' dirty copies in ALL (.35 in the brief): the words drop, so the dirty copy goes down
SPREAD = .5        # the gang's offsets (.007 i - .03 s) halved: at the full spread the ear heard "the sea, next"


def gang_pitch(i):
    return .88 + .03 * i if i < 5 else 1.0 + .04 * (i - 5)


def voices(who, text, secs, pm=1.0, clean=1.0, dirt=DIRT, spread=None):
    """The takes of one call: [(seconds from the call, mono, pan, amp, wet)]. who: M, F, MF (both, M 10 ms early),
    GANG (nine voices of the room), ALL (the gang and both shouters), ROOM (ALL twice: the second pass at a pitch
    3 % lower, 12 ms later, mirrored)."""
    out = []
    if who in ("M", "F", "MF"):
        for w in who:
            s = SHOUTERS[w]
            dt = -.01 if (w == "M" and len(who) > 1) else 0.0
            p = s["pitch"] * pm
            out.append((dt, take(text, secs, s["voice"], p), s["pan"], clean, .08))
            out.append((dt + .012, dirty(text, secs, s["voice"], p), s["dpan"], dirt, .08))
    elif who in ("GANG", "ALL"):
        sp = SPREAD if spread is None else spread
        out += [(sp * (.007 * i - .03), take(text, secs, v, gang_pitch(i) * pm), pan, .3, .25)
                for i, (v, pan) in enumerate(GANG)]
        if who == "ALL":
            out += voices("MF", text, secs, pm, .8, ALL_DIRT)
    elif who == "ROOM":
        out += [(dt, y, pan, a, .35) for dt, y, pan, a, _ in voices("ALL", text, secs)]
        out += [(dt + .012, y, 1 - pan, a, .35) for dt, y, pan, a, _ in voices("ALL", text, secs, pm=.97)]
    return out


def place(t, items, amp=1.0, wet=None, fx=None):
    """Put the takes of a call at t (25 ms early: the consonant on the step)."""
    for dt, y, pan, a, w in items:
        put("vox", t - EARLY + dt, fx(y) if fx else y, pan, a * amp, wet=w if wet is None else wet, echo=0)


def stack(items):
    """The takes of a call mixed to one stereo take: (seconds from the call, stereo)."""
    d0 = min(it[0] for it in items)
    n = max(int(round((dt - d0) * SR)) + len(y) for dt, y, *_ in items)
    out = np.zeros((n, 2))
    for dt, y, pan, a, _ in items:
        i = int(round((dt - d0) * SR))
        out[i:i + len(y), 0] += y * a * math.cos(pan * math.pi / 2)
        out[i:i + len(y), 1] += y * a * math.sin(pan * math.pi / 2)
    return d0, out


def call(who, t, text, secs, amp=1.0, wet=None, dirt=DIRT, spread=None):
    place(t, voices(who, text, secs, dirt=dirt, spread=spread), amp, wet)


# the chant, four forms
# "the C!" and "Six!" as two takes: the ear heard "the sea" and "next" / "text" / "thanks", even with no music.
# "the C six!" as one take: "the C6", every time. The take runs from step 6 to the end of the bar (or into bar b
# of the terrace form), so "six" still lands near step 12 (or bar b's downbeat).
def riot(bar, who):
    """One bar: Flash! (1.25 beats) the C six! (from step 6, six about on step 12)."""
    t = S.at(bar)
    call(who, t, "Flash!", .43)
    call(who, t + 6 * ST, "the C six!", .83)


def terrace(bar, who):
    """Two bars in half time: Flash! (2 beats) the C / six! (about on bar b's downbeat), then the room claps on 8,
    10 and 12."""
    t = S.at(bar)
    call(who, t, "Flash!", .69)
    call(who, t + 11 * ST, "the C six!", .83)      # at 1.0 s the room smeared "six": "sea secrets", "sea singers"
    for k in (8, 10, 12):
        put("drums", S.at(bar + 1) + k * ST, ROOMCLAP, amp=.8, wet=.25)


def name(bar):
    """SHOUT F calls the letter, the GANG the number."""
    call("F", S.at(bar), "C!", .345, 1.3)
    call("GANG", S.at(bar) + 8 * ST, "Six!", .345, 1.8, spread=.2)   # one short word: the gang tight
                                                                        # (at .5 the ear heard only her "C")


def chop_c():
    """SHOUT F's clean "C!", an octave up, its first 86 ms: the chopped c-c-c-c."""
    s = SHOUTERS["F"]
    return fade(octave_up(take("C!", .345, s["voice"], s["pitch"]))[:int(ST * SR)], 1.5)


def chop_six():
    s = SHOUTERS["F"]
    return fade(octave_up(take("Six!", .31, s["voice"], s["pitch"])), 2)


def chop(t, n=4, six=False, amp=1.0):
    """The chop on the LEAD bus (texture, not words): n c's in sixteenths, then (six) her Six! an octave up."""
    c = chop_c()
    for k in range(n):
        put("lead", t + k * ST, c, .3 if k % 2 == 0 else .7, amp, wet=.1)
    if six:
        put("lead", t + n * ST - EARLY, chop_six(), .3 if n % 2 == 0 else .7, amp, wet=.15, echo=.1)


def hook(bar):
    """The 666: one ALL take of Six!, put on beats 1-3, crushed to 16, 8 and 5 bits."""
    d0, st = stack(voices("ALL", "Six!", .31))
    for k, bits in enumerate((16, 8, 5)):
        put("vox", S.at(bar, k) - EARLY + d0, bitcrush(st, bits), amp=1.0, wet=.15)


def count_in(bar, beat0=0.0, every=1.0, secs=.26, snare=True):
    """SHOUT M: One! One! Five! Two! (115200 baud), dry, a dry crushed snare under each word."""
    for k, w in enumerate(("One!", "One!", "Five!", "Two!")):
        t = S.at(bar, beat0 + k * every)
        place(t, voices("M", w, secs), wet=0)
        if snare:
            put("drums", t, SNARE_X, amp=.8, wet=0)


def authority(t, text, secs=1.68, wet=.25, echo=.25, amp=1.1):
    """Alan, exactly the MC of the Rhythm of the Badge: never shouted, never distorted."""
    put("vox", t, take(text, secs, AUTHORITY, .84), .5, amp, wet=wet, echo=echo)


def readout(text):
    """The computer through a small speaker, at its own pace (P.say's sound)."""
    y = V._finish(V.tts(text, READOUT))
    y = y * (.14 / (np.sqrt(np.mean(y ** 2)) + 1e-9))
    return np.tanh(2 * e.bandpass(y, 300, 3400)) * .6


# ---------------------------------------------------------------- drums
def crunch(x):
    """The Atari Teenage Riot crunch: tanh(3x), then 12 bits."""
    return np.round(np.tanh(3 * x) * 2047) / 2047


SNARE_X = crunch(pad_sum(e.clap(.6), e.snare(.45)))
GHOST = crunch(e.snare(.3))
HAT_X = crunch(e.hat(.3))
BKICK = e.kick(1.0, punch=150, base=50, length=.3, click=.5)
_g = e.kick(1.0, punch=230, base=44, length=.45, click=.8)
GABBER = e.lowpass(np.tanh(7 * _g) / np.tanh(7), 8000)
CRASH = e.crash(1.0)
ROOMCLAP = np.zeros((int(.35 * SR), 2))
for _i in range(6):                     # six people clapping, 0-25 ms apart, across the room
    _c, _o, _p = e.clap(.5), int(_i * .005 * SR), .1 + .16 * _i
    ROOMCLAP[_o:_o + len(_c), 0] += _c * math.cos(_p * math.pi / 2)
    ROOMCLAP[_o:_o + len(_c), 1] += _c * math.sin(_p * math.pi / 2)

BREAK_A = dict(kick="x.x.......xx....", clap="....x..o.o..x..o", hat="x.x.x.x.x.x.x.x.")
BREAK_B = dict(kick="x.x.......x.....", clap="....x..o.o..x.o.", hat="x.x.x.x.x.x.xox.", extra="..............oo")
HALF = dict(kick="x.........x.....", clap="........x.......", hat="x.x.x.x.x.x.x.x.")


def hits(s):
    return [(k, 1.0 if c == "x" else .55) for k, c in enumerate(s) if c in "xo"]


def bkick(t, v=1.0):
    put("drums", t, BKICK, .5, v, wet=0)
    S.kicks.append(t)


def gabber(t, amp=1.0):
    put("drums", t, GABBER, .5, .8 * amp, wet=0)
    S.kicks.append(t)


def brk(bar, amp=1.0, kick=True, steps=16, pat=None, until=None):
    """The break (A A A B); kick=False: its kick off (the gabber has the low end)."""
    pat = pat or (BREAK_B if bar % 4 == 3 else BREAK_A)
    t0 = S.at(bar)
    ok = (lambda k: k < steps and (until is None or t0 + k * ST < until))
    if kick:
        for k, v in hits(pat["kick"]):
            if ok(k):
                bkick(t0 + k * ST, v * amp)
    for k, v in hits(pat["clap"]):
        if ok(k):
            put("drums", t0 + k * ST, SNARE_X, .5, v * amp, wet=.18)
    for k, v in hits(pat["hat"]):
        if ok(k):
            put("perc", t0 + k * ST, HAT_X, .62, .6 * v * amp, wet=.04)
    for k, v in hits(pat.get("extra", "")):
        if ok(k):
            put("drums", t0 + k * ST, GHOST, .45, v * amp, wet=.15)


def four(bar, amp=1.0, steps=16):
    for k in range(0, steps, 4):
        gabber(S.at(bar) + k * ST, amp)


TERRACE_A = (50, 54, 80, 82, 84, 86, 90, 112, 114)     # the first bar of each terrace call


def half(bar, amp=1.0, gab=True, kick=True):
    """Half time, the gabber on the kick's steps; not on step 10 of a terrace call's first bar, where "the C six!"
    starts (the ear heard "Flash, let's eat sex" under it)."""
    brk(bar, amp, kick=kick, pat=HALF)
    if gab:
        for k, _ in hits(HALF["kick"]):
            if not (k == 10 and bar in TERRACE_A):
                gabber(S.at(bar) + k * ST, amp)


def crash(bar, amp=1.0):
    put("perc", S.at(bar), CRASH, .5, .7 * amp, wet=.3)


def roll(bar0, bars, until=None, amp=1.0):
    """P.roll's snare roll (climbing, thirty-seconds in the last bar), stopped at `until`."""
    total = bars * 16
    for k in range(total):
        u = k / total
        t = S.at(bar0) + k * ST
        for dt, a in ((0, 1.0), (ST / 2, .8)) if k >= total - 16 else ((0, 1.0),):
            if until is None or t + dt < until:
                put("drums", t + dt, e.snare((.15 + .6 * u ** 1.5) * amp * a), .5, wet=.25)


# ---------------------------------------------------------------- bass: the sine sub
_subs = {}


def sub_note(m, d):
    k = (m, round(d, 4))
    if k not in _subs:
        t = e.tt(d + .03)
        g = np.tanh(3 * np.sin(2 * np.pi * e.hz(m) * t))
        _subs[k] = e.lowpass(g, 250) * e.gate(t, d, .02) * e.rise(t, .004)
    return _subs[k]


def root_of(bar):
    return e.root_note(P.chord(bar), lo=29)       # F1, Db2, Eb2


def bass(bar, style="eighths", amp=1.0, steps=16, root=None):
    m = root or root_of(bar)
    if style == "eighths":
        for k in range(0, steps, 2):
            put("bass", S.at(bar) + k * ST, sub_note(m, 1.8 * ST), .5, .5 * amp, wet=0)
    elif style == "sixteenths":
        for k in range(steps):
            put("bass", S.at(bar) + k * ST, sub_note(m, .9 * ST), .5, .45 * amp, wet=0)
    else:   # whole
        put("bass", S.at(bar), sub_note(m, S.bar * .97), .5, .5 * amp, wet=0)


# ---------------------------------------------------------------- noise guitars (keys bus)
POWER = {"F": (41, 48, 53), "Db": (37, 44, 49), "Eb": (39, 46, 51)}
ARTIC = {"palm": .07, "stab": 2 * ST * .9, "beat": BT * .9, "ring": S.bar * 1.75}
_gtrs = {}


def _gtr_take(chord, art, seed):
    d = ARTIC[art]
    rel = .012 if art != "palm" else .015
    t = e.tt(d + rel + .01)
    det = np.random.default_rng(seed).uniform(-10, 10, (3, 6)) / 100      # 6 saws a note, +-10 cents
    x = sum(e.saw(e.hz(m + c), t) for j, m in enumerate(POWER[chord]) for c in det[j]) / 18
    x = e.highpass(x, 90)
    x = e.peaking(x, 1000, 4.0)
    if art == "palm":
        x = e.lowpass(x, 1200) * np.exp(-t * 18)
    else:
        x = x * np.exp(-t * (1.2 if art == "ring" else 3))
    x = np.tanh(12 * x)
    x = e.lowpass(x, 4500)
    return x * e.gate(t, d, rel / 3) * e.rise(t, .002)


def gtr(chord, art):
    """Two takes (detune seeds), 20 ms apart, hard left and right; rendered once per (chord, articulation)."""
    k = (chord, art)
    if k not in _gtrs:
        a, b = _gtr_take(chord, art, 1), _gtr_take(chord, art, 2)
        o = int(.02 * SR)
        out = np.zeros((len(a) + o, 2))
        for y, off, pan in ((a, 0, .1), (b, o, .9)):
            out[off:off + len(y), 0] += y * math.cos(pan * math.pi / 2)
            out[off:off + len(y), 1] += y * math.sin(pan * math.pi / 2)
        _gtrs[k] = out
    return _gtrs[k]


def chord_of(bar):
    c = P.chord(bar)
    return c[:-1] if c.endswith("m") else c


def guitar(t, chord, art, amp=1.0):
    put("keys", t, gtr(chord, art), amp=.4 * amp, wet=.06)   # .2 in the first renders: 15 dB under the drums (STEMS)


def gtr_riot(bar, push=True, steps=16, amp=1.0):
    """Palm-muted eighths on the root under the words; an open push on step 14, choked at the next downbeat."""
    c = chord_of(bar)
    for k in range(0, min(steps, 14 if push else 16), 2):
        guitar(S.at(bar) + k * ST, c, "palm", .9 * amp)
    if push and steps > 14:
        guitar(S.at(bar) + 14 * ST, c, "stab", amp)


# ---------------------------------------------------------------- feedback, sirens, chip (pads, fx)
def feedback(bar0, bars, kind="drone", amp=1.0):
    """A guitar feeding back: a sine on F6 and its 2nd harmonic, 5.5 Hz vibrato, tanh(4x). swell: rising from
    nothing; whine: louder and bending up a semitone."""
    d = bars * S.bar
    t = e.tt(d)
    bend = 1 + (t / d) * (2 ** (1 / 12) - 1) if kind == "whine" else 1.0
    f = e.hz(89) * bend * (1 + .004 * np.sin(2 * np.pi * 5.5 * t))
    ph = np.cumsum(f) / SR
    x = np.sin(2 * np.pi * ph) + .5 * np.sin(4 * np.pi * ph)
    env = {"swell": (t / d) ** 2, "drone": np.minimum(t / .4, 1) * np.minimum((d - t) / .2, 1),
           "whine": np.minimum(t / .05, 1) * np.minimum((d - t) / .05, 1)}[kind]
    y = np.tanh(4 * x * .35) * env
    put("pads", S.at(bar0), y, .55, (.16 if kind == "whine" else .1) * amp, wet=.3)


def siren(bar0, bars, amp=1.0):
    """The two-tone: a square and a saw switching C5 / F5 every beat, band-passed, sweeping slowly across."""
    t = e.tt(bars * S.bar)
    f = np.where((t // BT).astype(int) % 2 == 0, e.hz(72), e.hz(77))
    x = e.bandpass(.5 * e.pulse(f, t) + .5 * e.saw(f, t), 600, 3000)
    p = .5 + .4 * np.sin(2 * np.pi * t / (4 * S.bar))
    st = np.stack([x * np.cos(p * np.pi / 2), x * np.sin(p * np.pi / 2)], 1)
    put("fx", S.at(bar0), st, amp=.07 * amp, wet=.2)


def whoop(bar0, bars, amp=1.0):
    t = e.tt(bars * S.bar)
    u = t / t[-1]
    f = 300 * 5 ** u
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * u ** 1.5
    put("fx", S.at(bar0), x, .5, .12 * amp, wet=.25)


def blip(m, d, amp=1.0):
    t = e.tt(d)
    return e.pulse(e.hz(m), t, .25) * e.gate(t, d - .004, .002) * e.rise(t, .001) * .3 * amp


JINGLE = np.concatenate([blip(m, ST / 2) for m in (89, 92, 96)])      # the boot chime: F6 Ab6 C7 in 32nds


def chip_arp(bar):
    for k in range(32):
        put("fx", S.at(bar) + k * ST / 2, blip((77, 80, 84, 89)[k % 4], ST / 2), .35 + .3 * (k % 2), .7, wet=.1)


def usb_click(t):
    """USB-C going in: 2 ms of noise (2-6 kHz) and a 4 ms tick at 1 kHz, dry."""
    n = e.bandpass(e.rng.standard_normal(int(.002 * SR)), 2000, 6000)
    k = np.sin(2 * np.pi * 1000 * e.tt(.004)) * np.exp(-e.tt(.004) * 900)
    put("perc", t, pad_sum(n * 1.5, k), .5, 1.0, wet=0)


def esptool(bar, steps=range(5), unders=(), amp=1.0):
    """esptool's '.....' (60 ms blips on C6, one a sixteenth) and '_____' (legato eighths on C5)."""
    for k in steps:
        put("fx", S.at(bar) + k * ST, blip(84, .06), .5, .8 * amp, wet=.05)
    for k in unders:
        put("fx", S.at(bar) + k * ST, blip(72, 2 * ST), .5, .8 * amp, wet=.05)


def rom_garbage(t, d):
    """The boot ROM's log read at the wrong baud rate is noise (the ESP32s log at 115200): random 8-N-1 bytes as a 1-bit
    square at SR/20 bits a second, high-passed, about -12 dB."""
    r = np.random.default_rng(74880)
    nbits = int(d * SR / 20)
    bits = []
    while len(bits) < nbits:
        bits += [0] + list(r.integers(0, 2, 8)) + [1] + [1] * int(r.integers(0, 3))
    x = np.repeat(np.array(bits[:nbits]) * 2.0 - 1, 20)
    put("fx", t, fade(e.highpass(x, 300), 3), .5, .25, wet=0)


# ---------------------------------------------------------------- the glitch pass
def _span(t0, t1):
    assert LO - 1e-6 <= t0 <= t1 <= HI + 1e-6, f"a glitch at {t0:.2f}-{t1:.2f} s touches the DJ's drums-only ends"
    return int(round(t0 * SR)), int(round(t1 * SR))


def _bufs(buses):
    """The buses (and with buses=None also the reverb and delay sends, so their tails follow the edit)."""
    return [S.bus[k] for k in (buses or e.BUSES)] + ([S.send, S.echo] if buses is None else [])


def loop(src_t, L, t0, t1, buses=None):
    """Repeat the slice of length L from src_t across t0..t1."""
    i0, i1 = _span(t0, t1)
    s0, n = int(round(src_t * SR)), int(round(L * SR))
    for b in _bufs(buses):
        src = fade(b[s0:s0 + n], 1).astype(np.float32)
        k = 0
        while True:
            a = int(round((t0 + k * L) * SR))
            if a >= i1:
                break
            m = min(n, i1 - a)
            b[a:a + m] = src[:m]
            k += 1


def stutter(t0, L, n, buses=None):
    loop(t0, L, t0, t0 + n * L, buses)


def crush(t0, t1, bits, hold, buses=None):
    i0, i1 = _span(t0, t1)
    for k in (buses or e.BUSES):
        S.bus[k][i0:i1] = bitcrush(S.bus[k][i0:i1], bits, hold).astype(np.float32)


def tape_stop(t0, d, buses=None):
    """Per channel, read slower and slower until it stops (low_battery.tape_stop: the rate from 1 to 0, exponent
    1.4), then silence to t0 + d."""
    i0, i1 = _span(t0, t0 + d)
    n = i1 - i0
    rate = np.linspace(1, 0, n) ** 1.4
    pos = np.cumsum(rate) - rate[0]
    tail = np.minimum((n - np.arange(n)) / (.25 * n), 1)        # no thump where it stops
    for b in _bufs(buses):
        src = b[i0:i1].astype(np.float64)
        for ch in range(2):
            b[i0:i1, ch] = (np.interp(pos, np.arange(n), src[:, ch]) * tail).astype(np.float32)


def cut(t0, t1, buses=None):
    """Zero everything (or these buses) from t0 to t1, with 2 ms ramps."""
    i0, i1 = _span(t0, t1)
    r = int(.002 * SR)
    down, up = np.linspace(1, 0, r)[:, None], np.linspace(0, 1, r)[:, None]
    for b in _bufs(buses):
        b[i0 - r:i0] *= down
        b[i0:i1] = 0
        if i1 + r <= int(round(HI * SR)):
            b[i1:i1 + r] *= up


def dropouts(bar0, bar1, rate0, rate1, seed=57):
    """The flaky USB cable (MORE FLUX's cold joint): drums, perc, keys and bass gone on random sixteenths, more
    and more often; the voices and the fx never."""
    i0, i1 = _span(S.at(bar0), S.at(bar1))
    r = np.random.default_rng(seed)
    g = np.ones(i1 - i0)
    n = (bar1 - bar0) * 16
    for k in range(n):
        if r.random() < rate0 + (rate1 - rate0) * k / (n - 1):
            a, b = int(round(k * ST * SR)), int(round((k + 1) * ST * SR))
            g[a:b] = 0
    g = np.minimum(g, e.one_pole(g, .0015))                 # 5 ms ramps, both ways
    g = np.minimum(g, e.one_pole(g[::-1], .0015)[::-1])
    for k in ("drums", "perc", "keys", "bass"):
        S.bus[k][i0:i1] *= g[:, None].astype(np.float32)


HOOKS = (39, 47, 79, 103, 111)


def glitch():
    # loops
    loop(S.at(40), S.bar / 2, S.at(68), S.at(69))              # FLASH the C- FLASH the C-
    loop(S.at(40), S.bar / 4, S.at(69), S.at(70))              # FLASH! FLASH! FLASH! FLASH!
    loop(S.at(40), S.bar / 8, S.at(70), S.at(71, 2))           # FL-FL-FL-FL...
    loop(S.at(110), S.bar, S.at(120), S.at(122))
    for k, div in enumerate((2, 4, 8, 16)):                    # 1/16 bar: an 11.6 Hz buzz
        loop(S.at(110), S.bar / div, S.at(122 + k), S.at(123 + k))
    loop(S.at(110), S.bar / 32, S.at(126), S.at(127, 2))       # 1/32: 23 Hz
    # stutters: the flash speeding up
    stutter(S.at(60, 3), ST, 4, buses=("drums", "perc", "keys", "bass"))
    stutter(S.at(61, 3), ST / 2, 8, buses=("drums", "perc", "keys", "bass"))
    stutter(S.at(62, 1), ST / 2, 8, buses=("drums", "perc", "keys", "bass"))
    # crushes
    crush(S.at(65), S.at(67), 6, 2, buses=("drums",))
    crush(S.at(127), S.at(127, 2), 1, 8)
    # tape stops
    tape_stop(S.at(47, 3), BT)                                 # into the authority
    tape_stop(S.at(71), 2 * BT)                                # the boot loop dies
    # cuts
    for b in HOOKS:
        if b != 47:                                            # beat 4: the band out, only the chop
            cut(S.at(b, 3), S.at(b + 1), buses=("drums", "perc", "bass", "keys", "pads"))
    dropouts(57, 60, .05, .30)
    cut(S.at(55, 3), S.at(56))
    cut(S.at(64), S.at(64, 2))
    cut(S.at(127, 2), S.at(128))
    i0, i1 = _span(S.at(126), S.at(128))                       # no tail rings under "Told you."
    S.send[i0:i1] = 0
    S.echo[i0:i1] = 0


# ---------------------------------------------------------------- the arrangement
RIOT_A = {32: "MF", 33: "GANG", 34: "MF", 35: "GANG", 36: "MF", 37: "GANG", 38: "ALL"}
for bar in range(BARS):
    intro, outro = bar < 16, bar >= 128
    riot_a, riot_c = 32 <= bar < 47, 96 <= bar < 111
    riot_b = 72 <= bar < 79
    is_hook = bar in HOOKS

    # ---- drums
    if bar < 8:
        brk(bar)
    elif bar < 16 or 128 <= bar < 140:
        brk(bar, kick=False)
        four(bar)
    elif bar >= 140:
        brk(bar)
    elif 16 <= bar < 31:
        brk(bar, kick=False)
        four(bar)
    elif bar in (72, 74):                   # under a grievance: the gabber and the hats only, no snares
        brk(bar, pat=dict(kick="", clap="", hat=BREAK_A["hat"]))
        four(bar)
    elif 76 <= bar < 79:                    # the name call: the drums answer in the gaps, nothing under the words
        for k in (4, 12):
            gabber(S.at(bar) + k * ST)
            put("drums", S.at(bar) + k * ST, SNARE_X, .5, 1.0, wet=.18)
        for k in (5, 6, 7, 13, 14, 15):
            put("perc", S.at(bar) + k * ST, HAT_X, .62, .6, wet=.04)
    elif riot_a or riot_b or riot_c or is_hook:
        steps = 16 if (not is_hook or bar == 47) else 12
        brk(bar, kick=False, steps=steps)
        four(bar, steps=steps)
    elif 48 <= bar < 56 or 88 <= bar < 92:
        half(bar, .8)
    elif bar in (58, 59):                   # under "Hold boot!" (steps 0-8) only the hats; the break after it
        brk(bar, .5, pat=dict(kick="", clap="", hat=BREAK_A["hat"]), steps=9)
        brk(bar, .8, pat=dict(kick="." * 9 + BREAK_A["kick"][9:], clap="." * 9 + BREAK_A["clap"][9:], hat="." * 9
                              + BREAK_A["hat"][9:]))
    elif 56 <= bar < 63:
        brk(bar, .8, until=S.at(62, 2))
    elif bar in (65, 66, 67):
        gabber(S.at(bar))
    elif 80 <= bar < 88 or 112 <= bar < 116:
        half(bar)
    elif 116 <= bar < 120:
        gabber(S.at(bar))
        gabber(S.at(bar) + 10 * ST)
    if bar in (0, 32, 40, 72, 80, 96, 104, 112, 128):
        crash(bar)

    # ---- bass
    if 20 <= bar < 31 or riot_a or riot_b or riot_c:
        bass(bar, "eighths")
    elif is_hook:
        bass(bar, "eighths", steps=16 if bar == 47 else 12)
    elif 48 <= bar < 56 or 88 <= bar < 92:
        bass(bar, "whole", .9, root=29)
    elif 56 <= bar < 62:
        bass(bar, "eighths", .9, root=29)
    elif bar == 62:
        bass(bar, "eighths", .9, steps=8, root=29)
    elif 80 <= bar < 88 or 112 <= bar < 116:
        bass(bar, "whole")

    # ---- guitars
    if 20 <= bar < 31:
        gtr_riot(bar, push=False, amp=.8)
    elif bar in (72, 74):                                      # under a whole-bar grievance: palm only
        gtr_riot(bar, push=False)
    elif 76 <= bar < 79:                                       # the name call: stabs in the gaps only
        for k in (4, 12):
            guitar(S.at(bar) + k * ST, chord_of(bar), "stab")
    elif is_hook:                                              # an open F5 with each SIX!
        for b in range(3):
            guitar(S.at(bar, b), "F", "beat", 1.1)
        if bar == 47:                                          # beat 4 plays on, into the tape stop
            for k in (12, 14):
                guitar(S.at(bar) + k * ST, "F", "palm", .9)
    elif riot_a or riot_b or riot_c:
        gtr_riot(bar)
    elif bar in (48, 52, 88):
        guitar(S.at(bar), "F", "ring", .8)
    elif 56 <= bar < 62 or bar == 62:
        for k in range(16 if bar < 62 else 8):
            if not (bar in (58, 59) and k < 9 or bar == 56 and 4 <= k < 12):   # stops dead under "Hold boot!"
                                                                                # and "Connecting."
                guitar(S.at(bar) + k * ST, "F", "palm", .8)
    elif 80 <= bar < 88 or 112 <= bar < 116:
        if bar % 2 == 1:                                       # bar b: a choked stab with the room's first clap
            guitar(S.at(bar) + 8 * ST, "F", "stab", 1.0)

    # ---- the chant
    if bar in RIOT_A:
        riot(bar, RIOT_A[bar])
    if bar - 64 in RIOT_A:
        riot(bar, RIOT_A[bar - 64])
    if 40 <= bar < 47 or 104 <= bar < 111:
        riot(bar, "ALL")
    if is_hook:
        hook(bar)
        if bar != 47:
            chop(S.at(bar, 3))       # at 2.0 the ear took the c-c-c-c into the next bar as "6, 6, 6, 6..."
    if bar in (73, 75):
        riot(bar, "GANG")
    if 76 <= bar < 79:
        name(bar)
    for b0, who in ((50, "GANG"), (54, "ALL"), (80, "MF"), (82, "GANG"), (84, "ALL"), (86, "GANG"), (90, "GANG"),
                    (112, "ALL"), (114, "ALL"), (116, "ROOM"), (118, "ROOM")):
        if bar == b0:
            terrace(bar, who)
    if 104 <= bar < 111:                                       # a quiet C6 blip after each shout
        put("fx", S.at(bar) + 15 * ST, blip(84, .03), .5, .6, wet=.05)

# ---- the band arrives
feedback(16, 4, "swell")
siren(16, 4)
for b in range(24, 28):
    chip_arp(b)
for b in (24, 28):
    chop(S.at(b) + 8 * ST, six=True, amp=.9)
whoop(28, 3)
roll(29, 2)
count_in(31)

# ---- the authority
siren(48, 8)
feedback(48, 8, "drone")
authority(S.at(48), "Warning. That is the C six.")
authority(S.at(52), "Do not flash the C six.")

# ---- the flash
usb_click(S.at(56))
put("vox", S.at(56, 1), readout("Connecting."), .5, .8, wet=.15, echo=.15)
esptool(56, steps=range(8, 13))
for b in (57, 58, 59):
    esptool(b, steps=range(5) if b == 57 else (), unders=(5, 7, 9, 11, 13) if b == 57 else (9, 11, 13),
            amp=1.0 if b == 57 else .4)       # nothing under "Hold boot!" (alone the ear heard it; in the mix "Halt boot")
call("F", S.at(58), "Hold boot!", .69, 1.3)         # at .52 s the ear heard "Whole food"
call("GANG", S.at(59), "Hold boot!", .69, 1.3, spread=.2)
_d0, _fl = stack(voices("M", "Flash!", .3))                    # one take, retriggered, a semitone up each beat
for b in range(10):
    bar, beat = 60 + b // 4, b % 4
    per = {60: 1, 61: 2, 62: 4}[bar]
    for j in range(per):
        y = repitch(_fl, b)
        y = fade(y[:int((BT / per - .004) * SR)], 3)
        put("vox", S.at(bar, beat + j / per) - EARLY + _d0, y, amp=1.0, wet=0)
roll(60, 3, until=S.at(62, 2))
whoop(60, 3)
put("vox", S.at(62, 2), readout("Hard resetting via R T S pin."), .5, .85, wet=0)
feedback(63, 1, "whine", .8)

# ---- the crash
rom_garbage(S.at(64, 2), 2 * BT)
_guru = readout("Goo roo meditation error. Core zero panicked.")
_i = len(V._finish(V.tts("Goo roo meditation error.", READOUT)))         # clean up to the end of "error"
_guru[_i:] = bitcrush(_guru[_i:], 8, 4)
put("vox", S.at(65), _guru, .5, .85, wet=.1, echo=.1)
feedback(65, 2, "whine")
_d0, _pa = stack(voices("F", "Panic!", .3))
for b, (hold, bits) in enumerate(((2, 12), (4, 8), (8, 6), (16, 4))):    # 22050, 11025, 5512, 2756 Hz
    put("vox", S.at(67, b) - EARLY + _d0, bitcrush(_pa, bits, hold), amp=1.0, wet=.12)

# ---- riot B: the grievances
call("M", S.at(72), "Wifi is down!", S.bar - ST, 1.2)
call("F", S.at(74), "Old firmware!", S.bar - ST, 1.2)

# ---- the authority caves
siren(88, 4, .8)
feedback(88, 7, "drone")
_dnf = take("Do not flash the C six.", 1.68, AUTHORITY, .84)
for k in range(4):
    put("vox", S.at(88) + k * ST, fade(_dnf[:int(ST * SR)], 2), .5, 1.1, wet=.25, echo=.1)
authority(S.at(88, 1), "Do not flash the C six.")
authority(S.at(92), "Fine. Flash the C six.")
roll(93, 2)
whoop(93, 2)
count_in(95)

# ---- the terraces' drone
feedback(80, 8, "drone", .8)
feedback(112, 4, "drone", .8)

if os.environ.get("GLITCH", "1") == "1":
    glitch()

# ---- after the glitch pass: the boot chimes, the double-speed count-in, the authority's last word
for b in (68, 69, 70, 120, 121, 122, 123):
    put("fx", S.at(b), JINGLE, .5, .9 if b < 100 else .5, wet=.1)   # 120-123: softer, over the looped "Flash!"
count_in(71, 2, .5, .17)
put("vox", S.at(127, 2), take("Told you.", .55, AUTHORITY, .84), .5, 1.1, wet=0, echo=0)

# ---------------------------------------------------------------- the mixdown
cut_keys = [(0, 18000), (S.at(16), 18000), (S.at(16) + .05, 700), (S.at(30.9), 6000), (S.at(31) - .005, 6000),
            (S.at(31), 18000), (S.n / SR, 18000)]   # the master filter: the band arrives behind it
NAME = f"{os.path.basename(__file__)[:-3].replace('_', '-')}_{BPM}bpm_{KEY}"
OUT = parts.out_path(NAME)
S.mixdown(OUT, {"drums": 1.0, "perc": .7, "bass": .9, "pads": .7, "keys": 1.0, "lead": .6, "vox": 1.5, "fx": .6},
          cut_keys=cut_keys, duck={"pads": .7, "bass": .45, "keys": .35}, room=.15, echo_mix=.3, lufs=LUFS,
          ir=room.impulse_response((8.0, 6.0, 3.5), rt60=1.0))


def written(path):
    """Where mixdown wrote it: a test render (PREVIEW, SOLO, MUTE, GAIN) goes to renders/scratch/."""
    test = [f"{k.lower()}{os.environ[k]}" for k in ("PREVIEW", "SOLO", "MUTE", "GAIN") if os.environ.get(k)]
    renders = os.path.join(os.path.dirname(os.path.abspath(e.__file__)), "renders")
    if test and os.path.dirname(os.path.abspath(path)) == renders:
        stem = os.path.splitext(os.path.basename(path))[0]
        path = os.path.join(renders, "scratch", re.sub(r"[^\w.+-]", "", f"{stem}-{'-'.join(test)}") + ".wav")
    return path


def true_silence(path, holes):
    """Zero these stretches of the written WAV (2 ms ramps): digital silence, no reverb tail in the holes."""
    with wave.open(path) as w:
        params, x = w.getparams(), np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, 2).astype(np.float64)
    shift = S.at(int(os.environ["PREVIEW"].split("-")[0])) if os.environ.get("PREVIEW") else 0.0
    r = int(.002 * SR)
    for t0, t1 in holes:
        i0, i1 = int(round((t0 - shift) * SR)), int(round((t1 - shift) * SR))
        if i0 - r < 0 or i1 + r > len(x):
            continue
        x[i0 - r:i0] *= np.linspace(1, 0, r)[:, None]
        x[i0:i1] = 0
        x[i1:i1 + r] *= np.linspace(0, 1, r)[:, None]
    with wave.open(path, "wb") as w:
        w.setparams(params)
        w.writeframes(np.round(x).astype("<i2").tobytes())


if os.environ.get("GLITCH", "1") == "1":
    true_silence(written(OUT), [(S.at(55, 3), S.at(56)), (S.at(64), S.at(64, 2))])
print(f"{len(_takes)} voice takes rendered")
print(f"share.SONGS row: (\"{NAME}.wav\", \"{TITLE}\", \"{DAY}\", {BPM}, \"{KEY}\", {BARS}),")
