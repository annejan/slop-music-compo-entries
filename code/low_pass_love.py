#!/usr/bin/env python3
"""Low Pass Love: 90's mellow house (French touch), 122 BPM, A minor. Saturday's theme of the AI slop music compo.

low_pass_love.py [OUT.wav]   (default renders/low-pass-love_122bpm_Am.wav)
SINGER=en_US-hfc_male-medium: the old disco man (Piper, re-pitched, with his choir), for an A/B

Every note and every sound here is written by Claude, in this file: no samples, no loops. Paris, 1998, in a
bedroom studio: a "disco loop" that was never on a record (strings, a funk guitar, a bass guitar, a Rhodes and the
dust of a vinyl that never existed), played through one resonant low-pass filter that opens and closes, a phaser,
and a sidechain that pumps it to the kick. Over it a talk box sings the hook. The joke is the filter itself: it
does what the words say. "You cut me off at eighty hertz" cuts the loop off at eighty hertz; "put the treble in
its place" puts it back. The first and last 16 bars are drums only, for the DJ.

  bars   0-15  intro: kick and hats, then clap and shaker (drums only)
        16-23  the disco loop arrives, filter closed (only the bass and the thump get through)
        24-31  the filter slowly opens; a riser
        32-47  hook (talk box): "low pass love / open up the filter / low pass love / let the highs come through";
               the filter opens all the way on "the highs"
        48-55  the full loop, pumping; a Rhodes melody and the funk guitar lick; a slow filter dip
        56-63  verse (the singer, alone): the filter follows the words
        64-71  hook (talk box)
        72-79  break: no kick; "close it, close it" (it closes, only the bass is left), "open it up" (it opens)
        80-95  hook twice: the talk box, the singer an octave under it
        96-111 the loop winds down, the filter closing slowly; the talk box says goodbye
       112-127 outro: drums only

The talk box: a synth (two saws and a pulse, with glide) whose spectrum is shaped, 5 ms at a time, by the spectral
envelope WORLD finds in a Piper voice speaking each word (voice.tts and voice.analyse): the synth "speaks" through
someone else's mouth. The funk guitar is a Karplus-Strong string, the bass guitar is additive, the Rhodes is the
DX7 E.Piano (dx7.py) and the reverb is a simulated room (room.py).

The singer ("singer D", 21 November): Lem the Shapeshifter DS 2.5 (DiffSinger) sings the written notes and words,
SoulX-Singer SVC turns him into a warm Qwen baritone (parts.Band with diva_voice="ds:lem"). One voice, no doubles,
no harmony, no vocoder: 90's mellow house is sparse. Shape it fast with Lem alone:
DS_TIMBRE= SOLO=vox PREVIEW=56-64 .venv/bin/python low_pass_love.py
"""
import functools
import math
import os
import sys

import numpy as np
from scipy import signal
from scipy.ndimage import uniform_filter1d

import engine as e
import dx7
import parts
import room
import voice as V

SR = e.SR
e.seed(122)
BARS = 128
S = e.Song(bpm=122, bars=BARS)
STEP = S.step
B = S.beat
SWING = .06 * STEP          # French house is nearly straight: a hint of shuffle

PROG = ["Am9", "D9", "Fmaj9", "E7"]

MOUTH = os.environ.get("MOUTH", "en_US-ryan-high")           # whose speech shapes the talk box
SINGER = os.environ.get("SINGER", "ds:lem")                  # singer D; en_US-hfc_male-medium: the old disco man
BACKING = ["en_US-joe-medium", "en_GB-alan-medium", "en_US-john-medium"]   # left, right, the third above (Piper only)
FALSETTO = "en_US-bryce-medium"                              # an octave up, very Saturday night (Piper only)
PIPER = not SINGER.startswith("ds:")
# singer D: a male voice for a male line (verse A3-E4, hook E3-C4). The baritone crooner, not the tenor: the lines
# sit low (a baritone's middle), and "velvety" fits a late-night French-house vocal better than a "eurodance lead".
TIMBRE = "sing_qwen_baritone"
ACCENT = {"love": 2}
P = None if PIPER else parts.Band(S, PROG, diva_voice=SINGER, timbre=TIMBRE, stack="", harmony="", accent=ACCENT,
                                  verse_double=0.0)
