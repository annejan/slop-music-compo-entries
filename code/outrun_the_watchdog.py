#!/usr/bin/env python3
"""Outrun The Watchdog: synthwave, 118 BPM, D minor. A timed dry run of a surprise round (synthwave, drawn by the
night's workflow on 19 November), made alone in the night: not heard by anyone yet when written.

outrun_the_watchdog.py [OUT.wav]          PREVIEW=32-48 outrun_the_watchdog.py: only bars 32 to 47
TAKES=1,2,3 outrun_the_watchdog.py        make the singer's ACE-Step takes (seeds 1, 2, 3) and stop

Firmware hangs at three in the morning, and the watchdog timer counts down: kick it, or it resets the badge. The
singer (ACE-Step's own take, played whole) drifts over the neon night drive: "Outrun the watchdog, kick it every
night". The room shouts the real name of the job: "Kick it!". In the break the main loop is stuck and the timeout
counts down; the room kicks it just in time. "Good dog."

The band is the synthwave kit (kits.py): 118 BPM, Dm Bb C Am, the gated snare, the pulsing sixteenth bass, the
Juno pad, the square arpeggio, the gliding saw lead, a big hall. Choices made from the genre's known traits, for
the morning's ears to judge:
- The singer is an airy, breathy female voice (the research's prompt: "airy female vocal"), sung a cappella by
  ACE-Step and laid over the band at about -8 dB under it, as in Push It To Prod and Uptime Fever.
- Under her take the kit's chorus plays without its lead line (the lead would sing against her); the lead comes
  back in the bars after her take.
- The room's "Kick it!" is a one-word call like Uptime Fever's "Up-time!": short, so it fits between the snares.
- The narrators are Ryan and Lessac, plain speech, as in Uptime Fever.

  bars   0-15  intro: the drums alone (for the DJ), gated toms at the end of each 8 bars
        16-31  the band comes in: bass and pad, then the arpeggio; the room teases "Kick it!"
        32-47  A: her take (8 bars) over the band, then the lead and the room's "Kick it!"
        48-63  the verse: the two narrators tell the story; the room from 56
        64-71  the break: no kick, the pad; the countdown; the room kicks it
        72-79  the build: the drums back, the room faster, a snare roll, a riser
        80-95  the last chorus: her take again, then the lead and the room
        96-111 outro: the drums alone (for the DJ)
"""
import glob
import os

import numpy as np

import engine as e
import kits
import parts
import room
import voice as V

# ---------------------------------------------------------------- the knobs
TITLE = "Outrun The Watchdog"
DAY = "Rehearsal: synthwave"
KIT = "synthwave"
K = kits.KITS[KIT]
BPM, BARS = K["bpm"], 112              # 118
KEY = K["key"]                         # Dm
KEY_CHANGE = 0
SINGER_SEED = int(os.environ.get("SINGER_SEED", "1"))

e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)
put = S.put
P = kits.band(KIT, S)
HERE = os.path.dirname(os.path.abspath(__file__))
TAKES_DIR = os.path.join(HERE, "renders", "ace", "takes", "outrun_the_watchdog")

# ---------------------------------------------------------------- the singer: ACE-Step's own take, played whole
CAPTION = ("1980s synthwave, an airy dreamy female vocal, breathy and cool, neon night drive, "
           "clear words, slow sustained notes")
HOOK = ["Outrun the watchdog", "Kick it every night", "Racing the timer", "Under neon lights"]


def singer_take(seed):
    """The take for this seed (takes.take caches it by its request). Made only with TAKES=...; a render without
    the take stops with a message instead of starting ACE-Step."""
    found = sorted(glob.glob(os.path.join(TAKES_DIR, f"chorus_s{seed}_*.wav")))
    if found and not os.environ.get("TAKES"):
        return found[0]
    if not os.environ.get("TAKES"):
        raise SystemExit(f"no take for seed {seed} in {TAKES_DIR}: make it with TAKES={seed} first")
    import takes
    return takes.take(CAPTION, takes.ace_words(HOOK, "Chorus"), BPM, "D minor", 8, seed, TAKES_DIR, "chorus", "en")


if os.environ.get("TAKES"):
    for s_ in os.environ["TAKES"].split(","):
        print(singer_take(int(s_)))
    raise SystemExit


def singer(bar, seed=SINGER_SEED, amp=.9):
    """Her whole take from the downbeat of `bar`, uncut, lightly band-limited (as Uptime Fever's diva)."""
    if not S.live(bar, 8):
        return
    import takes
    x = e.bandpass(takes.mono(singer_take(seed)), 110, 9000)
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * .1
    put("vox", S.at(bar), x, .5, amp, wet=.3, echo=.12)       # a little more hall and echo than disco: synthwave


# ---------------------------------------------------------------- the band: the kit, and its chorus without the lead
def band(bar, part):
    kits.play(KIT, S, P, bar, part)


def under_her(bar):
    """The kit's chorus with no lead line: the bars where she sings."""
    kits.synthwave_drums(S, P, bar, crash=bar % 8 == 0, fill=bar % 8 == 7)
    kits.synthwave_bass(S, P, bar, 1.0, cut=650)
    kits.synthwave_pads(S, P, bar, 1.1, cut=2400)
    kits.synthwave_arp(S, P, bar, .8, cut=4000)


