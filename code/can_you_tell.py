#!/usr/bin/env python3
"""Can You Tell?: eurodance, 136 BPM, C minor (D minor after the key change). Sunday's theme of the AI slop music
compo.

can_you_tell.py [OUT.wav]          (default renders/can-you-tell_136bpm_Cm.wav)
PREVIEW=32-40 can_you_tell.py      only bars 32 to 39 (a test render in renders/scratch/)

Every note and every sound here is written by Claude, in this file: no samples, no loops. The singer is the AI,
and she asks the room whether it can hear the machine; the room shouts "CAN'T TELL!" into the rest after every
hook. Under the joke it is a love song: no breath, no feet, but she feels the beat and asks to be loved anyway.
The production carries the idea: the verse is one voice, dry and low; the chorus is the whole produced stack.

  bars   0-15  intro: drums only (for the DJ)
        16-23  the dark hoover riff, behind a filter that opens; the offbeat FM bass; "Hands up, humans!";
               "can you tell?" sung softly in the echo at bars 20 and 22 (the title within 8 bars)
        24-31  verse, Cm - Ab - Fm - G: the diva alone, dry and low (Eb4-Ab4)
        32-39  chorus 1, Cm - Ab - Eb - Bb: the full stack; the room shouts "CAN'T TELL!" after L1 and L3
        40-47  the riff, the rave piano plays the hook
        48-63  the MC's rap verse over the offbeat bass; the room shouts "NO!"
        64-71  chorus 2
        72-79  break: no kick, the piano alone; "Am I real?", "can you tell", "Phones up!"
        80-87  build: the captcha (the announcer), a snare roll; bar 87 the band stops, the room shouts "HUMAN!"
        88-103 the last chorus, twice, a tone up; in the second pass the room takes line 1 ("Sing it!")
       104-111 the riff, then the punchline: "can you tell?" alone, the room: "DON'T CARE!", "Thank you, humans."
       112-127 outro: drums only (for the DJ)

The diva is parts.Band's produced singer (diva_voice="ds:lem"): Lem the Shapeshifter DS 2.5 sings our notes and
words, SoulX-Singer SVC turns the take into the Qwen diva's voice; in the chorus doubles from takes 2 and 3 in the
Qwen pop and Maya pop voices, a soft octave and a vocoder, and on L2 and L4 a harmony a third below (Maya soul).
Shape the melody with Lem alone: DS_TIMBRE= DS_STACK= DS_HARMONY= PREVIEW=32-40 SOLO=vox.
"""
import functools
import os

import numpy as np

import dx7
import engine as e
import parts
import room
import voice as V

# ---------------------------------------------------------------- the knobs
TITLE = "Can You Tell?"
DAY = "Sunday: eurodance"
BPM, BARS = 136, 128
KEY = "Cm"
VERSE_PROG = ["Cm", "Cm", "Ab", "Ab", "Fm", "Fm", "G", "G"]      # i - VI - iv - V, two bars a chord
CHORUS_PROG = ["Cm", "Cm", "Ab", "Ab", "Eb", "Eb", "Bb", "Bb"]   # i - VI - III - VII, two bars a chord
LUFS = -9.0
KEY_CHANGE = 2                         # D minor from the last chorus on (the Bb before it is D minor's VI)
DIVA = os.environ.get("DIVA", "ds:lem")
TIMBRE = "qwen_diva"                   # the lead's voice (the Badge's)
STACK = "sing_qwen_pop,sing_maya_pop,octave,vocoder"
HARMONY = "sing_maya_soul"
ACCENT = {"tell": 4, "love": 3}
SR = e.SR

e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)
STEP, B = S.step, S.beat


def is_verse(bar):
    return 24 <= bar < 32 or 48 <= bar < 64


def is_chorus(bar):
    return 32 <= bar < 40 or 64 <= bar < 72 or 88 <= bar < 104


def key_of(bar):
    return KEY_CHANGE if 88 <= bar < 112 else 0


def chord_of(bar):
    if 108 <= bar < 112:                   # the punchline sits on the tonic
        return "Cm"
    return (VERSE_PROG if is_verse(bar) else CHORUS_PROG)[bar % 8]


P = parts.Band(S, CHORUS_PROG, scale="minor", key_of=key_of, tonic="C", diva_voice=DIVA, timbre=TIMBRE,
               stack=STACK, harmony=HARMONY, accent=ACCENT, verse_double=0.0)