if P:
    P.ds_gain = 1.3                                          # his level (DS_GAIN overrides it): the vox bus 1-2 dB over
                                                             # the old disco man with his choir


def chord_of(bar):
    return PROG[bar % 4]


def sw(k):
    """The time of sixteenth k in a bar, a little swung."""
    return k * STEP + (SWING if k % 2 else 0)


# ---------------------------------------------------------------- the loop's own tape
# The disco loop is mixed onto its own tape first (bass, strings, guitar and Rhodes), and only at the end goes
# through the filter, the phaser and the pump, like a sample through a DJ's filter box.
LOOP = {k: np.zeros((S.n, 2), np.float32) for k in ("bass", "pads", "keys")}


def lput(stem, t, g, pan=.5, amp=1.0):
    i = int(round(t * SR))
    if i >= S.n or len(g) == 0:
        return
    j = min(i + len(g), S.n)
    seg = np.asarray(g[:j - i]) * amp
    if seg.ndim == 1:
        seg = np.stack([seg * math.cos(pan * math.pi / 2), seg * math.sin(pan * math.pi / 2)], axis=1)
    LOOP[stem][i:j] += seg


# ---------------------------------------------------------------- instruments
@functools.lru_cache(maxsize=None)
def bass_guitar(m, d, vel=1.0, mute=False):
    """A fingered bass guitar: harmonics that die faster the higher they are, a little stiffness, a thump of the
    finger, a soft valve. A muted note is mostly thump."""
    f = float(e.hz(m))
    t = e.tt(d + .08)
    g = np.zeros_like(t)
    for n in range(1, 16):
        fn = f * n * math.sqrt(1 + .00015 * n * n)
        if fn > 4000:
            break
        a = abs(math.sin(math.pi * n * .22)) / n ** 1.1 * vel ** (.3 + .08 * n)   # plucked a fifth along the string
        g += a * np.sin(2 * np.pi * fn * t + n * .7) * np.exp(-t * (1.0 + .8 * n + (25 if mute else 0)))
    thump = e.lowpass(e.rng.standard_normal(len(t)), 700) * np.exp(-t * 90) * (.9 if mute else .35)
    g = np.tanh(1.6 * (g * .8 + thump)) / 1.2
    return g * e.rise(t, .003) * e.gate(t, d, .03) * vel


@functools.lru_cache(maxsize=None)
def string_pluck(m, d, vel=.8, damp=.996, bright=4000.0):
    """A Karplus-Strong guitar string: a burst of noise round a tuned loop (an averaging low-pass and an all-pass
    for the fraction of a sample), as one IIR filter. damp: how much of the sound survives one trip."""
    f = float(e.hz(m))
    N = SR / f
    Ni = int(N - .5)
    frac = N - .5 - Ni
    c = (1 - frac) / (1 + frac)
    n = int((d + .2) * SR)
    x = np.zeros(n)
    burst = e.lowpass(e.rng.standard_normal(Ni), bright * (.5 + vel))
    x[:Ni] = burst
    k = max(int(Ni * .16), 1)                    # picked near the bridge: a comb on the burst
    x[k:] -= .7 * x[:-k].copy()
    a = np.zeros(Ni + 3)
    a[0], a[1] = 1.0, c
    a[Ni:Ni + 3] -= damp * .5 * np.array([c, 1 + c, 1])
    y = signal.lfilter([1.0, c], a, x)
    t = e.tt(n / SR)
    y = e.bandpass(y, 180, 5000)                 # a single-coil pickup through a small amp
    return y * e.gate(t, d, .025) * vel * .6


def strum(m_list, d, vel, mute, up=False):
    """A chord, string after string (a down stroke low to high, an up stroke high to low)."""
    order = list(reversed(m_list)) if up else list(m_list)
    out = np.zeros(int((d + .25) * SR))
    for j, m in enumerate(order):
        g = string_pluck(m, d, vel * (1 - .06 * j), damp=.93 if mute else .992, bright=2500.0 if mute else 4500.0)
        i = int(j * .006 * SR)
        out[i:i + len(g)] += g[:len(out) - i]
    return out


