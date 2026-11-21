#!/usr/bin/env python3
"""Low Battery Lullaby: 90's mellow house, 120 BPM, D minor. Saturday's theme of the AI slop music compo.

low_battery.py [OUT.wav]   (default renders/low-battery_120bpm_Dm.wav)

Every note and every sound here is written by Claude, in this file: no samples, no loops. Sunrise after the
party, and the laptop is dying. A DX7 Rhodes on minor ninths, a warm sub bass, shuffled 909 hats, soft rimshots,
an airy pad with a choir of "ooh"s, an M1 organ, vinyl dust, and a chopped female vocal "sample" that is not a
sample: Piper TTS sings "low battery", "ten percent", "charging" and "sleep mode" (voice.py), and this file chops
it. The battery-warning beep is the hook, a deadpan system voice reads the battery level out loud, and in the
break the beep plays Brahms' lullaby (1868, public domain) while the laptop goes to sleep. It wakes up "fully
charged", runs down again, and at the end the music stops like a tape when the power goes. The first and last 16
bars are drums only, for the DJ.

  bars   0-15  intro: kick and hats, then clap, rimshots and shaker (drums only)
        16-31  the sub bass; the Rhodes behind a door; "battery low", and the first beeps
        32-47  verse: Rhodes, airy pad, the first chops ("low battery"); "ten percent remaining"
        48-63  groove: the chop hook (low battery / ten percent / ch-ch-charging / sleep mode), M1 organ,
               the "ooh" choir; a soft DX7 melody from bar 56
        64-71  break, "sleep mode": no kick, no bass, the lights low; the beep sings the lullaby;
               "please connect charger", then a charging chime and a riser
        72-87  groove again, "fully charged": a hundred percent, wide awake; the melody and a drawbar organ
        88-103 running down: ten, five, one percent; "shutting down, good night"; the music tape-stops
       104-119 outro: drums only

The singer (singer D, 21 November): Lem the Shapeshifter DS 2.5 (DiffSinger) sings the written notes and words
of the chops (parts.Band, diva_voice="ds:lem"), and SoulX-Singer SVC turns her into a husky, intimate Qwen voice
(sing_qwen_husky: a lullaby wants a soft late-night voice, not a gospel diva). One singer, no doubles, no harmony,
no vocoder, no "ooh" choir: sparse, like the records. The sampler tricks stay: the "ch-ch-ch" stutter and the two
reversed words are cut from her own take. Lines that go above D5 ("charging") are sung an octave lower. Shape her
fast with Lem alone: DS_TIMBRE= SOLO=vox PREVIEW=48-56 .venv/bin/python low_battery.py.
SINGER=en_GB-jenny_dioco-medium: the approved version, Piper re-pitched and chopped, with the Piper "ooh" choir.

Voices (Piper, code/voices/): en_US-amy-medium is the laptop's system voice (through a small speaker); with
SINGER=<a Piper voice> that voice sings the chops and en_GB-cori-high, en_US-kristin-medium and
en_US-ljspeech-high are the "ooh" choir. The reverb is a simulated room (room.py): a bedroom, 4.5 x 3.6 x 2.6 m.
"""
import os
import sys

import numpy as np

import engine as e
import dx7
import parts
import room
import voice as V

e.seed(1001)    # 0x3E9: the battery's serial number
S = e.Song(bpm=120, bars=120)
STEP = S.step
B = S.beat
SWING = .16 * STEP          # 58 % shuffle on the sixteenths

SINGER = os.environ.get("SINGER", "ds:lem")    # SINGER=en_GB-jenny_dioco-medium: the approved Piper chops
LEM = SINGER.startswith("ds:")
SYSTEM = os.environ.get("SYSTEM", "en_US-amy-medium")
CHOIR = ["en_GB-cori-high", "en_US-kristin-medium", "en_US-ljspeech-high"]

PROG = ["Dm9", "Bbmaj9", "Gm9", "Am7"]
BREAK = ["Fmaj9", "Bbmaj9", "Gm9", "Am7"]     # the break goes to the relative major, for the lullaby

# the Rhodes voicings, by hand: rootless, close, around middle C, the top note moving by a step at most
KEYS = {"Dm9": [53, 57, 60, 64], "Bbmaj9": [57, 60, 62, 65], "Gm9": [58, 62, 65, 69], "Am7": [55, 60, 64, 69],
        "Fmaj9": [57, 60, 64, 67]}