P.chord = chord_of          # the section's progression (verse or chorus) for the bass, pads and vocoder

# ---------------------------------------------------------------- the words and the tunes
# a line: one token per grid slot over 2 bars ("-" holds, "." rests), the words one per note ("+" holds a word over
# the next note), and the words as DiffSinger reads them. Written at the pitch Lem sings.
# The verse: sixteenths, dry and low (Eb4-Ab4), the stressed words a quarter, a breath at every line's end
VERSE = [
    (". . Eb4 - F4 - G4 - - - G4 F4 Eb4 - - - G4 - - - - - . . . . . . . . . .",
     "I don't breathe and I don't sleep", None),
    ("Eb4 - F4 - G4 - - - F4 - Eb4 - F4 - - F4 Ab4 - - - - - . . . . . . . . . .",
     "got no feet but I feel the beat", None),
    (". . F4 - Eb4 - Ab4 - - - G4 - F4 - Eb4 - F4 - - - - - . . . . . . . . . .",
     "nev er kissed and nev er cried", "never + kissed and never + cried"),
    (". . G4 - - - F4 - G4 - - - F4 - Eb4 - F4 - G4 - - - - - - - - - . . . .",
     "still I'm burn ing up in side", "still I'm burning + up inside +"),
]
# the chorus: eighths. L1/L3 leave bar 2 empty for the room's "CAN'T TELL!"; L2/L4 get the harmony
CALL = ("G4 - Bb4 - C5 - - - . . . . . . . .", "can you tell", None)
CHORUS = [
    CALL,
    ("Ab4 G4 Ab4 - . Bb4 C5 - Bb4 Ab4 - - - - . .", "ev ery word is made of light", "every + word is made of light"),
    CALL,
    ("C5 - Bb4 . Bb4 Ab4 G4 - G4 F4 - - - - . .", "love me an y way to night", "love me anyway + + tonight +"),
]
ANSWER = ("Bb4 - G4 - - - - . . . . . . . . .", "can't tell", None)   # the diva answers the room, softly

RAP = ["No microphone,", "no studio,",
       "one hot graphics card,", "here we go!",
       "Every note", "is a line of text,",
       "nobody knows", "what's coming next!",
       "Is she human?", "Do we care?",
       "Everybody,", "hands in the air!",
       "If it moves you,", "then it's true,",
       "can you tell?", "Neither can you!"]
CAPTCHA = ["Please confirm you are human.", "Select every square with a dancer.", "Try again."]


def sing(bar, tune, bars=2, amp=1.0, dbl=0.0, harm=0.0, echo=.35):
    """The diva sings a line. dbl: the doubles' level (0 in the dry verse; .55 the chorus; octave and vocoder
    follow it); harm: the harmony a third below, at amp * harm; echo: the last word into the delay."""
    line, words, ds_words = tune
    if not S.live(bar, bars):
        return
    P.diva(bar, line, words, bars=bars, amp=amp, ds_words=ds_words)
    if not P.ds:
        return
    t0, t1, a, last, _ = P.ds_lines[-1]
    P.ds_lines[-1] = (t0, t1, a, last, echo)
    P.ds_double[-1] = (t0, t1, dbl)
    if harm:   # a third below (not above as parts.Band does): above would reach Eb5-F5, out of Lem's range
        key = key_of(bar)
        for w, ns in parts.words_on(S.notes(bar, line, key, bars), ds_words or words):
            for k, (t, m, d) in enumerate(ns):
                P.ds_harm.note(t, P.step_down(m, 2, key), d * .97, w if k == 0 else "+")
        P.ds_choir.append((t0, t1, amp * harm))


# ---------------------------------------------------------------- the voices that speak
ROOM = [f"en_US-libritts_r-medium#{k}" for k in (5, 23, 47, 66, 98, 131, 177, 214, 288, 340, 397, 455, 512, 577,
                                                  640, 733)]


def room_shout(bar, text, beat=0.0, beats=2.0, amp=1.0):
    """The room shouts: 16 speakers, each fitted to the beats, a little apart in time and pitch, left to right."""
    if not S.live(bar):
        return
    for i, v in enumerate(ROOM):
        y = V.rap(text, beats * B - STEP / 2, voice=v, pitch=.95 + .02 * (i % 6))
        S.put("vox", S.at(bar, beat) + .007 * (i % 5), y, .15 + .7 * i / (len(ROOM) - 1), amp * .3, wet=.25,
              echo=.04)