def strings(notes, d, a=.18, r=.45, cut=3800):
    """Disco strings: a detuned ensemble with the edges off (the phaser comes later)."""
    return e.supersaw(notes, d, spread=.14, voices=6, a=a, r=r, cut=cut)


def swoop(m, d):
    """The disco strings' glissando: an octave up into the downbeat."""
    t = e.tt(d + .3)
    u = np.clip(t / d, 0, 1)
    pitch = m - 12 + 12 * u ** 1.6
    out = np.zeros((len(t), 2))
    for v in range(6):
        out[:, v % 2] += e.saw(e.hz(pitch + (v / 5 - .5) * .25), t)
    out = e.lowpass(out, 3500) / 6
    return out * ((u ** 1.5) * e.gate(t, d, .12))[:, None]


def rhodes(m, d, vel):
    return dx7.note("epiano", m, d, vel, tail=.9)


# ---------------------------------------------------------------- the talk box
def _frames(arr, idx):
    i0 = np.clip(np.floor(idx).astype(int), 0, len(arr) - 1)
    i1 = np.clip(i0 + 1, 0, len(arr) - 1)
    w = (idx - i0)[:, None]
    return arr[i0] * (1 - w) + arr[i1] * w


TB_N, TB_HOP = 1024, 220


@functools.lru_cache(maxsize=None)
def talkbox(text, notes, mouth=MOUTH, take=0, level=.12):
    """A talk box singing one word on notes ((midi, seconds), ...): a synth through the mouth of a Piper voice.

    The word's frames are stretched like voice.sing does (the consonants keep their length, the vowel fills the
    notes). Then, every 5 ms, the synth's spectrum is flattened and given the shape of the speech's spectral
    envelope (WORLD's CheapTrick); where the speech is noise (an s, a t), white noise is shaped instead.
    Returns (lead_in seconds, mono audio)."""
    x = V.tts(text, mouth, take=take)
    f0, sp, ap, energy = V.analyse(x)
    n = len(f0)
    voiced = f0 > 0
    if voiced.any():
        loud = voiced & (energy > .4 * energy[voiced].max())
        idx = np.nonzero(loud)[0]
        a0, b0 = idx[0], idx[-1] + 1
    else:
        a0, b0 = n // 3, 2 * n // 3
    total = sum(d for _, d in notes)
    pre, post = a0, n - b0
    want = int(round(total / V.FS))
    room_ = want - post
    if room_ < max(b0 - a0, 1) * .5:
        k = want / max(n, 1)
        pre, post = int(pre * k), int(post * k)
        room_ = max(want - post, 1)
    src = np.concatenate([np.linspace(0, a0, pre, endpoint=False), np.linspace(a0, b0, max(room_, 1), endpoint=False),
                          np.linspace(b0, n - 1, max(post, 1))])
    sp2, ap2 = _frames(sp, src), _frames(ap, src)
    vo = _frames(voiced[:, None].astype(float), src)[:, 0]
    L = int(len(src) * V.FS * SR)
    t = np.arange(L) / SR
    # the synth: our notes from the vowel on, a glide between them, a slow vibrato on long notes
    tau = np.maximum(t - pre * V.FS, 0)
    ends = np.cumsum([d for _, d in notes])
    j = np.clip(np.searchsorted(ends, tau, side="right"), 0, len(notes) - 1)
    tgt = np.array([m for m, _ in notes], float)[j]
    al = 1 - math.exp(-1 / (.045 * SR))
    sm = signal.lfilter([al], [1, al - 1], tgt - tgt[0], zi=[0.0])[0] + tgt[0]
    since = tau - np.concatenate([[0], ends[:-1]])[j]
    sm = sm + .12 * np.sin(2 * np.pi * 5.0 * tau) * np.clip((since - .3) / .3, 0, 1)
    f = e.hz(sm)
    carrier = e.saw(f, t) + .7 * e.saw(f * 2 ** (6 / 1200), t) + .5 * e.pulse(f * .5, t, .35)
    noise = e.rng.standard_normal(L)
    kw = dict(fs=SR, window="hann", nperseg=TB_N, noverlap=TB_N - TB_HOP)
    _, ft, C = signal.stft(carrier, **kw)
    _, _, Nz = signal.stft(noise, **kw)
    # WORLD's envelope at each STFT frame; its bins are 22050/1024 Hz apart, ours 44100/1024: every other one
    wf = np.clip(ft / V.FS, 0, len(src) - 1)
    env = _frames(sp2, wf)[:, ::2]
    aper = _frames(ap2, wf)[:, ::2]
    voi = np.interp(wf, np.arange(len(vo)), vo)[:, None]
    bins = C.shape[0]
    E = np.zeros((len(ft), bins))
    A = np.ones((len(ft), bins))
    k = min(env.shape[1], bins)
    E[:, :k], A[:, :k] = np.sqrt(env[:, :k]), aper[:, :k]
    # in the vowels, a talk box is all synth; in the consonants it hisses
    mixn = np.clip(A * (1 - .8 * voi), 0, 1)
    flatC = uniform_filter1d(np.abs(C), 9, axis=0) + 1e-9
    flatN = uniform_filter1d(np.abs(Nz), 9, axis=0) + 1e-9
    Y = (C / flatC * (1 - mixn.T) + Nz / flatN * mixn.T * .6) * E.T
    _, y = signal.istft(Y, **kw)
    y = y[:L]
    y = e.lowpass(e.highpass(y, 110), 6500)      # the plastic tube and the mouth: no deep lows, no air
    body = y[int(pre * V.FS * SR):] if pre else y
    y = y * (level / (np.sqrt(np.mean(body ** 2)) + 1e-9))
    q = int(.004 * SR)
    y[:q] *= np.linspace(0, 1, q)
    y[-q:] *= np.linspace(1, 0, q)
    return pre * V.FS, y