def is_break(bar):
    return 64 <= bar < 72


def chord_of(bar):
    return (BREAK if is_break(bar) else PROG)[bar % 4]


def sw(k):
    """The time of sixteenth k in a bar, swung."""
    return k * STEP + (SWING if k % 2 else 0)


# singer D: Lem sings the chops' notes and words, one Qwen voice, nothing on top (90's mellow house: sparse)
TIMBRE = "sing_qwen_husky"          # soft, breathy, intimate: a lullaby (sing_qwen_soul: a gospel diva, too big)
P = parts.Band(S, PROG, diva_voice=SINGER, timbre=TIMBRE, stack="", harmony="", accent={"battery": 2},
               verse_double=0.0) if LEM else None
# no breath before her phrases (parts.LEM has one): before "low battery" it came out "hello battery" (Whisper, Lem
# alone, bars 32-63: "low battery" 4 of 8 without the breath, 2 of 8 with it; "ten percent" 4 of 4 against 3 of 4).
# DS_BREATH=1 brings it back.
BREATHS = False
if LEM:
    P.ds_gain = 1.7       # a lullaby: a little under Common Ground's 2.0 (her vox bus -11 LUFS, the hook every bar)

# ---------------------------------------------------------------- my own sounds
# a DX7 patch for the melody: the E.Piano's shape, but the modulators lower and scaled down hard over the keyboard,
# and the bell at ratio 4 instead of 14, so the high notes stay round (a high FM piano goes "harpsichord")
dx7.PATCHES["nightlight"] = dict(algo=5, feedback=2, gain=2.0, ops=[
    dx7.op(1, 0, 0, 99, (95, 26, 20, 55), (99, 84, 0, 0), vel=.4),             # 1 carrier: body
    dx7.op(1, 0, 0, 70, (95, 32, 20, 60), (99, 72, 0, 0), vel=.8, ks=9),       # 2 -> 1: a soft edge
    dx7.op(1, 0, 4, 92, (92, 22, 20, 55), (99, 88, 0, 0), vel=.3),             # 3 carrier, a little sharp
    dx7.op(4, 0, 0, 60, (99, 55, 50, 70), (99, 0, 0, 0), vel=1.0, ks=12),      # 4 -> 3: the ping, short
    dx7.op(1, 0, -4, 82, (95, 22, 20, 55), (99, 82, 0, 0), vel=.3),            # 5 carrier, a little flat
    dx7.op(1, 0, 0, 60, (95, 24, 20, 60), (99, 80, 0, 0), vel=.6, ks=9),       # 6 -> 5
])


def rhodes(m, d, vel):
    return dx7.note("epiano", m, d, vel, tail=.9)


def nightlight(m, d, vel):
    return dx7.note("nightlight", m, d, vel, tail=1.0)


def beep(m, d, a=1.0):
    """The battery warning: a sine with a little third harmonic (a small speaker's square wave, worn round)."""
    t = e.tt(d + .03)
    f = float(e.hz(m))
    g = np.sin(2 * np.pi * f * t) + .12 * np.sin(2 * np.pi * 3 * f * t)
    return g * e.rise(t, .003) * e.gate(t, d, .012) * a * .5


def drawbar(notes, d, a=1.0):
    """Stereo: a Hammond-ish organ held under the chords, three drawbars (16', 8', 4'), a slow Leslie."""
    t = e.tt(d + .1)
    out = np.zeros((len(t), 2))
    for m in notes:
        f = float(e.hz(m))
        g = .5 * np.sin(2 * np.pi * f / 2 * t) + np.sin(2 * np.pi * f * t) + .35 * np.sin(2 * np.pi * f * 2 * t)
        out[:, 0] += g * (1 + .25 * np.sin(2 * np.pi * .8 * t))
        out[:, 1] += g * (1 + .25 * np.sin(2 * np.pi * .8 * t + 2.0))
    env = e.rise(t, .05) * e.gate(t, d, .06)
    return out * env[:, None] * a / max(len(notes), 1) * .5


def tape_stop(x, seconds):
    """Read x slower and slower until it stops: the power going out."""
    n = int(seconds * e.SR)
    rate = np.linspace(1, 0, n) ** 1.4
    pos = np.cumsum(rate)
    pos = pos[pos < len(x) - 1]
    i = pos.astype(int)
    w = pos - i
    return x[i] * (1 - w) + x[i + 1] * w


