#!/usr/bin/env python3
"""Pull-Up Resistor: happy hardcore, 170 BPM, F major. A rehearsal of the surprise round (19 November), made
from kit_template.py by the WEEKEND.md playbook, without anyone listening. Below: the template's own notes.

KIT TEMPLATE: the start of a surprise-round song on one of kits.py's 11 genre kits (kits.py --list), the way
Overclocked Heart was made in the rehearsal of 19 November: the kit's band, an ACE-Step diva take played whole in
the choruses, spoken parts from the voice cast. Copy it (cp kit_template.py my_song.py), set the knobs, write the
spoken lines. It renders as it is, as a test (without a diva until one is pinned).

my_song.py [OUT.wav]                 PREVIEW=48-64 my_song.py: only bars 48 to 63, for a quick listen
CAST="mc=qwen_hype" my_song.py       another voice for a role (a test render, to renders/scratch/)

The diva (WEEKEND.md, "The diva: a draft round"): make drafts with takes.py my_song --drafts ..., pick one by ear,
--keep it, bring it to the song's tempo and key with takes.finish and pin it with
takes.pin(wav, "my_song", "chorus"): this script plays renders/ace/takes/my_song/pinned/chorus.wav and never makes a
take itself. DIVA_OFFSET=-1 plays it a bar earlier (fit.py's offset).

For delivery: append the line printed at the end to the END of share.SONGS, write the lyric sheet as
../lyrics/NN-my_song.txt (NN: its row number), then share.py --only my-song and dj.py --only my_song.

  bars   0-15  intro: the kit's drums alone (for the DJ)
        16-31  the kit's intro part (the band behind a filter)
        32-47  verse: the kit's verse part, two narrators tell the story
        48-63  chorus: the kit's chorus part, the diva's whole take
        64-71  break: the kit's break part (no kick), the announcer
        72-79  build: the verse part, a snare roll, a riser
        80-95  the last chorus: the diva's take again
        96-111 outro: the kit's drums alone (for the DJ)
"""
import os

import numpy as np

import engine as e
import kits
import parts
import room
import voice as V

# ---------------------------------------------------------------- the knobs
KIT_NAME = "happy hardcore"                  # kits.py --list: trance, eurobeat, hardstyle, gabber, happy hardcore, ...
TITLE = "Pull-Up Resistor"
DAY = "Rehearsal: happy hardcore"              # "Saturday: <genre>" or "Sunday: <genre>": the set it plays in
CHORUS_LEAD = False                    # the kit's lead line in the choruses (trance, Hi-NRG) under the diva: off
NARRATOR_A, NARRATOR_B, ANNOUNCER = "cast:narrator", "cast:diva", "cast:announcer"   # voice.CAST roles or names
MC = "cast:mc"

KIT = kits.KITS[KIT_NAME]
BPM, BARS = KIT["bpm"], 112
KEY = KIT["key"]
KEY_CHANGE = 0
LUFS = KIT["lufs"]
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.basename(__file__)[:-3]
NAME = f"{SCRIPT.replace('_', '-')}_{BPM}bpm_{KEY}"
TAKES_DIR = os.path.join(HERE, "renders", "ace", "takes", SCRIPT)
DIVA_WAV = os.environ.get("DIVA_WAV") or os.path.join(TAKES_DIR, "pinned", "chorus.wav")
DIVA_BARS = 16
DIVA_OFFSET = int(os.environ.get("DIVA_OFFSET", "1"))   # whole bars: -1 = the take one bar earlier
# fit.py: the take (round 2, draft 3, SFT guidance 7) fits the chords 53 % one bar later, 24 % as laid. One bar
# later, its 16.45 sung bars run past the chorus: into the break (the announcer waits until bar 66) and, in the
# last chorus, into the DJ's drums-only outro. So the last chorus plays the take up to LAST_BARS: six lines, cut at
# the dip before the seventh (take bar 11.99), and the kit's hook comes back for the chorus's last three bars.
LAST_BARS = 11.98
# The software ear (asr.hear on the full mix, chorus bars): at the template's level it heard none of the diva's
# words over this kit (0 %, Overclocked Heart's approved choruses: 49 and 53 %); GAIN=vox previews: x1.6 7 %, x2.0
# 33 %, x2.5 52 %. Not heard by a person yet: DIVA_GAIN is the diva alone (the spoken lines were heard as they are).
DIVA_GAIN = 2.5
MC_AMP = 2.0                           # the build's MC shouts: at 1.1 lost under the snare roll and the riser
HAS_DIVA = os.path.exists(DIVA_WAV)
if not HAS_DIVA:
    print(f"no diva yet: {DIVA_WAV} (pin a take with takes.pin)")

e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)
put = S.put
P = kits.band(KIT_NAME, S)