@functools.lru_cache(maxsize=None)
def sung(text, notes, voice, cents=0.0, take=0, formant=1.0, vowel_only=False):
    """vowel_only: for the voices behind the singer (only the vowels, less vibrato), so his consonants stay clean."""
    return V.sing(text, list(notes), voice=voice, cents=cents, take=take, formant=formant, vowel_only=vowel_only,
                  vibrato=.15 if vowel_only else .35)


def words_on(notes, words):
    """Pair words with notes: a word takes its note and one more for each "+" after it (sung as one word)."""
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


# ---------------------------------------------------------------- the words and their tunes (eighths, two bars)
HOOK = [
    (". E4 - G4 - A4 - - - - - - . . . .", "low pass love"),
    (". A4 G4 - E4 - D4 - E4 - - - D4 - - .", "oh pen up the fill tur"),
    (". E4 - G4 - A4 - - - - - - . . . .", "low pass love"),
    (". A4 G4 - C5 - - - B4 - A4 - G#4 - - .", "let the highs come through +"),
]
VERSE = [
    (". A3 C4 C4 C4 B3 C4 D4 E4 - - . . . . .", "you cut me off at eigh tee hurts"),
    (". E4 - E4 D4 - C4 - D4 - - A2 - - - .", "now all I hear is bass"),
    (". C4 C4 D4 - E4 D4 C4 D4 - E4 - - - . .", "turn the knob a lit tull bay bee"),
    (". E4 E4 A4 - G4 - E4 D4 - E4 - - - - -", "put the treb bull in its place"),
]
CLOSE = (". E4 - D4 - . . . E4 - D4 - . . . .", "close it close it")
OPEN = (". A4 - G4 - C5 - - - - - - . . . .", "oh pen up")
# the words as DiffSinger reads them (real English; "+" holds a word over the next note), where Piper's spelling
# differs. "bass" is "base" for him: the dictionary may read the fish.
DS_WORDS = {
    "oh pen up the fill tur": "open + up the filter +",
    "you cut me off at eigh tee hurts": "you cut me off at eighty + hurts",
    "now all I hear is bass": "now all I hear is base",
    "turn the knob a lit tull bay bee": "turn the knob a little + baby +",
    "put the treb bull in its place": "put the treble + in its place",
    "oh pen up": "open + up",
}
# singer D's own rhythm where the written one slurs (Whisper, 21 November), changed as little as it takes:
# - "at eighty hertz" in even eighths came out "a lady head" (Lem alone): the line starts on the downbeat, "eigh"
#   gets a quarter and "hertz" stays on the bar line (spelled "hurts": 2 of 2 takes "at 80 hertz"). The SVC
#   conversion then blurred the fast stops ("cut me off at": "can be your fatty", in every timbre), so in sixteenths
#   "cut" and "off" are an eighth with a sixteenth rest after them (baritone: "you get me off at 80 hertz");
# - "knob" lets go a sixteenth before "a little" ("on it all" before; now "turn the knob a little baby");
# - "treble" with "-ble" an eighth ("chair button" before);
# - "open" with "o" a quarter on the downbeat, not an eighth pickup ("help un-up");
# - in the break, "up" short, not held (held: "how about that?").
DS_LINES = {
    "you cut me off at eigh tee hurts": "A3 - C4 - . C4 C4 - . B3 C4 - - D4 - - E4 - - - - - - - . . . . . . . .",
    "turn the knob a lit tull bay bee": ". . C4 - C4 - D4 - - . E4 - D4 - C4 - D4 - - - E4 - - - - - - - . . . .",
    "put the treb bull in its place": ". E4 E4 A4 - - G4 E4 D4 - E4 - - - - -",
    "oh pen up the fill tur": "A4 - G4 - E4 - D4 - E4 - - - D4 - - .",
    "oh pen up": ". A4 - G4 - C5 - . . . . . . . . .",
}


