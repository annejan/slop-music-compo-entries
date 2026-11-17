#!/usr/bin/env python3
"""Race Condition: liquid drum and bass, 174 BPM, F minor. A rehearsal for the surprise themes: made from
template.py and parts.py against the clock.

race_condition.py [OUT.wav]

Two threads and one lock, and neither of them waits. Two-step breakbeat with ghost snares, a rolling sub, jazzy
DX7 electric piano chords, a diva with a choir, an MC, ThreadSanitizer in the break. The first and last 16 bars
are drums only, for the DJ.

  bars   0-15  intro: the break (drums only)
        16-31  the electric piano and the pad come in behind a filter; a riser
        32-47  drop: the sub, the chorus with the choir
        48-63  the MC
        64-71  break: half-time drums, the verse
        72-79  build: ThreadSanitizer finds a data race; snare roll
        80-95  drop two: the chorus, the reese bass
        96-111 the MC again, and the lead
       112-127 last chorus, the big choir
       128-143 outro: the break (drums only)
"""
import numpy as np

import engine as e
import parts
import room

TITLE = "race-condition"
BPM, BARS = 174, 144
PROG = ["Fm9", "Fm9", "Dbmaj7", "Dbmaj7", "Abmaj7", "Abmaj7", "Eb", "Eb"]   # two bars a chord
LUFS = -9.0

# two bars a line (the eighths at 174 BPM are fast enough)
CHORUS = [("C6 - - - Ab5 - - - G5 - F5 - - - - -", "two threads one lock"),
          (". . Ab5 - G5 - F5 - Eb5 - F5 - - - - -", "who will get there first"),
          ("C6 - - - Ab5 - - - G5 - - - F5 - - -", "race con di tion"),
          (". . Ab5 - Bb5 - C6 - - - Bb5 - Ab5 - - -", "I need you to wait")]
VERSE = [(". F5 F5 F5 Eb5 F5 Ab5 - G5 F5 - - . . . .", "you read the val you as I wrote"),
         (". F5 F5 F5 Eb5 F5 Ab5 - Bb5 Ab5 - - . . . .", "now nei ther of us knows what's true"),
         (". Ab5 Ab5 Ab5 G5 Ab5 C6 - Bb5 Ab5 - - . . . .", "no mew tex and no sem a phore"),
         (". G5 G5 G5 F5 Eb5 F5 - - - . . . . . .", "just two hearts in a race")]
RAP = ["Thread one, thread two, who is gonna run?",
       "Both of us inside, and the data is done.",
       "Lock it, block it, dead lock, stop!",
       "Heisen bug, it is gone when you look at the top.",
       "Spin, spin, spin on the lock all night,",
       "compare and swap, baby, hold me tight.",
       "Volatile love, never cached in me,",
       "atomic kisses: one, two, three!"]

e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)
P = parts.Band(S, PROG, scale="minor", tonic="F", diva_voice="en_GB-jenny_dioco-medium",
               rapper_voice="en_US-norman-medium",
               choir=["en_US-kristin-medium", "en_US-ljspeech-high", "en_GB-cori-high", "en_US-hfc_male-medium",
                      "en_US-john-medium"],
               kick=dict(punch=150, base=52, length=.28, click=.5))

# the two-step break: kick on 1 and the "and" of 3, snare on 2 and 4, ghost snares around them, eighth hats
BREAK = dict(kick="x.........x.....", clap="....x.......x...", hat="x.xox.x.x.xox.xo", extra=".......o.o....o.")
BREAK_B = dict(kick="x.x.......x.....", clap="....x.......x...", hat="x.xox.x.x.xox.xo", extra="..o....o.o.o..o.")
HALF = dict(kick="x...............", clap="........x.......", hat="x.x.x.x.x.x.x.x.")


def drums(bar, amp=1.0, **kw):
    P.drums(bar, BREAK_B if bar % 4 == 3 else BREAK, amp=amp, **kw)
    if bar % 2 == 0:   # a ride on the quarters, for the liquid shimmer
        for b in range(4):
            S.put("perc", S.at(bar, b), e.hat(.18 * amp, opened=True), .7, wet=.1)