def speaker(x):
    """A laptop's little speaker: no lows, no highs, a little crunch."""
    return np.tanh(e.bandpass(x, 380, 3800) * 2.5) * .6


# ---------------------------------------------------------------- drums
def drums(bar, kick=True, clap=True, hats=True, shaker=False, rimshots=False, congas=False, crash=False, amp=1.0):
    t0 = S.at(bar)
    if kick:
        for b in range(4):
            S.kick(t0 + b * B, .95 * amp, punch=85, base=45, length=.42, click=.12)
    if clap:
        for b in (1, 3):
            S.put("drums", t0 + b * B, e.clap(.42 * amp), .5, wet=.3)
            S.put("drums", t0 + b * B, e.snare(.14 * amp), .5, wet=.2)
    if hats:
        for k in range(16):
            if k % 4 == 2:
                S.put("perc", t0 + sw(k), e.hat(.4 * amp, opened=True), .6, wet=.1)
            else:
                a = (.2 if k % 2 else .28) * amp * (1 + .15 * np.sin(bar * 1.3 + k))
                S.put("perc", t0 + sw(k), e.hat(a), .64, wet=.05)
    if shaker:
        for k in range(16):
            S.put("perc", t0 + sw(k), e.shaker((.32 if k % 2 else .18) * amp), .32, wet=.08)
    if rimshots:     # soft, off the grid's strong beats, a different figure every other bar
        for k in ((3, 6, 11, 14) if bar % 2 else (3, 10, 13)):
            S.put("perc", t0 + sw(k), e.rim(.28 * amp), .42, wet=.25, echo=.12)
    if congas:
        for k, m, a in ((7, 62, .3), (10, 57, .35), (11, 57, .22), (15, 62, .25)):
            S.put("perc", t0 + sw(k), e.conga(m, a * amp), .7, wet=.2)
    if crash:
        S.put("perc", t0, e.crash(.4), .5, wet=.3)


# ---------------------------------------------------------------- bass
BASSLINE = [(0, 0, 3), (3, 0, 1), (6, 7, 1), (8, 0, 2), (11, 12, 1), (12, 7, 2), (14, 0, 1)]


def bass(bar, amp=1.0):
    """A warm sub: the root low (G1 to D2), the fifth and the octave for the bounce."""
    root = e.root_note(chord_of(bar), lo=31)
    for k, iv, n in BASSLINE:
        S.put("bass", S.at(bar) + sw(k), e.deep_bass(root + iv, n * STEP * .9), .5, .9 * amp, wet=0)


# ---------------------------------------------------------------- keys
RHODES_COMP = [(0, 4, .7), (7, 2, .5), (10, 5, .65)]    # sixteenth, length in sixteenths, velocity


def rhodes_comp(bar, amp=1.0, cut=None):
    notes = KEYS[chord_of(bar)]
    hits = RHODES_COMP + ([(15, 1, .45)] if bar % 4 == 3 else [])   # a push into the next bar
    for k, n, vel in hits:
        if k == 15:
            notes_k = KEYS[chord_of(bar + 1)]
        else:
            notes_k = notes
        for j, m in enumerate(notes_k):
            g = rhodes(m, n * STEP, vel)
            if cut:
                g = e.lowpass(g, cut)
            pan = .5 + .3 * np.sin(2 * np.pi * (bar + k / 16) / 2)   # a tremolo that pans, one cycle in 2 bars
            S.put("keys", S.at(bar) + sw(k) + j * .007, g, pan, .4 * amp, wet=.3, echo=.12)


ORGAN = [2, 6, 9, 14]


def organ_stabs(bar, amp=1.0):
    notes = e.close_voicing(chord_of(bar), lo=60, hi=74)[:4]
    for k in ORGAN:
        for m in notes:
            S.put("keys", S.at(bar) + sw(k), e.organ(m, STEP * 1.1), .4, .26 * amp, wet=.25, echo=.15)


def organ_hold(bar, amp=1.0):
    S.put("keys", S.at(bar), drawbar(KEYS[chord_of(bar)], S.bar * .98), amp=.5 * amp, wet=.3)