def talk(bar, line, words, octave=-12, amp=1.0, pan=.5, echo=.08):
    for w, ns in words_on(S.notes(bar, line, bars=2), words):
        li, y = talkbox(w, tuple((m + octave, round(d * .96, 4)) for _, m, d in ns))
        S.put("lead", ns[0][0] - li, y, pan, amp, wet=.18, echo=echo)


def third_above(m):
    """Two steps up A minor (natural): a diatonic third."""
    scale = {9, 11, 0, 2, 4, 5, 7}
    for up in (3, 4):
        if (m + up) % 12 in scale:
            return m + up
    return m + 3


def disco(bar, line, words, octave=0, amp=1.0, choir=0.0, falsetto=0.0):
    """The singer sings a line, `octave` semitones from the written notes. Singer D (the default): Lem, alone, into
    his one take (choir and falsetto ignored: sparse). The old disco man (SINGER=<a Piper voice>): choir > 0 adds two
    other men (left and right) and a third man a third above; falsetto > 0 adds one more an octave up, in the
    middle, at the back."""
    if P:      # parts.Band sings octave + 12 above its notes: -12 is the written pitch
        P.diva(bar, DS_LINES.get(words, line), words, bars=2, octave=octave - 12, amp=amp,
               ds_words=DS_WORDS.get(words))
        return
    for w, ns in words_on(S.notes(bar, line, bars=2), words):
        t = ns[0][0]
        notes = tuple((m + octave, round(d * .96, 4)) for _, m, d in ns)
        li, y = sung(w, notes, SINGER)
        S.put("vox", t - li, y, .5, amp, wet=.15, echo=.08)
        if choir:
            third = tuple((third_above(m), d) for m, d in notes)
            for voice, ns2, cents, late, pan, g in ((BACKING[0], notes, 7, .014, .2, .75),
                                                    (BACKING[1], notes, -7, .008, .8, .75),
                                                    (BACKING[2], third, 0, .005, .45, .55)):
                _, y2 = sung(w, ns2, voice, cents=cents, vowel_only=True)
                S.put("vox", t + late, y2, pan, amp * choir * g, wet=.2, echo=.05)
        if falsetto:
            _, y2 = sung(w, tuple((m + 12, d) for m, d in notes), FALSETTO, formant=1.05, vowel_only=True)
            S.put("vox", t + .01, y2, .55, amp * falsetto, wet=.3, echo=.1)