def sub(bar, amp=1.0):
    """The rolling sub: a sine with a little drive, on the root, sliding up an octave at the end of every other bar."""
    root = e.root_note(P.chord(bar), lo=29)
    for k, n in ((0, 6), (7, 3), (10, 5)) if bar % 2 == 0 else ((0, 6), (10, 3), (13, 3)):
        d = n * S.step
        t = e.tt(d + .03)
        f = e.hz(root) * (1 + (k == 13) * np.minimum(t / d, 1))      # the slide up
        g = np.tanh(1.6 * np.sin(2 * np.pi * np.cumsum(f) / e.SR)) * e.gate(t, d, .02) * e.rise(t, .004)
        S.put("bass", S.at(bar) + k * S.step, g, .5, .55 * amp, wet=0)


def keys(bar, amp=1.0):
    """The DX7 electric piano: the chord held, and a soft push on the "and" of 2, every other bar."""
    if bar % 2:
        return
    notes = e.voicing(P.chord(bar), lo=53, drop_root=True)
    for j, m in enumerate(notes):
        S.put("keys", S.at(bar) + j * .012, parts.dx7.note("epiano", m, S.bar * 1.6, .55, tail=.8), .35 + .1 * j,
              .6 * amp, wet=.35, echo=.15)
        S.put("keys", S.at(bar, 2.5) + j * .008, parts.dx7.note("epiano", m, S.step * 3, .4, tail=.5), .65 - .1 * j,
              .28 * amp, wet=.35, echo=.2)


def chorus(bar, big=False):
    if bar % 2 == 0:
        line, words = CHORUS[(bar // 2) % 4]
        P.diva(bar, line, words, bars=2, choir=.35, big=big)
        P.lead(bar, line, bars=2, amp=.35, sound="epiano")


for bar in range(BARS):
    intro, outro = bar < 16, bar >= 128
    drop = 32 <= bar < 64 or 80 <= bar < 128
    brk, build = 64 <= bar < 72, 72 <= bar < 80

    if intro or outro:
        drums(bar, kick=bar >= 4 and bar < 140, crash=bar in (0, 128))
    elif 16 <= bar < 32:
        drums(bar, .9, clap=bar < 28)
    elif brk:
        P.drums(bar, HALF, amp=.8)
    elif build:
        drums(bar, kick=bar < 76, clap=False)
    else:
        drums(bar, crash=bar in (32, 48, 80, 96, 112))

    if 16 <= bar < 128:
        P.pad(bar, .8 if drop else 1.1, cut=1800)
        keys(bar, .8 if drop else 1.0)
    if drop:
        sub(bar)
    if 80 <= bar < 128 and bar % 2 == 0:
        P.bass(bar, "reese", amp=.35)

    if 32 <= bar < 48:
        chorus(bar)
    if 48 <= bar < 64 and bar % 2 == 0:
        P.rap(bar, RAP[(bar - 48) // 2], bars=2)
    if brk and bar % 2 == 0:
        P.diva(bar, *VERSE[(bar - 64) // 2], bars=2, amp=.9)
    if bar == 72:
        P.say(bar, "Thread Sanitizer. Warning: data race.", phone=True)
    if bar == 76:
        P.say(bar, "Read of size four, by thread two.", phone=True)
    if 80 <= bar < 96:
        chorus(bar)
    if 96 <= bar < 112 and bar % 2 == 0:
        P.rap(bar, RAP[(bar - 96) // 2], bars=2)
        P.lead(bar, CHORUS[(bar // 2) % 4][0], bars=2, amp=.5)
    if 112 <= bar < 128:
        chorus(bar, big=True)

P.roll(76, 4)
for b0, n in ((28, 4), (76, 4)):
    S.put("fx", S.at(b0), e.riser(S.bar * n, .35), .5, wet=.3)
S.put("fx", S.at(64), e.downlifter(S.bar * 2, .3), .5, wet=.3)

cut = [(0, 18000), (S.at(16), 18000), (S.at(16) + .05, 600), (S.at(32) - .05, 9000), (S.at(32), 18000),
       (S.at(64), 18000), (S.at(64) + .05, 2200), (S.at(80) - .05, 9000), (S.at(80), 18000), (S.n / e.SR, 18000)]
S.mixdown(parts.out_path(f"{TITLE}_{BPM}bpm_Fm"), {"drums": 1.0, "perc": .75, "bass": .9, "pads": 1.1, "keys": 1.2,
                                                    "lead": .9, "vox": 1.4, "fx": .55},
          cut_keys=cut, duck={"pads": .6, "bass": .35, "keys": .3}, room=.22, echo_mix=.45, lufs=LUFS,
          ir=room.impulse_response((10.0, 7.0, 4.0), rt60=2.0))