def pads(bar, amp=1.0, cut=1500):
    notes = e.voicing(chord_of(bar), lo=50)
    S.put("pads", S.at(bar), e.pad(notes, S.bar, cut=cut, a=.6, r=1.0), amp=.45 * amp, wet=.45)


_sung = {}


def sung(word, notes, voice, vibrato=.2, take=0, cents=0.0):
    """voice.sing, remembered: a chop that comes back is the same piece of audio, as from a sampler."""
    key = (word, tuple((m, round(d, 3)) for m, d in notes), voice, vibrato, take, cents)
    if key not in _sung:
        _sung[key] = V.sing(word, [(m, round(d, 3)) for m, d in notes], voice=voice, vibrato=vibrato, take=take,
                            cents=cents)
    return _sung[key]


def oohs(bar, amp=1.0):
    """The airy part of the pad: three women sing "ooh" on the top of the chord, a bar long, soft in and out."""
    top = KEYS[chord_of(bar)][1:] if chord_of(bar) != "Am7" else [64, 67, 69]
    for j, (m, v) in enumerate(zip(top, CHOIR)):
        li, y = sung("ooh", [(m, S.bar * 1.05)], v, vibrato=.12)
        n = len(y)
        env = np.minimum(np.arange(n) / (.35 * e.SR), 1) * np.minimum((n - np.arange(n)) / (.5 * e.SR), 1)
        S.put("pads", S.at(bar) - li, y * env, .2 + .3 * j, .32 * amp, wet=.6, echo=.1)


# ---------------------------------------------------------------- the chops
def words_on(notes, words):
    """Pair words with notes: a word takes its note and one more for each "+" after it."""
    out, toks, i = [], words.split(), 0
    for k, w in enumerate(toks):
        if w == "+":
            continue
        span = 1
        while k + span < len(toks) and toks[k + span] == "+":
            span += 1
        out.append((w, notes[i:i + span]))
        i += span
    assert i == len(notes), (words, len(notes))
    return out


def chop(bar, line, words, amp=1.0, pan=.5, echo=.25, cut=None):
    """A chopped vocal line: each word sung on its note, then cut off hard at the end of the note (a sampler's
    gate), the way a house record chops a vocal."""
    for w, ns in words_on(S.notes(bar, line), words):
        t = ns[0][0]
        li, y = sung(w, [(m, d * .95) for _, m, d in ns], SINGER)
        end = int((li + sum(d for _, _, d in ns) + .03) * e.SR)
        y = y[:end].copy()
        k = min(int(.012 * e.SR), len(y))
        y[-k:] *= np.linspace(1, 0, k)
        swing = SWING if round((t - S.at(bar)) / STEP) % 2 else 0
        if cut:
            y = e.lowpass(y, cut)
        S.put("vox", t + swing - li, y, pan, amp, wet=.2, echo=echo)


# the words as Lem reads them (real English words; "+" holds a word over the next note)
DS_WORDS = {"ten per cent": "ten percent +",
            "five per cent": "five percent +", "one per cent": "one percent +", "char jing": "charging +",
            "full lee charged": "fully + charged", "a hun dred per cent": "a hundred + percent +",
            "wide a wake": "wide awake +"}


# Lem's rhythm where the chop's slurred: "char" on a quarter (on an eighth Whisper heard "touching", "chanting")
DS_LINES = {". . . . . . F5 - D5 - - - . . . .": ". . . . F5 - - - D5 - - - . . . .",
            ". . A4 - - . C5 - A4 - . . A4 . A4 .": ". . A4 - - . C5 - A4 - . . A4 - A4 -",   # "low low": eighths
            ". . D5 - . C5 - - A4 - - - . . . .": ". . D5 - - C5 - - A4 - - - . . . .",   # "ten" longer
            ". . A4 - - . C5 - D5 - - . . . . .": ". . A4 - - - C5 - D5 - - . . . . ."}   # "fully" legato: one word
CHAR_AT = 1.0                       # the beat where Lem's "charging" starts (the stutter is cut from it)


def vocal(bar, line, words, amp=1.0, echo=.25, cut=None):
    """A line of the chops: Lem's take (singer D) or the Piper chop. Lem sings at the written pitch, a line that
    goes above D5 an octave lower (her realistic top)."""
    if not LEM:
        chop(bar, line, words, amp, echo=echo, cut=cut)
        return
    line = DS_LINES.get(line, line)
    top = max(e.midi(tok) for tok in line.split() if tok not in "-.")
    P.diva(bar, line, DS_WORDS.get(words, words), amp=amp, octave=-24 if top > 74 else -12)