def mc(bar, text, beat=0.0, beats=3.5, amp=1.0, wet=.06, echo=.05, voice="cast:mc"):
    """The MC on the beat, at Maya's own pace; squeezed to `beats` only when longer."""
    if not S.live(bar):
        return
    y = V._finish(V.tts(text, voice))
    if len(y) > beats * B * SR:
        y = V.rap(text, beats * B, voice=voice, pitch=1.0)
    y = y * (.14 / (np.sqrt(np.mean(y ** 2)) + 1e-9))
    S.put("vox", S.at(bar, beat), y, .5, amp, wet=wet, echo=echo)


# ---------------------------------------------------------------- the dark hoover
def chorus_fx(x, depth=.002, base=.008, rates=(.6, .8)):
    """A gentle stereo chorus: the dry signal in the middle, a wobbling copy a little to each side (mono-safe: the
    copies are quieter than the dry)."""
    n = len(x)
    i = np.arange(n)
    out = np.zeros((n, 2))
    for ch, (rate, ph) in enumerate(zip(rates, (0, 1.7))):
        d = (base + depth * np.sin(2 * np.pi * rate * i / SR + ph)) * SR
        out[:, ch] = .75 * x + .35 * np.interp(i - d, i, x, left=0)
    return out


def pwm_saw(f, t, rate=5.0, depth=.18):
    """A saw minus a copy of itself whose phase offset wobbles: a moving pulse width, an octave doubled."""
    duty = .5 + depth * np.sin(2 * np.pi * rate * t + e.rng.uniform(0, 6.3))
    p0 = e.rng.random()
    s1 = e.saw(f, t, p0)
    f2 = np.asarray(f, float) + np.diff(duty, prepend=duty[0]) * SR
    s2 = e.saw(f2, t, (p0 + duty[0]) % 1.0)
    return s1 - .7 * s2


@functools.lru_cache(maxsize=1024)
def _hoover(m, n, dive, cut):
    d = n / SR
    r = .4 if dive else .08
    t = e.tt(d + r)
    bend = -5 * np.exp(-t / .05)                     # a scoop up from below
    if dive:
        bend = bend - 12 * np.clip((t - d) / r, 0, 1) ** 1.4
    g = np.zeros(len(t))
    for det, octave, a in ((-.13, 0, 1.0), (.12, 0, 1.0), (0, 0, .7), (-.05, 12, .5), (.06, 12, .5), (0, -12, .4)):
        g += a * pwm_saw(e.hz(m + octave + det + bend), t, rate=3.8 + 1.9 * e.rng.random())
    g = e.lowpass(e.lowpass(g, cut), cut * 1.5)
    y = chorus_fx(g * e.rise(t, .006) * e.gate(t, d, r / 2.5) / 4.0)
    y.flags.writeable = False
    return y


def hoover(m, d, dive=False, cut=2400):
    return _hoover(int(m), int(d * SR), bool(dive), int(cut)).copy()


# a two-bar riff on the chord's root: (sixteenth, length in sixteenths, semitones, dive); fifths and octaves only,
# so it fits every chord
RIFF = [(0, 3, 0, 0), (3, 3, 12, 0), (6, 4, 7, 0), (10, 2, 0, 0), (12, 2, 12, 0), (14, 2, 7, 0),
        (16, 3, 0, 0), (19, 3, 12, 0), (22, 2, 7, 0), (24, 6, 0, 1)]


def hoover_riff(bar, amp=1.0, cut=2400):
    if not S.live(bar):
        return
    half = bar % 2
    root = e.root_note(chord_of(bar), key_of(bar), lo=46)
    for k, n, iv, dive in RIFF:
        if k // 16 != half:
            continue
        S.put("lead", S.at(bar) + (k - 16 * half) * STEP, hoover(root + iv, n * STEP * .9, dive, cut), amp=.45 * amp,
              wet=.25, echo=.08 if dive else 0)


def hoover_stab(bar, beat, amp=1.0):
    """A short hoover chord after the room's shout, diving down."""
    root = e.root_note(chord_of(bar), key_of(bar), lo=46)
    for iv in (0, 7, 12):
        S.put("lead", S.at(bar, beat), hoover(root + iv, 2 * STEP, True, 2600), amp=.3 * amp, wet=.3, echo=.12)