def build(bar):
    """The build: the drums back (the kick from bar 76), the bass, the pad, the arpeggio opening up."""
    kits.synthwave_drums(S, P, bar, kick=bar >= 76, fill=bar == 79)
    kits.synthwave_bass(S, P, bar, .9, cut=300 + 60 * (bar - 72))
    kits.synthwave_pads(S, P, bar, 1.0, cut=1400 + 150 * (bar - 72))
    kits.synthwave_arp(S, P, bar, .8, cut=1500 + 400 * (bar - 72))


# ---------------------------------------------------------------- the room and the narrators
_takes = {}


def shout(text, secs, voice, pitch):
    k = (text, round(secs, 4), voice, pitch)
    if k not in _takes:
        _takes[k] = V.rap(text, secs, voice=voice, pitch=pitch)
    return _takes[k]


GANG = [("en_US-joe-medium", .2), ("en_US-john-medium", .8), ("en_US-amy-medium", .35),
        ("en_US-kristin-medium", .65), ("en_US-bryce-medium", .5)]


def kick_it(bar, beat=0.0, amp=1.0):
    """The room: "Kick it!", a little apart in time and pitch."""
    if not S.live(bar):
        return
    for i, (v, pan) in enumerate(GANG):
        put("vox", S.at(bar, beat) + .007 * i - .014, shout("Kick it!", 1.4 * S.beat, v, .95 + .05 * i), pan,
            .42 * amp, wet=.2, echo=.06)


def gasp(bar, beat=0.0, word="Ooh!", amp=.8):
    """The room, all together, one word."""
    if not S.live(bar):
        return
    for i, (v, pan) in enumerate(GANG):
        put("vox", S.at(bar, beat) + .009 * i - .02, shout(word, 1.2 * S.beat, v, 1.0 + .04 * i), pan, .4 * amp,
            wet=.25, echo=.05)


RYAN, LESSAC = "en_US-ryan-high", "en_US-lessac-high"        # the two dry narrators, taking turns


def mc(bar, text, voice, amp=1.0, beat=0.0):
    """A narrator: plain speech at its own pace, clean."""
    if not S.live(bar, 2):
        return
    y = V._finish(V.tts(text, voice))
    put("vox", S.at(bar, beat), y * (.14 / (np.sqrt(np.mean(y ** 2)) + 1e-9)), .5, amp, wet=.12, echo=.12)


LINES = {48: ("Three in the morning. The firmware hangs.", RYAN),
         50: ("Somewhere in the main loop, a watchdog is counting.", LESSAC),
         52: ("Sixteen seconds. Fifteen. Fourteen.", RYAN),
         54: ("Feed it, or it bites.", LESSAC)}
BREAK = {64: ("The main loop is stuck.", LESSAC, 0.0), 66: ("Watchdog timeout in three.", RYAN, 0.0),
         68: ("Two. One.", LESSAC, 0.0), 70: ("Good dog.", RYAN, 2.0)}
GASPS = {64: "Ooh!", 66: "Ooh!"}

# ---------------------------------------------------------------- the arrangement
for bar in range(BARS):
    if bar < 16 or bar >= 96:
        band(bar, "drums")
        continue
    if bar < 24:
        band(bar, "intro")
    elif bar < 32:
        band(bar, "verse")
        if bar in (28, 30):
            kick_it(bar, 0, .8)
            kick_it(bar, 2, .8)
    elif 32 <= bar < 40 or 80 <= bar < 88:                            # her take
        under_her(bar)
        if bar in (32, 80):
            singer(bar, amp=.9 if bar == 32 else 1.0)
    elif 40 <= bar < 48 or 88 <= bar < 96:                            # the lead and the room
        band(bar, "chorus")
        if bar % 2 == 0:
            kick_it(bar, 0)
            kick_it(bar, 2)
    elif 48 <= bar < 64:                                              # the verse: the narrators
        band(bar, "verse")
        if bar in LINES:
            mc(bar, *LINES[bar])
        if bar >= 56 and bar % 2 == 0:
            kick_it(bar, 0, .8)
            kick_it(bar, 2, .8)
    elif 64 <= bar < 72:                                              # the break: no kick, the countdown
        band(bar, "break")
        if bar in BREAK:
            text, voice, beat = BREAK[bar]
            mc(bar, text, voice, 1.1, beat)
        if bar in GASPS:
            gasp(bar, 2, GASPS[bar])
        if bar == 70:
            kick_it(bar, 0, 1.2)
    elif 72 <= bar < 80:                                              # the build: the room, faster
        build(bar)
        n = 2 if bar < 76 else 4
        for b in range(0, 4, 4 // n):
            kick_it(bar, b, .7 + .05 * (bar - 72))

P.roll(76, 4)
S.put("fx", S.at(76), e.riser(S.bar * 4, .35), .5, wet=.3)
S.put("fx", S.at(64), e.downlifter(S.bar * 2, .3), .5, wet=.3)
S.put("fx", S.at(28), e.riser(S.bar * 4, .3), .5, wet=.3)
P.finish()
NAME = f"outrun-the-watchdog_{BPM}bpm_{KEY}"
S.mixdown(parts.out_path(NAME), dict(K["mix"], vox=1.3), room=.2, echo_mix=.35, lufs=K["lufs"],
          ir=room.impulse_response(*K["room"]))
print(f"share.SONGS row: (\"{NAME}.wav\", \"{TITLE}\", \"{DAY}\", {BPM}, \"{KEY}\", {BARS}),")