_lem = {}          # Lem's lead take, as Band.finish rendered it (for the stutter and the reversed words)
_after = []        # the sampler tricks on her take, done once it exists


def lem_cut(t0, t1):
    """A piece of Lem's take from t0 to t1 seconds, at the level she has in the mix."""
    y = _lem.get("y")
    if y is None:
        return np.zeros(1)
    i, j = max(int(t0 * e.SR), 0), min(int(t1 * e.SR), len(y))
    return y[i:j] * float(os.environ.get("DS_GAIN", P.ds_gain)) if j > i else np.zeros(1)


def stutter(bar, k, word, m, n=3, amp=1.0):
    """ch-ch-ch-: the first sixteenth of a word fired n times, then the word. With Lem: the start of her "charging"
    (on CHAR_AT) in the same bar."""
    if LEM:
        lead = .12            # her "ch" starts about .17 s before the note
        _after.append(lambda: [S.put("vox", S.at(bar) + sw(k + j) - lead,
                                     fade(lem_cut(S.at(bar, CHAR_AT) - lead, S.at(bar, CHAR_AT) + .45 * STEP)), .5,
                                     amp * (.7 + .1 * j), wet=.15, echo=.1) for j in range(n)])
        return
    li, y = sung(word, [(m, STEP * 2)], SINGER)
    piece = y[:int((li + STEP * .45) * e.SR)].copy()
    piece[-200:] *= np.linspace(1, 0, 200)
    for j in range(n):
        S.put("vox", S.at(bar) + sw(k + j) - li, piece, .5, amp * (.7 + .1 * j), wet=.15, echo=.1)


