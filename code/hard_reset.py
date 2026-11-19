#!/usr/bin/env python3
"""Hard Reset: hardstyle, 150 BPM, F# minor. A timed dry run of a surprise round (hardstyle, drawn by the workflow on
the night of 19 November), made alone, without anyone listening. Not heard yet.

hard_reset.py [OUT.wav]            PREVIEW=32-48 hard_reset.py: only bars 32 to 47, for a quick listen
TAKE_SEED=2 hard_reset.py          the singer's take with seed 2 (default 3: the most words for the software ear)

A badge froze at 99 % of a firmware update, at three in the morning. The only way out: hold the button for ten
seconds. The singer (ACE-Step's own a cappella take, played whole) sings the anthem "Hold the button, count to ten,
hard reset, we rise again", the room shouts "Hard reset!", and in the breakdown the narrators count it down.

  bars   0-15  intro: the hardstyle drums alone (for the DJ)
        16-31  the reverse bass and the pad come in; the narrators offer the update; the lead behind a filter from 24
        32-47  the anthem: the singer's whole take (32-39) over the band, the lead held back; then the full lead
               and the room's "Hard reset!"
        48-63  the verse: the narrators tell what went wrong; the room from 56
        64-71  the breakdown: no beat, the pad, a piano, the lead behind a filter that opens; "Hold the power button."
        72-79  the build: the room counts down from six, a snare roll, a riser, the lead opening up
        80-95  the last anthem: her take again, then the full lead and the room
        96-111 outro: the drums alone (for the DJ)

The band is the kit kits.play("hardstyle", ...): the distorted pitched kick, the reverse bass, the big clap, the
anthem lead (3-3-3-3-2-2), the pumping pad, i-VI-III-VII. Choices made from the genre's traits, not by ear:
- The singer is a male anthem voice ("euphoric hardstyle anthem, a powerful male vocalist"), as the research's
  hardstyle prompt asks for a male vocal hook; a female voice is as common in euphoric hardstyle.
- Under the take the lead plays as in the kit's verse (half level, behind a 1.8 kHz filter), so the words come
  through; the full lead answers in the eight bars after the take, as hardstyle leads answer a vocal.
- The take sits at the level of Uptime Fever's diva (RMS 0.1, amp 0.9, vox bus 1.3): about -8 dB under the band.
- The narrators (Ryan and Lessac) speak plainly, a little louder (1.15) than in Uptime Fever: the kick is louder.
- The breakdown is the kit's 8 bars; the build keeps the kick out and lets the room count down to the drop.
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
TITLE = "Hard Reset"
DAY = "Rehearsal: hardstyle"
KIT = kits.KITS["hardstyle"]
BPM, BARS = KIT["bpm"], 112
KEY = KIT["key"]
KEY_CHANGE = 0
LUFS = KIT["lufs"]
HERE = os.path.dirname(os.path.abspath(__file__))
TAKES_DIR = os.path.join(HERE, "renders", "ace", "hard_reset")
TAKE_SEED = int(os.environ.get("TAKE_SEED", "3"))      # the ear: seed 1 45 %, seed 2 64 %, seed 3 77 %
HOOK = ["Hold the button, count to ten", "Hard reset, we rise again",
        "Hold the button, count to ten", "Hard reset, we rise again"]

e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)
SR = e.SR
put = S.put
P = kits.band("hardstyle", S)


def play(bar, part):
    kits.play("hardstyle", S, P, bar, part)


# ---------------------------------------------------------------- the singer: ACE-Step's own take, played whole
def take_path(seed=TAKE_SEED):
    """The take for this seed, made by takes.take() (4B LM, SFT DiT, a cappella, 8 bars): None when missing."""
    got = sorted(glob.glob(os.path.join(TAKES_DIR, f"chorus_s{seed}_*.wav")))
    return got[-1] if got else None


def singer(bar, amp=.9):
    """The whole take from the downbeat of `bar`, uncut, lightly band-limited (as in Uptime Fever)."""
    if not S.live(bar, 8):
        return
    path = take_path()
    if not path:
        print(f"no take for seed {TAKE_SEED} in {TAKES_DIR}: the singer is left out")
        return
    from math import gcd
    from scipy import signal as sg
    import master
    x, sr = master.read(path)
    x = x.mean(1)
    if sr != SR:
        g = gcd(SR, sr)
        x = sg.resample_poly(x, SR // g, sr // g)
    x = e.bandpass(x, 110, 9000)
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * .1
    put("vox", S.at(bar), x, .5, amp, wet=.22, echo=.08)


# ---------------------------------------------------------------- the room and the narrators
_shouts = {}


def shout(text, secs, voice, pitch):
    k = (text, round(secs, 4), voice, pitch)
    if k not in _shouts:
        _shouts[k] = V.rap(text, secs, voice=voice, pitch=pitch)
    return _shouts[k]


GANG = [("en_US-joe-medium", .2), ("en_US-john-medium", .8), ("en_US-amy-medium", .35),
        ("en_US-kristin-medium", .65), ("en_US-bryce-medium", .5)]


def call(bar, beat=0.0, word="Hard reset!", beats=2.0, amp=1.0):
    """The room, all together, a little apart in time and pitch."""
    if not S.live(bar):
        return
    for i, (v, pan) in enumerate(GANG):
        put("vox", S.at(bar, beat) + .007 * i - .014, shout(word, beats * S.beat, v, .95 + .05 * i), pan,
            .42 * amp, wet=.2, echo=.06)


RYAN, LESSAC = "en_US-ryan-high", "en_US-lessac-high"


def mc(bar, text, voice, amp=1.15, beat=0.0):
    """A narrator: plain speech at its own pace, clean."""
    if not S.live(bar, 2):
        return
    y = V._finish(V.tts(text, voice))
    put("vox", S.at(bar, beat), y * (.14 / (np.sqrt(np.mean(y ** 2)) + 1e-9)), .5, amp, wet=.1, echo=.12)


INTRO = {16: ("Firmware update available.", LESSAC), 20: ("Install now?", RYAN), 22: ("Yes.", LESSAC)}
VERSE = {48: ("Three in the morning.", RYAN), 50: ("Ninety nine percent.", LESSAC),
         52: ("Then the screen went white.", RYAN), 54: ("The badge is bricked.", LESSAC)}
BREAK = {64: ("Hold the power button.", LESSAC), 66: ("Ten seconds.", RYAN), 68: ("Do not let go.", LESSAC),
         70: ("Nine. Eight. Seven.", RYAN)}
COUNT = {72: "Six!", 73: "Five!", 74: "Four!", 75: "Three!", 76: "Two!", 77: "One!"}

# ---------------------------------------------------------------- the arrangement
for bar in range(BARS):
    if bar < 16 or bar >= 96:
        play(bar, "drums")
        continue
    if bar < 24:
        play(bar, "intro")
    elif bar < 32:
        play(bar, "verse")
    elif 32 <= bar < 40 or 80 <= bar < 88:                  # the take: the band, the lead held back
        kits.hardstyle_drums(S, P, bar, crash=bar in (32, 80))
        kits.hardstyle_bass(S, P, bar)
        kits.hardstyle_pad(S, P, bar, 1.0)
        kits.hardstyle_lead(S, P, bar, .5, cut=1800)
    elif 40 <= bar < 48 or 88 <= bar < 96:
        play(bar, "chorus")
    elif bar < 64:
        play(bar, "verse")
    elif bar < 72:
        play(bar, "break")
    else:                                                   # the build: no kick, the lead opens, the room counts
        P.pad(bar, 1.3, cut=2500 + 400 * (bar - 72))
        kits.hardstyle_lead(S, P, bar, .8 + .03 * (bar - 72), cut=4000 + 600 * (bar - 72))

    if bar in INTRO:
        mc(bar, *INTRO[bar])
    if bar in (24, 28):
        call(bar, 0, amp=.8)
    if bar in (32, 80):
        singer(bar, amp=.9 if bar == 32 else 1.0)
    if (40 <= bar < 48 or 88 <= bar < 96) and bar % 2 == 0:
        call(bar, 0)
        call(bar, 2)
    if bar in VERSE:
        mc(bar, *VERSE[bar])
    if 56 <= bar < 64 and bar % 2 == 0:
        call(bar, 0, amp=1.0)
    if bar in BREAK:
        mc(bar, *BREAK[bar])
    if bar == 66:
        call(bar, 2, "Ooh!", 1.2, .8)
    if bar in COUNT:
        call(bar, 0, COUNT[bar], 1.5, .8 + .05 * (bar - 72))
    if bar in (78, 79):                                      # "Reset!" alone, in one beat, was heard as "The seven"
        call(bar, 0, amp=1.1)
        call(bar, 2, "Hard reset!" if bar == 78 else "Now!", 2.0 if bar == 78 else 1.5, 1.2)

P.roll(76, 4)
put("fx", S.at(76), e.riser(S.bar * 4, .35), .5, wet=.3)
put("fx", S.at(64), e.downlifter(S.bar * 2, .3), .5, wet=.3)
put("fx", S.at(28), e.riser(S.bar * 4, .3), .5, wet=.3)

P.finish()
NAME = f"hard-reset_{BPM}bpm_{KEY}"
S.mixdown(parts.out_path(NAME), dict(KIT["mix"], vox=1.3), room=.2, echo_mix=.35, lufs=LUFS,
          ir=room.impulse_response(*KIT["room"]))
print(f"share.SONGS row: (\"{NAME}.wav\", \"{TITLE}\", \"{DAY}\", {BPM}, \"{KEY}\", {BARS}),")