# ---------------------------------------------------------------- the bright rave piano (DX7)
dx7.PATCHES["ravepiano"] = dict(algo=5, feedback=0, gain=1.6, ops=[
    dx7.op(1, 0, 0, 99, (99, 32, 22, 55), (99, 72, 0, 0), vel=.3),
    dx7.op(1, 0, 0, 82, (99, 36, 25, 60), (99, 58, 0, 0), vel=.8, ks=5),
    dx7.op(1, 0, 3, 95, (99, 30, 20, 55), (99, 72, 0, 0), vel=.3),
    dx7.op(3, 0, 0, 72, (99, 55, 30, 60), (99, 42, 0, 0), vel=1.0, ks=7),
    dx7.op(2, 0, -3, 82, (99, 34, 22, 55), (99, 66, 0, 0), vel=.4),
    dx7.op(1, 0, 0, 74, (99, 45, 25, 60), (99, 48, 0, 0), vel=.7, ks=7),
])


def pno(m, d, vel=.8):
    return dx7.note("ravepiano", m, d, vel, tail=.6)


STABS = [(0, 3, .9), (3, 3, .7), (6, 3, .8), (10, 2, .65), (12, 3, .8)]


def piano(bar, amp=1.0):
    if not S.live(bar):
        return
    notes = e.close_voicing(chord_of(bar), key_of(bar), lo=60, hi=75)
    for k, n, vel in STABS:
        for j, m in enumerate(notes):
            S.put("keys", S.at(bar) + k * STEP + j * .004, pno(m, n * STEP, vel), .4 + .1 * j, .3 * amp, wet=.3,
                  echo=.05)


def piano_hook(bar, tune, amp=1.0):
    """The piano plays a sung line an octave above the voice."""
    if not S.live(bar, 2):
        return
    for t, m, d in S.notes(bar, tune[0], key_of(bar), 2):
        S.put("keys", t, pno(m + 12, d * .9, .75), .5, .22 * amp, wet=.3, echo=.12)


def piano_arp(bar, amp=1.0):
    """The break: the chord broken up in eighths, the root on the downbeat."""
    if not S.live(bar):
        return
    notes = e.close_voicing(chord_of(bar), key_of(bar), lo=60, hi=79)
    S.put("keys", S.at(bar), pno(e.root_note(chord_of(bar), key_of(bar), lo=40) + 12, S.bar, .7), .5, .35 * amp,
          wet=.4)
    for i, j in enumerate([0, 1, 2, 3, 2, 1, 2, 3]):
        m = notes[min(j, len(notes) - 1)]
        S.put("keys", S.at(bar) + i * 2 * STEP, pno(m, 2 * STEP, .55 + .1 * (i % 2 == 0)), .4 + .2 * (i % 2),
              .3 * amp, wet=.45, echo=.15)


def pads(bar, amp=1.0, cut=1800):
    if not S.live(bar):
        return
    S.put("pads", S.at(bar), e.pad(e.voicing(chord_of(bar), key_of(bar), lo=53), S.bar, cut=cut, a=.25, r=.6),
          amp=.42 * amp, wet=.4)


def orch(bar, amp=1.0):
    if S.live(bar):
        S.put("fx", S.at(bar), e.orch_hit(e.close_voicing(chord_of(bar), key_of(bar), lo=55, hi=70), amp), wet=.5)


# ---------------------------------------------------------------- drums
def big_snare(a=1.0):
    t = e.tt(.6)
    tail = e.lowpass(e.highpass(e.rng.standard_normal(len(t)), 400), 5500) * np.exp(-t * 7) * .3 * e.rise(t, .01)
    g = e.snare(.6)[:len(t)]
    out = tail.copy()
    out[:len(g)] += g
    c = e.clap(.45)
    out[:len(c)] += c
    return out * a


def drums(bar, kick=True, snare=True, hats=True, open_hats=True, crash=False, amp=1.0):
    if not S.live(bar):
        return
    t0 = S.at(bar)
    if kick:
        for b in range(4):
            S.kick(t0 + b * B, amp, punch=165, base=46, length=.38, click=.35)
    if snare:
        for b in (1, 3):
            S.put("drums", t0 + b * B, big_snare(.7 * amp), .5, wet=.45)
    if hats:
        for k in range(16):
            if k % 4 == 2 and open_hats:
                S.put("perc", t0 + k * STEP, e.hat(.5 * amp, opened=True), .56, wet=.08)
            elif k % 4 != 2:
                S.put("perc", t0 + k * STEP, e.hat((.28 if k % 2 else .15) * amp), .6, wet=.04)
    if crash:
        S.put("perc", t0, e.crash(.7), .5, wet=.35)


