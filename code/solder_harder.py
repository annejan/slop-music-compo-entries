#!/usr/bin/env python3
"""Solder Harder: gabber, 180 BPM, A minor. A timed dry run for the surprise theme (gabber, drawn for the night of
19 November), made alone in one go, without anyone listening: every choice below is from the genre's known traits.

solder_harder.py [OUT.wav]          PREVIEW=32-48 solder_harder.py: only bars 32 to 47, for a quick listen
TAKES=1,2,3 solder_harder.py        make the MC's ACE-Step takes (seeds 1, 2, 3) and stop
MC_SEED=1 solder_harder.py          the song with another take (default 3)

A badge-building night at a hacker camp: three hundred joints to go, the iron at four hundred and fifty degrees, and
the Rotterdam MC (ACE-Step's own take, played whole) yells "Solder harder! Burn it in!". The room shouts "Harder!",
and in the break a cold joint is found: more flux.

  bars   0-15  intro: the gabber drums alone (for the DJ)
        16-31  the hoover riff comes in behind a closed filter; the room teases "Harder!"
        32-47  the chorus: the MC's whole take (16 bars), the hoover riff, the poing, the stabs
        48-63  the verse: the kick, the poing, the stabs; two narrators tell the story; the room from 56
        64-71  the break: no kick, the pad and the held hoover; "Cold joint detected." (the room gasps)
        72-79  the build: the riff's filter opens, the room faster, a snare roll, a kick roll, a riser
        80-95  the last chorus: the MC's take again, the room
        96-111 outro: the gabber drums alone (for the DJ)

The band is the "gabber" kit from kits.py (kits.band, kits.play, and its parts for the build), unchanged. The
choices from the genre's traits (research/surprise-genres.md, not heard yet):
- 180 BPM and the distorted kick that is the bass as well, no bassline: the kit's.
- the voice: a hoarse shouting male MC, not a diva: gabber records are shouted MC samples, not sung.
- the hook is short words on the beat, repeated ("Solder harder", "Burn it in"): shouted, not a melody.
- the room shouts one word ("Harder!") in the gaps, like the crowd samples on the records.
- the narrators (Ryan and Lessac) stay plain speech, as in Uptime Fever; at 180 BPM a line has two bars (2.7 s).
- the take sits at the level of Push It To Prod and Uptime Fever (about -8 dB under the band).
- a kick roll on the eighths in the last bar of the build: the classic gabber run into the drop.
"""
import os

import numpy as np

import engine as e
import kits
import parts
import room
import voice as V

# ---------------------------------------------------------------- the knobs
KIT = kits.KITS["gabber"]
TITLE = "Solder Harder"
DAY = "Rehearsal: gabber"
BPM, BARS = KIT["bpm"], 112            # 180
KEY = KIT["key"]                       # Am
KEY_CHANGE = 0
LUFS = KIT["lufs"]                     # -8.5
MC_SEED = int(os.environ.get("MC_SEED", "3"))        # the software ear: seed 3 80 %, 1 60 %, 2 42 %

e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)
SR = e.SR
put = S.put
P = kits.band("gabber", S)             # Am Am F E
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- the MC: ACE-Step's own take, played whole
MC_CAPTION = ("early 1990s Rotterdam gabber, a hoarse shouting male MC, aggressive hype, hardcore rave crowd "
              "energy, clear words")
MC_LINES = ["Solder harder, solder harder", "Burn it in, burn it in", "Solder harder, solder harder",
            "Hardcore flux, let the smoke begin"] * 2
MC_BARS = 16                           # 21.3 s at 180 BPM
TAKES_DIR = os.path.join(HERE, "renders", "ace", "takes", "solder_harder")


def mc_take(seed):
    """The take for this seed (takes.take: cached by its request, made when missing; ACE_LOCK shares the GPU)."""
    import takes
    return takes.take(MC_CAPTION, takes.ace_words(MC_LINES, "Chorus"), BPM, "A minor", MC_BARS, seed, TAKES_DIR,
                      "chorus", "en")


if os.environ.get("TAKES"):
    for s_ in os.environ["TAKES"].split(","):
        print(mc_take(int(s_)))
    raise SystemExit