# ---------------------------------------------------------------- drums
def drums(bar, kick=True, clap=True, hats=True, open_hats=True, shaker=False, crash=False, amp=1.0):
    t0 = S.at(bar)
    if kick:
        for b in range(4):
            S.kick(t0 + b * B, .95 * amp, punch=95, base=47, length=.42, click=.2)
    if clap:
        for b in (1, 3):
            S.put("drums", t0 + b * B, e.clap(.5 * amp), .5, wet=.22)
            S.put("drums", t0 + b * B, e.snare(.2 * amp), .5, wet=.2)
    if hats:
        for k in range(16):
            if k % 4 == 2:
                if open_hats:
                    S.put("perc", t0 + sw(k), e.hat(.45 * amp, opened=True), .58, wet=.08)
            else:
                a = (.2 if k % 2 else .28) * amp * (1 + .12 * np.sin(1.7 * bar + k))
                S.put("perc", t0 + sw(k), e.hat(a), .64, wet=.04)
    if shaker:
        for k in range(16):
            S.put("perc", t0 + sw(k), e.shaker((.3 if k % 2 else .18) * amp), .36, wet=.06)
    if crash:
        S.put("perc", t0, e.crash(.45), .5, wet=.3)


# ---------------------------------------------------------------- the disco loop, bar by bar (onto its tape)
def seventh(name):
    iv = e.chord(name)[1]
    return 10 if 10 in iv else 7


def bass(bar, amp=1.0):
    """Octave-jumping disco bass, a ghost note or two, and a walk into the next chord."""
    c, nxt = chord_of(bar), chord_of(bar + 1)
    root = e.root_note(c, lo=33)
    r2 = e.root_note(nxt, lo=33)
    s = seventh(c)
    line = [(0, 0, 2, 1.0), (2, 12, 1, .8), (3, None, 1, .5), (4, 0, 1, .75), (6, 12, 1, .85), (7, s, 1, .6),
            (8, 0, 2, .95), (10, 12, 1, .8), (11, None, 1, .45), (12, 7, 1, .7), (13, 12, 1, .65),
            (14, s, 1, .75), (15, r2 - root - 1 + (12 if r2 - root - 1 < -5 else 0), 1, .7)]
    for k, iv, n, vel in line:
        mute = iv is None
        g = bass_guitar(root + (0 if mute else iv), round(n * STEP * .85, 4), vel, mute)
        lput("bass", S.at(bar) + sw(k), g, .5, .55 * amp)


CHOP = "X.xxX.xX.xX.xXx."     # the funk guitar: X a ringing chord, x a muted scratch


def guitar(bar, amp=1.0):
    notes = e.close_voicing(chord_of(bar), lo=57, hi=72)[:4]
    for k, ch in enumerate(CHOP):
        if ch == ".":
            continue
        if ch == "X":
            g = strum(notes, STEP * 1.1, .8, False, up=k % 2 == 1)
            lput("keys", S.at(bar) + sw(k), g, .3, .5 * amp)
        else:
            g = strum(notes, .045, .45, True, up=k % 2 == 1)
            lput("keys", S.at(bar) + sw(k), g, .3, .4 * amp)


LICK = ["A4 . C5 . D5 . E5 G5 . E5 . D5 C5 . A4 .", "A4 . C5 . D5 . F#5 . E5 . D5 - C5 . D5 ."]


def lick(bar, amp=1.0):
    """The guitar's single-note lick, the hook of the loop."""
    for t, m, d in S.notes(bar, LICK[bar % 2]):
        lput("keys", t, string_pluck(m, round(d * .9, 4), .85, .995, 3500.0), .7, .42 * amp)


def strings_bar(bar, amp=1.0):
    notes = e.close_voicing(chord_of(bar), lo=60, hi=76)
    lput("pads", S.at(bar), strings(notes, S.bar * .98), .5, .33 * amp)
    if bar % 8 == 7:
        top = e.close_voicing(chord_of(bar + 1), lo=64, hi=76)[-1]
        lput("pads", S.at(bar, 2), swoop(top, B * 2), .5, .25 * amp)


RHODES_COMP = [(0, 7, .62), (10, 5, .5)]