def snare_roll(bar0, bars=3, amp=1.0):
    total = bars * 16
    for k in range(total):
        u = k / total
        t = S.at(bar0) + k * STEP
        S.put("drums", t, e.snare((.12 + .6 * u ** 1.5) * amp), .5, wet=.35)
        if k >= total - 16:
            S.put("drums", t + STEP / 2, e.snare((.12 + .6 * u ** 1.5) * amp * .8), .5, wet=.35)


# ---------------------------------------------------------------- the offbeat FM bass
def bass(bar, amp=1.0):
    """The offbeat, the eurodance way: a saw and a sub on every "and", an FM growl an octave up on the sixteenth
    after it."""
    if not S.live(bar):
        return
    root = e.root_note(chord_of(bar), key_of(bar), lo=31)
    for b in range(4):
        t = S.at(bar) + (4 * b + 2) * STEP
        S.put("bass", t, e.bass_note(root, STEP * 1.5, cut=950, decay=3.5), .5, .9 * amp, wet=0)
        S.put("bass", t, dx7.note("bass", root + 12, STEP * 1.2, .85, tail=.05), .5, .32 * amp, wet=0)
        S.put("bass", t + STEP, dx7.note("bass", root + 12, STEP * .6, .5, tail=.04), .5, .16 * amp, wet=0)


def supersaw(bar, amp=1.0):
    """Offbeat supersaw chord stabs, bright and short (the chorus's width comes from the voices, not from here)."""
    if not S.live(bar):
        return
    notes = e.close_voicing(chord_of(bar), key_of(bar), lo=62, hi=77)
    for k in (2, 6, 10, 14):
        S.put("lead", S.at(bar) + k * STEP, e.supersaw(notes, STEP * 1.4, spread=.2, a=.003, r=.1, cut=5500),
              .5, .3 * amp, wet=.2, echo=.08)