# ---------------------------------------------------------------- the words (spoken; tags like <excited> reach Maya)
VERSE = {32: ("Pin thirteen was floating.", NARRATOR_A), 34: ("Reading noise all night.", NARRATOR_B),
         36: ("High, low, nobody knew.", NARRATOR_A), 38: ("Then a resistor came along.", NARRATOR_B),
         40: ("Ten K, tied to the rail.", NARRATOR_A), 42: ("<excited> And the pin went high!", NARRATOR_B)}
BREAK = {66: ("Attention, all floating inputs.", ANNOUNCER), 68: ("Please pull up now.", ANNOUNCER),
         70: ("Thank you.", ANNOUNCER)}
BUILD = {76: ("<excited> Pull up! Pull up!", MC), 78: ("<excited> Ten K to the sky!", MC)}


def say(bar, text, voice, amp=1.0, beat=0.0):
    """A spoken line at its own pace from `bar` (beat), clean."""
    if not S.live(bar, 2):
        return
    y = V._finish(V.tts(text, voice))
    put("vox", S.at(bar, beat), y * (.14 / (np.sqrt(np.mean(y ** 2)) + 1e-9)), .5, amp, wet=.12, echo=.15)


def diva(bar, amp=1.0, bars=None):
    """The pinned ACE-Step take, whole (or its first `bars` bars, the last 80 ms faded), from the downbeat of `bar`,
    lightly band-limited. The level comes from the whole take, so a cut take sits at the same level."""
    if not HAS_DIVA or not S.live(bar, bars or DIVA_BARS):
        return
    import takes
    x = e.bandpass(takes.mono(DIVA_WAV), 120, 10000)
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * .1
    if bars:
        x = x[:int(bars * S.bar * e.SR)].copy()
        f = int(.08 * e.SR)
        x[-f:] *= np.linspace(1, 0, f)
    put("vox", S.at(bar), x, .5, amp, wet=.25, echo=.12)


def diva_sings(bar):
    """True in a chorus bar where the pinned take sings: the first chorus's take whole, the last one up to LAST_BARS."""
    if not HAS_DIVA:
        return False
    a, b = 48 + DIVA_OFFSET, 80 + DIVA_OFFSET
    return a <= bar < a + DIVA_BARS or b <= bar < b + (LAST_BARS or DIVA_BARS)


def chorus(bar):
    """The kit's chorus; its lead line (trance, Hi-NRG) stays out while the diva sings, unless CHORUS_LEAD. The
    happy hardcore kit plays its hook with kits.hh_lead straight onto the lead bus, not with P.lead, so that one is
    held back here too (CHORUS_LEAD alone did not reach it)."""
    if diva_sings(bar) and not CHORUS_LEAD:
        keep, P.lead = P.lead, (lambda *a, **k: None)
        keep_hook, kits.hh_lead = kits.hh_lead, (lambda *a, **k: None)
        kits.play(KIT_NAME, S, P, bar, "chorus")
        P.lead, kits.hh_lead = keep, keep_hook
    else:
        kits.play(KIT_NAME, S, P, bar, "chorus")


# ---------------------------------------------------------------- the arrangement
for bar in range(BARS):
    if bar < 16 or bar >= 96:                                          # the DJ's drums
        kits.play(KIT_NAME, S, P, bar, "drums")
    elif bar < 32:
        kits.play(KIT_NAME, S, P, bar, "intro")
    elif bar < 48:
        kits.play(KIT_NAME, S, P, bar, "verse")
        if bar in VERSE:
            say(bar, *VERSE[bar])
    elif bar < 64 or 80 <= bar < 96:
        chorus(bar)
        if bar == 48:
            diva(bar + DIVA_OFFSET, DIVA_GAIN)
        elif bar == 80:
            diva(bar + DIVA_OFFSET, DIVA_GAIN, bars=LAST_BARS)
    elif bar < 72:
        kits.play(KIT_NAME, S, P, bar, "break")
        if bar in BREAK:
            say(bar, *BREAK[bar], amp=1.1)
    else:                                                              # the build
        kits.play(KIT_NAME, S, P, bar, "verse")
        if bar in BUILD:
            say(bar, *BUILD[bar], amp=MC_AMP)

P.roll(76, 4)
put("fx", S.at(72), e.riser(S.bar * 8, .35), .5, wet=.3)
put("fx", S.at(64), e.downlifter(S.bar * 2, .3), .5, wet=.3)
put("fx", S.at(28), e.riser(S.bar * 4, .25), .5, wet=.3)
P.finish()
S.mixdown(parts.out_path(NAME), dict(KIT["mix"], vox=1.3), room=.2, echo_mix=.35, lufs=LUFS,
          ir=room.impulse_response(*KIT["room"]))
print(f"share.SONGS row: (\"{NAME}.wav\", \"{TITLE}\", \"{DAY}\", {BPM}, \"{KEY}\", {BARS}),")