def rhodes_comp(bar, amp=1.0):
    for k, n, vel in RHODES_COMP:
        for j, m in enumerate(e.voicing(chord_of(bar), lo=55, drop_root=True)):
            lput("keys", S.at(bar) + sw(k) + j * .005, rhodes(m, n * STEP, vel), .65, .3 * amp)


MELODY = [
    "E5 - - D5 E5 - G5 - E5 - D5 - C5 - A4 -", "C5 - - A4 - - G4 - A4 - - - . . . .",
    "F5 - - E5 D5 - C5 - D5 - E5 - C5 - A4 -", "B4 - - G#4 - - E4 - G#4 - B4 - D5 - E5 -",
]


def melody(bar, amp=1.0):
    """A Rhodes tune over the loop (not part of it: it stays out of the filter); the octave under it, softly."""
    for t, m, d in S.notes(bar, MELODY[bar % 4]):
        S.put("keys", t, rhodes(m, d, .7), .55, .3 * amp, wet=.3, echo=.25)
        S.put("keys", t, rhodes(m - 12, d, .5), .45, .16 * amp, wet=.25)


# ---------------------------------------------------------------- the arrangement
HOOK_BARS = (32, 40, 64, 80, 88)
for bar in range(BARS):
    intro, outro = bar < 16, bar >= 112
    brk = 72 <= bar < 80
    loop = 16 <= bar < 112
    if intro:
        drums(bar, clap=bar >= 4, open_hats=bar >= 8, shaker=bar >= 8, crash=bar == 0)
    elif outro:
        drums(bar, clap=bar < 124, open_hats=bar < 120, shaker=bar < 116, crash=bar == 112)
    elif brk:
        drums(bar, kick=False, clap=bar >= 78, hats=bar >= 74, open_hats=False, shaker=True, amp=.75)
    else:
        drums(bar, shaker=True, crash=bar in (32, 48, 64, 80))

    if loop:
        bass(bar, .85 if 72 <= bar < 76 else 1.0)
        if not (74 <= bar < 76):
            strings_bar(bar)
            guitar(bar)
            rhodes_comp(bar)
        if 48 <= bar < 56 or 88 <= bar < 104:
            lick(bar)
    if 48 <= bar < 56:
        melody(bar)

    # the voices
    if any(h <= bar < h + 8 for h in HOOK_BARS) and bar % 2 == 0:
        h = max(x for x in HOOK_BARS if x <= bar)
        line, words = HOOK[(bar - h) // 2]
        big = bar >= 80
        talk(bar, line, words, amp=1.0)
        if big:
            disco(bar, line, words, octave=-12, amp=.55 if PIPER else .8, choir=.43, falsetto=.3 if bar >= 88 else 0)
    if 56 <= bar < 64 and bar % 2 == 0:
        disco(bar, *VERSE[(bar - 56) // 2], choir=.25 if bar >= 60 else 0)
    if bar == 72:
        talk(bar, *CLOSE, amp=.9)
    if bar == 76:
        disco(bar, *OPEN, octave=-12, choir=.43)
    if bar in (100, 104):
        talk(bar, *HOOK[0], amp=.8, echo=.3)

if P:
    P.finish()   # singer D's one take into the vox bus, each line at its own level

# the dust of the record goes in the loop: it is filtered with the rest
dust = e.crackle(S.at(112) - S.at(16), .6)
lput("pads", S.at(16), dust, .5, 1.0)

# a spoken aside, while the filter opens in the break
aside = V.rap("From twenty hertz to twenty K.", B * 3, voice="en_US-norman-medium", pitch=.95, level=.1)
S.put("vox", S.at(78, 1), aside, .5, .8, wet=.25, echo=.3)

S.put("fx", S.at(30), e.riser(S.bar * 2, .22), .5, wet=.3)
S.put("fx", S.at(78), e.riser(S.bar * 2, .25), .5, wet=.3)
S.put("fx", S.at(72), e.downlifter(S.bar * 2, .2), .5, wet=.3)
S.put("fx", S.at(111), e.downlifter(S.bar * 1, .15), .5, wet=.3)


# ---------------------------------------------------------------- the filter box: low-pass, phaser, pump
def curve(keys):
    """A cutoff per sample from (bar, Hz) keys, moving in octaves (log) between them."""
    ks, vs = zip(*[(S.at(b), v) for b, v in keys])
    return np.exp(np.interp(np.arange(S.n) / SR, ks, np.log(vs)))


V0 = 1 / 16       # a sixteenth of a bar, for keys a hair before a bar line
CUT = [(0, 200), (16, 200), (24, 380),                                     # closed: bass and thump
       (32, 3000), (38, 4500), (40, 18000),                                # "let the highs come through"
       (50, 18000), (52, 1400), (55, 9000), (56, 12000),                   # a slow dip in the instrumental
       (57, 12000), (57.25, 80), (60, 80), (61.5, 2500),                   # "eighty hertz"... "now all I hear is bass"
       (62, 3000), (63, 3500), (63.5, 18000),                              # "put the treble in its place"
       (72, 18000), (73.5, 150), (76, 150), (80 - V0, 9000), (80, 18000),  # close it... open it up
       (96, 18000), (111.5, 180), (BARS, 180)]
RESO = 1.3


def phaser(x, i0, i1, stages=6, lo=280.0, hi=3200.0, mix=.45, block=256):
    """Six all-pass stages swept by a slow sine (one cycle every four bars, the channels a quarter apart),
    mixed with the dry sound: moving notches, the disco swoosh."""
    rate = 1 / (4 * S.bar)
    kk = np.arange(stages + 1)
    binom = np.array([math.comb(stages, k) for k in kk], float)
    for ch in range(2):
        zi = np.zeros(stages)
        y = np.empty(i1 - i0)
        for i in range(i0, i1, block):
            fc = lo * (hi / lo) ** (.5 + .5 * math.sin(2 * math.pi * rate * i / SR + ch * math.pi / 2))
            w = math.tan(math.pi * fc / SR)
            a = (w - 1) / (w + 1)
            b, den = binom * a ** (stages - kk), binom * a ** kk
            y[i - i0:i - i0 + block], zi = signal.lfilter(b, den, x[i:min(i + block, i1), ch], zi=zi)
        x[i0:i1, ch] = (1 - mix) * x[i0:i1, ch] + mix * y
    return x


def pump(depth, release=.75):
    """The sidechain: down with every kick, back up over most of the beat (the French house breath)."""
    g = np.ones(S.n)
    L = int(release * B * SR)
    att = int(.004 * SR)
    u = np.arange(L) / L
    shape = (1 - u) ** 2 * np.minimum(np.arange(L) / att, 1)
    for tk in S.kicks:
        i = int(tk * SR)
        j = min(i + L, S.n)
        g[i:j] = np.minimum(g[i:j], 1 - depth * shape[:j - i])
    return g


cut = curve(CUT)
i0, i1 = int(S.at(16) * SR) - 2048, min(int((S.at(112) + 3) * SR), S.n)
for stem, (depth, wet, echo, phase_it) in {"bass": (.35, 0, 0, False), "pads": (.6, .35, 0, True),
                                          "keys": (.45, .25, .08, True)}.items():
    x = LOOP.pop(stem).astype(np.float64)
    for ch in range(2):
        x[i0:i1, ch] = e.sweep(x[i0:i1, ch], cut[i0:i1], RESO, 128)
    if phase_it:
        x = phaser(x, i0, i1)
    x *= pump(depth)[:, None]
    S.bus[stem] += x.astype(np.float32)
    if wet:
        S.send += (x * wet).astype(np.float32)
    if echo:
        S.echo += (x * echo).astype(np.float32)
    del x

here = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "renders", "low-pass-love_122bpm_Am.wav")
os.makedirs(os.path.dirname(out), exist_ok=True)
S.mixdown(out, {"drums": .85, "perc": .7, "bass": 2.0, "pads": 2.0, "keys": 1.6, "lead": 1.8, "vox": 1.8, "fx": .3},
          duck={"lead": .1}, room=.2, echo_mix=.4, lufs=-10.0,
          ir=room.impulse_response((9.0, 6.5, 3.5), rt60=1.5))