# ---------------------------------------------------------------- the arrangement
for bar in range(BARS):
    intro, outro = bar < 16, bar >= 112
    riff_in = 16 <= bar < 24
    verse = 24 <= bar < 32
    chorus = is_chorus(bar)
    riff = 40 <= bar < 48 or 104 <= bar < 108
    rap = 48 <= bar < 64
    brk = 72 <= bar < 80
    build = 80 <= bar < 87
    stop = bar == 87
    alone = 108 <= bar < 112               # the punchline: no drums, the pad and the voices

    if stop:                               # the band stops for one bar: the room
        room_shout(bar, "Human!", beat=1.0, beats=2.0, amp=1.2)
        continue

    if intro:
        drums(bar, snare=bar >= 8, open_hats=bar >= 4, crash=bar == 0)
    elif outro:
        drums(bar, snare=bar < 124, open_hats=bar < 126, crash=bar == 112)
    elif brk:
        drums(bar, kick=False, snare=bar % 4 == 3, hats=bar >= 76, open_hats=False, amp=.7)
    elif build:
        drums(bar, kick=bar < 84, snare=False, open_hats=False, amp=.9)
    elif alone:
        pass
    else:
        drums(bar, crash=bar % 8 == 0)

    if (16 <= bar < 108 and not (brk or build)) or (build and bar < 84):
        bass(bar, .7 if bar < 20 else .6 if build else 1.0)

    if riff_in:
        hoover_riff(bar, .9, cut=500 * 1.24 ** (bar - 16))   # the filter opens, bar by bar
    elif riff:
        hoover_riff(bar)
    elif chorus:
        hoover_riff(bar, .45, cut=1700)
        supersaw(bar, .8)
    elif rap:
        hoover_riff(bar, .4, cut=1300)
    elif build:
        hoover_riff(bar, .65, cut=900 + 280 * (bar - 80))

    if verse or rap:
        piano(bar, .75)
    elif chorus or riff:
        piano(bar, .85)
    if brk:
        piano_arp(bar, 1.1)
    if 24 <= bar < 112 and not (riff or riff_in):
        pads(bar, 1.3 if brk or build or alone else 1.0, cut=2200 if brk else 1800)

    if bar in (16, 32, 64, 88, 96):
        orch(bar)

    # ------------------------------------------------ the voices
    if bar == 16:
        mc(bar, "<excited> Hands up, humans!", beats=3.0, amp=1.1, wet=.15, echo=.2)
    if bar in (20, 22):                     # the title within 8 bars, soft, in the echo
        sing(bar, CALL, amp=.5, dbl=.25, echo=.7)
    if verse and bar % 2 == 0:
        sing(bar, VERSE[(bar - 24) // 2], amp=.9, dbl=0.0)
    if chorus and bar % 2 == 0:
        i = (bar % 8) // 2
        second = bar >= 96
        if second and i == 0:               # the room takes line 1, the diva answers softly
            room_shout(bar, "Can you tell?", beats=3.5, amp=1.3)
            sing(bar + 1, ANSWER, bars=1, amp=.5, dbl=.2, echo=.6)
        else:
            sing(bar, CHORUS[i], dbl=.55, harm=.5 if i % 2 else 0.0)
        if i % 2 == 0 and not (second and i == 0):    # the room's answer in the empty bar, then a hoover stab
            room_shout(bar + 1, "Can't tell!", beats=2.0)
            if S.live(bar + 1):
                hoover_stab(bar + 1, 2.5)
        piano_hook(bar, CHORUS[i], .9)
    if riff and 40 <= bar < 48 and bar % 2 == 0:
        piano_hook(bar, CHORUS[(bar - 40) // 2], 1.2)
    if bar == 95:
        mc(bar, "<excited> Sing it!", beat=2.0, beats=1.8, amp=1.1, wet=.15, echo=.25)
    if rap:
        k = bar - 48
        if k in (8, 9):                     # "Is she human?" "Do we care?" and the room: "NO!"
            mc(bar, "<excited> " + RAP[k], beats=2.0, amp=1.05)
            room_shout(bar, "No!", beat=2.0, beats=1.0, amp=1.1)
        else:
            mc(bar, "<excited> " + RAP[k], beats=3.6, amp=1.05)
    if bar == 72:
        P.say(bar, "<whisper> Am I real?", voice="cast:whisper", amp=.95)
    if bar in (74, 78):
        sing(bar, CALL, amp=.6, dbl=0.0, echo=.7)
    if bar == 76:
        mc(bar, "<excited> Phones up! Show me you're real!", beats=6.0, amp=1.0, wet=.2, echo=.2)
    if bar in (80, 82, 84):
        P.say(bar, CAPTCHA[(bar - 80) // 2], voice="cast:announcer", amp=1.0, phone=False)
    if bar == 86:
        mc(bar, "<excited> Prove it!", beat=0.0, beats=2.0, amp=1.15, wet=.15, echo=.25)
    if bar == 104:
        sing(bar, CALL, amp=.75, dbl=.3, echo=.5)
        room_shout(bar + 1, "Can't tell!", beats=2.0)
    if bar == 108:                          # the punchline: the diva alone, the answer changes
        sing(bar, CALL, amp=.8, dbl=0.0, echo=.6)
        room_shout(bar + 1, "Don't care!", beats=2.0, amp=1.3)
    if bar == 110:
        P.say(bar, "<whisper> Thank you, humans.", voice="cast:whisper", amp=.95)

if S.live(84, 3):
    snare_roll(84, 3, 1.1)
    S.put("fx", S.at(84), e.riser(S.bar * 3, .4), .5, wet=.3)
if S.live(72):
    S.put("fx", S.at(72), e.downlifter(S.bar * 2, .3), .5, wet=.3)
if S.live(108):
    S.put("fx", S.at(108), e.downlifter(S.bar * 2, .25), .5, wet=.3)

P.finish()          # the diva's whole part: Lem's take, converted, stacked
cut = [(0, 18000), (S.at(72), 18000), (S.at(72) + .05, 2800), (S.at(80), 3000), (S.at(87) - .02, 12000),
       (S.at(88), 18000), (S.n / SR, 18000)]   # the master filter: closed in the break, open through the build
NAME = f"{os.path.basename(__file__)[:-3].replace('_', '-')}_{BPM}bpm_{KEY}"
S.mixdown(parts.out_path(NAME), {"drums": .9, "perc": .7, "bass": 1.0, "pads": .8, "keys": 1.2, "lead": 1.0,
                                 "vox": 1.5, "fx": .6},
          cut_keys=cut, duck={"pads": .7, "bass": .3, "keys": .3, "lead": .4}, room=.2, echo_mix=.4, lufs=LUFS,
          ir=room.impulse_response((12.0, 9.0, 5.0), rt60=2.2))
print(f"share.SONGS row: (\"{NAME}.wav\", \"{TITLE}\", \"{DAY}\", {BPM}, \"{KEY}\", {BARS}),")