def mc_shout(bar, seed=MC_SEED, amp=.9):
    """The MC's whole take from the downbeat of `bar`, uncut, lightly band-limited (as Uptime Fever's diva)."""
    if not S.live(bar, MC_BARS):
        return
    from math import gcd
    from scipy import signal as sg
    import master
    x, sr = master.read(mc_take(seed))
    x = x.mean(1)
    if sr != SR:
        g = gcd(SR, sr)
        x = sg.resample_poly(x, SR // g, sr // g)
    x = e.bandpass(x, 150, 9000)
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * .1
    put("vox", S.at(bar), x, .5, amp, wet=.2, echo=.08)


# ---------------------------------------------------------------- the room and the narrators
_takes = {}


def shout(text, secs, voice, pitch):
    k = (text, round(secs, 4), voice, pitch)
    if k not in _takes:
        _takes[k] = V.rap(text, secs, voice=voice, pitch=pitch)
    return _takes[k]


GANG = [("en_US-joe-medium", .2), ("en_US-john-medium", .8), ("en_US-amy-medium", .35),
        ("en_US-kristin-medium", .65), ("en_US-bryce-medium", .5)]


def harder(bar, beat=0.0, amp=1.0, word="Harder!"):
    """The room: one shouted word, a little apart in time and pitch."""
    if not S.live(bar):
        return
    for i, (v, pan) in enumerate(GANG):
        put("vox", S.at(bar, beat) + .007 * i - .014, shout(word, 1.8 * S.beat, v, .95 + .05 * i), pan,
            .42 * amp, wet=.18, echo=.06)


RYAN, LESSAC = "en_US-ryan-high", "en_US-lessac-high"        # the two dry narrators, taking turns


def mc(bar, text, voice, amp=1.0, beat=0.0):
    """A narrator: plain speech at its own pace, clean."""
    if not S.live(bar, 2):
        return
    y = V._finish(V.tts(text, voice))
    put("vox", S.at(bar, beat), y * (.14 / (np.sqrt(np.mean(y ** 2)) + 1e-9)), .5, amp, wet=.1, echo=.12)


LINES = {48: ("Three hundred joints to go.", RYAN), 50: ("The iron is set to four fifty.", LESSAC),
         52: ("Somebody said: lead free.", RYAN), 54: ("Nobody listened.", LESSAC),
         56: ("The fume extractor gave up an hour ago.", RYAN), 58: ("The smoke alarm is dancing.", LESSAC)}
BREAK = {64: ("Cold joint detected.", LESSAC), 66: ("Reflow it.", RYAN), 68: ("More flux?", LESSAC),
         70: ("More flux.", RYAN)}
GASPS = {64: "Ooh!", 68: "Flux!", 70: "Yeah!"}

# ---------------------------------------------------------------- the arrangement
for bar in range(BARS):
    if bar < 16 or bar >= 96:                                          # the DJ's drums
        kits.gabber_drums(S, P, bar, crash=bar in (0, 96))
        continue
    if bar < 32:                                                       # the riff comes in, filter closed
        kits.play("gabber", S, P, bar, "intro")
        if bar in (24, 28):
            harder(bar, 0, .8)
            harder(bar, 2, .8)
    elif bar < 48 or 80 <= bar < 96:                                   # the chorus: the MC's whole take
        kits.play("gabber", S, P, bar, "chorus")
        if bar in (32, 80):
            mc_shout(bar, amp=.9 if bar == 32 else 1.0)
        if bar % 8 == 7:
            harder(bar, 2, .7)
    elif bar < 64:                                                     # the verse: the narrators
        kits.play("gabber", S, P, bar, "verse")
        if bar in LINES:
            mc(bar, *LINES[bar])
        if bar >= 56 and bar % 2 == 1:                                 # after each line, then on every bar at the end
            harder(bar, 2)
        if bar in (60, 62):
            harder(bar, 0)
            harder(bar, 2)
    elif bar < 72:                                                     # the break: no kick, the story
        kits.play("gabber", S, P, bar, "break")
        if bar in BREAK:
            mc(bar, *BREAK[bar], amp=1.1)
        if bar in GASPS:
            harder(bar, 2, .8, GASPS[bar])
    else:                                                              # the build: the filter opens, the room faster
        kits.gabber_drums(S, P, bar, fill=bar == 79)
        kits.gabber_riff(S, P, bar, .8, cut=700 * 2 ** ((bar - 72) / 3.5))
        kits.gabber_stab(S, P, bar, steps=(0, 3, 6, 10, 12) if bar >= 76 else (0, 3, 6), amp=.8)
        n = 2 if bar < 76 else 4
        for b in range(0, 4, 4 // n):
            harder(bar, b, .6 + .05 * (bar - 72))
        if bar == 79 and S.live(bar):                                  # the kick roll on the eighths
            m = e.root_note(P.prog[0], P.key_of(bar), lo=33)
            for k in (2, 6, 10, 14):
                put("drums", S.at(bar) + k * S.step, kits.gabber_kick(m, round(2 * S.step - .012, 4)), .5, .8,
                    wet=0)

P.roll(76, 4)
put("fx", S.at(76), e.riser(S.bar * 4, .35), .5, wet=.3)
put("fx", S.at(64), e.downlifter(S.bar * 2, .3), .5, wet=.3)
put("fx", S.at(28), e.riser(S.bar * 4, .3), .5, wet=.3)
P.finish()
NAME = f"solder-harder_{BPM}bpm_{KEY}"
S.mixdown(parts.out_path(NAME), dict(KIT["mix"], vox=1.3), room=.2, echo_mix=.35, lufs=LUFS,
          ir=room.impulse_response(*KIT["room"]))
print(f"share.SONGS row: (\"{NAME}.wav\", \"{TITLE}\", \"{DAY}\", {BPM}, \"{KEY}\", {BARS}),")