def fade(y, ms=5):
    """A short fade at both ends (a sampler's click guard)."""
    y = np.array(y, float)
    k = min(int(ms / 1000 * e.SR), len(y) // 2)
    if k:
        y[:k] *= np.linspace(0, 1, k)
        y[-k:] *= np.linspace(1, 0, k)
    return y


def reverse_chop(bar, word, m, amp=1.0, src=None):
    """A word sung, reversed, swelling into the downbeat of bar. With Lem: the word cut from her take, src =
    (from, to) in seconds."""
    if LEM:
        def rev():
            y = fade(lem_cut(*src))[::-1]
            y = y * np.linspace(0, 1, len(y)) ** 2
            S.put("vox", S.at(bar) - len(y) / e.SR, y, .5, amp, wet=.5, echo=.2)
        _after.append(rev)
        return
    li, y = sung(word, [(m, B * 2)], SINGER)
    y = y[::-1] * np.linspace(0, 1, len(y)) ** 2
    S.put("vox", S.at(bar) - len(y) / e.SR, y, .5, amp, wet=.5, echo=.2)


# the hook, a phrase a bar, a four-bar cycle. Spelled the way the singer should say it, a syllable a note
HOOK_LOW = [
    (". . A4 - - . C5 - A4 - . . A4 . A4 .", "low bat tree low low"),
    (". . D5 - . C5 - - A4 - - - . . . .", "ten per cent"),
    (". . . . . . F5 - D5 - - - . . . .", "char jing"),          # the "ch-ch-ch" is a stutter, steps 0-2
    (". . C5 - - - A4 - - - - - . . . .", "sleep mode"),
]
HOOK_FULL = [
    (". . A4 - - . C5 - D5 - - . . . . .", "full lee charged"),
    (". . D5 - C5 - A4 - - . C5 - A4 - - .", "a hun dred per cent"),
    (". . . . . . F5 - D5 - - - . . . .", "char jing"),
    (". . C5 - - - A4 - D5 - - - . . . .", "wide a wake"),
]
LEVEL = {"ten": (". . D5 - . C5 - - A4 - - - . . . .", "ten per cent"),
         "five": (". . C5 - . A4 - - G4 - - - . . . .", "five per cent"),
         "one": (". . A4 - . G4 - - F4 - - - - - . .", "one per cent")}


def hook(bar, full=False, amp=1.0):
    i = bar % 4
    line, words = (HOOK_FULL if full else HOOK_LOW)[i]
    if i == 2:
        stutter(bar, 0, "char", 74, 3, amp * .9)
    vocal(bar, line, words, amp)


# ---------------------------------------------------------------- the laptop
BEEPS = [(10, 81, .5), (11, 81, .5), (13, 74, 2.5)]     # beep beep booop: the battery, low, landing on the root


def beeps(bar, amp=1.0):
    for k, m, n in BEEPS:
        S.put("lead", S.at(bar) + sw(k), beep(m, n * STEP * .6), .58, .2 * amp, wet=.2, echo=.4)


def chime(bar, up=True, amp=1.0):
    """The charger: plugged in (up) or the power going away (down). D minor, of course."""
    notes = [62, 65, 69, 74] if up else [74, 69, 65, 62]
    for j, m in enumerate(notes):
        S.put("lead", S.at(bar, 2) + j * STEP, beep(m, STEP * (3 if j == 3 else .8)), .5, .22 * amp, wet=.35,
              echo=.35)


# Brahms' Lullaby, the first two lines, squared into 4/4 for the beep to play
LULLABY = [
    "A4 - A4 C5 - - - . A4 - A4 C5 - - - .",
    "A4 - C5 - F5 - - - E5 - - D5 D5 - C5 -",
    "G4 - A4 Bb4 - - - . G4 - A4 Bb4 - - - .",
    "G4 - Bb4 - E5 - D5 C5 - - E5 - F5 - - -",
]


def lullaby(bar, amp=1.0, octave=12):
    for t, m, d in S.notes(bar, LULLABY[bar % 4]):
        S.put("lead", t, beep(m + octave, d * .8), .45, .22 * amp, wet=.45, echo=.4)
        S.put("lead", t, nightlight(m, d * .9, .5), .55, .3 * amp, wet=.4)


def system(bar, text, seconds, beat=0.0, amp=1.0):
    """The laptop's voice, deadpan, through its own little speaker."""
    y = speaker(V.rap(text, seconds, voice=SYSTEM, pitch=1.0, level=.16))
    S.put("vox", S.at(bar, beat), y, .5, amp, wet=.15, echo=.15)


MELODY = [
    "E5 - - D5 F5 - E5 - . . A4 - C5 - D5 -", "D5 - - - - - . . F5 - - E5 D5 - C5 -",
    "D5 - - C5 Bb4 - A4 - . . G4 - Bb4 - D5 -", "C5 - - - - - . . E5 - - - . . . .",
]


def melody(bar, amp=1.0):
    """The soft DX7 on top, an octave over the chops."""
    for t, m, d in S.notes(bar, MELODY[bar % 4]):
        S.put("lead", t, nightlight(m + 12, d, .75), .55, .22 * amp, wet=.35, echo=.3)
        S.put("lead", t, rhodes(m, d, .5), .45, .1 * amp, wet=.3)


# ---------------------------------------------------------------- the arrangement
for bar in range(120):
    intro, outro = bar < 16, bar >= 104
    brk = is_break(bar)
    groove = 48 <= bar < 64 or 72 <= bar < 88
    if intro:
        drums(bar, clap=bar >= 8, shaker=bar >= 8, rimshots=bar >= 12, crash=bar == 0)
    elif outro:
        drums(bar, clap=bar < 112, shaker=bar < 116, rimshots=bar < 112, crash=bar == 104)
    elif brk:
        drums(bar, kick=False, clap=bar >= 68, hats=bar >= 66, shaker=True, rimshots=bar >= 68, amp=.7)
    else:
        drums(bar, shaker=True, rimshots=True, congas=groove, crash=bar in (32, 48, 72, 88))

    if 16 <= bar < 104 and not brk:
        bass(bar, .6 if bar < 20 else 1.0)
    if 24 <= bar < 32:
        rhodes_comp(bar, .8, cut=800 + (bar - 24) * 300)
    if 32 <= bar < 102:
        rhodes_comp(bar, .8 if brk else 1.0, cut=1400 if brk else None)
    if 32 <= bar < 96:
        pads(bar, 1.3 if brk else (.6 if bar >= 88 else 1.0), cut=1100 if brk else 1500)
    if 48 <= bar < 88 and (brk or bar % 2 == 0) and not LEM:      # the Piper "ooh" choir: not with singer D
        oohs(bar, 1.3 if brk else 1.0)
    if groove and bar < 88:
        organ_stabs(bar, .8 if bar < 64 else 1.0)
    if 72 <= bar < 88:
        organ_hold(bar)
    if 56 <= bar < 64 or 76 <= bar < 88:
        melody(bar)
    if brk:
        lullaby(bar)

    # the chops
    if 32 <= bar < 48 and bar % 4 == 1:
        vocal(bar, *HOOK_LOW[0], amp=.85, echo=.4)
    if bar == 43:
        vocal(bar, *HOOK_LOW[1], amp=.8, echo=.4)
    if 48 <= bar < 64:
        hook(bar)
    if 72 <= bar < 88:
        hook(bar, full=True)
    if brk and bar % 4 == 3:
        vocal(bar, *HOOK_LOW[3], amp=.9, echo=.5, cut=2500)
    for b, lvl in ((88, "ten"), (92, "five"), (96, "one")):
        if bar == b:
            vocal(bar, *LEVEL[lvl], amp=.9, echo=.4)
        if bar == b + 2:
            vocal(bar, *HOOK_LOW[0], amp=.8, echo=.4)

    # the battery
    if (28 <= bar < 64 or 72 <= bar < 100) and bar % 4 == 3 and not 76 <= bar < 88:
        beeps(bar, .8 if bar < 32 else 1.0)

system(26, "Battery low.", 1.2, amp=.9)
system(40, "Ten percent remaining.", 1.8, beat=2)
system(64, "Entering sleep mode.", 1.8, beat=1)
system(66, "Please connect charger.", 2.0, beat=1)
system(70, "Charging.", 1.0, beat=0)
system(71, "Battery fully charged.", 1.8, beat=0)
system(98, "Shutting down.", 1.3, beat=0)
system(100, "Good night.", 1.2, beat=0)
# with Lem the reversed words are hers: "sleep" from bar 67's "sleep mode", "charged" from bar 72's "fully charged"
reverse_chop(64, "sleep", 69, .8, src=(S.at(67, .5) - .1, S.at(67, 1.5) + .1))
reverse_chop(72, "charged", 74, .8, src=(S.at(72, 2) - .12, S.at(72, 2.75) + .25))
chime(70, up=True)
chime(99, up=False)

# the power goes: the last chord, a whole bar of it, slowing down to nothing over bars 102-103
last = sum(rhodes(m, S.bar * 1.5, .7) for m in KEYS["Dm9"])
S.put("keys", S.at(102), tape_stop(last, S.bar * 1.6), .5, .45, wet=.3)
S.put("pads", S.at(102), tape_stop(e.pad(e.voicing("Dm9", lo=50), S.bar * 1.5, cut=1500).mean(1), S.bar * 1.6),
      .5, .3, wet=.4)

# the dust on the record, all the way through
S.put("fx", 0, e.crackle(S.length), .5, 1.0, wet=0)
S.put("fx", S.at(69), e.riser(S.bar * 3, .2), .5, wet=.3)
S.put("fx", S.at(64), e.downlifter(S.bar * 2, .18), .5, wet=.3)

if LEM:
    _render = P.ds_part.render

    def _keep(**kw):          # Band.finish renders the lead take first: keep it for the sampler tricks
        if "DS_BREATH" not in os.environ:
            kw["breaths"] = BREATHS
        y = _render(**kw)
        _lem.setdefault("y", y)
        return y
    P.ds_part.render = _keep
    P.finish()                # singer D's one take into the mix, each line at its level, the echo on the last word
    for f in _after:
        f()

# sleep mode: the lights go low in the break, and come back up while it charges
cut = [(0, 18000), (S.at(64), 18000), (S.at(64) + .05, 1500), (S.at(69), 1500), (S.at(72) - .02, 9000),
       (S.at(72), 18000), (S.n / e.SR, 18000)]
here = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "renders", "low-battery_120bpm_Dm.wav")
os.makedirs(os.path.dirname(out), exist_ok=True)
S.mixdown(out, {"drums": .85, "perc": .7, "bass": .9, "pads": 1.0, "keys": 1.1, "lead": 1.1, "vox": 1.45, "fx": .5},
          cut_keys=cut, room=.2, echo_mix=.45, lufs=-10.0,
          ir=room.impulse_response((4.5, 3.6, 2.6), rt60=1.2))
