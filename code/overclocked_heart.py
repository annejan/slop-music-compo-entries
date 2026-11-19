#!/usr/bin/env python3
"""Overclocked Heart: Hi-NRG, 128 BPM, B minor. The dress rehearsal of 19 November (Hi-NRG drawn at 13:09), made
the compo-day way: the user picked the pitch and the singer, then the take by ear.

overclocked_heart.py [OUT.wav]          PREVIEW=48-64 overclocked_heart.py: only bars 48 to 63, for a quick listen
TAKES=1,2,3 overclocked_heart.py        make the diva's ACE-Step takes (seeds 1, 2, 3) and stop
DIVA_SEED=2 overclocked_heart.py        the song with another take

A diva whose heart runs past spec for her lover: ninety-five degrees, the fans screaming, "don't you throttle me".
The diva is ACE-Step's own take, played whole, sung 3 semitones lower and slower and lifted by Rubber Band
(takes.py --lift 3: the user's pick, "really 90s eurotrash"). In the break the machine warns of the heat.

  bars   0-15  intro: the Hi-NRG drums alone (for the DJ)
        16-31  the octave bass comes in behind a closed filter, then the stabs
        32-47  the verse: two narrators tell how it started
        48-63  the chorus: the diva's whole take (16 bars), the bass, the brass stabs, the pad
        64-71  the break: no kick, the pad and the bass behind a filter that opens; the thermal warning
        72-79  the build: the fans spin up (a riser), a snare roll
        80-95  the last chorus: the diva's take again, the orchestra hit on every downbeat
        96-111 outro: the Hi-NRG drums alone (for the DJ)

The band is the "hi-nrg" kit from kits.py, without its lead line in the choruses (the diva sings there).
"""
import os

import numpy as np

import engine as e
import kits
import parts
import room
import voice as V

# ---------------------------------------------------------------- the knobs
KIT = kits.KITS["hi-nrg"]
TITLE = "Overclocked Heart"
DAY = "Rehearsal: Hi-NRG"
BPM, BARS = KIT["bpm"], 112            # 128
KEY = KIT["key"]                       # Bm
KEY_CHANGE = 0
LUFS = KIT["lufs"]
DIVA_SEED = int(os.environ.get("DIVA_SEED", "2"))
DIVA_OFFSET = int(os.environ.get("DIVA_OFFSET", "0"))   # whole bars: -1 = the take one bar earlier (fit.py's offset)

e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)
SR = e.SR
put = S.put
P = kits.band("hi-nrg", S)             # Bm Em A F#
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- the diva: ACE-Step's own take, lifted, played whole
DIVA_CAPTION = "1980s Hi-NRG, a powerful dramatic female dance diva, soaring, theatrical, clear words"
DIVA_LINES = ["Overclocked heart, running way too hot", "Every time you touch me, I give all I've got",
              "Overclocked heart, past the red line", "Ninety-five degrees and I'm feeling fine",
              "Overclocked heart, the fans are screaming loud", "Spinning out of spec in a dancing crowd",
              "Overclocked heart, don't you throttle me", "Push me to the limit, set my voltage free"]
DIVA_BARS = 16                         # 30 s at 128 BPM
LIFT = 3
TAKES_DIR = os.path.join(HERE, "renders", "ace", "takes", "overclocked_heart")


def diva_take(seed):
    """The take for this seed (takes.take: cached by its request, made when missing)."""
    import takes
    return takes.take(DIVA_CAPTION, takes.ace_words(DIVA_LINES, "Chorus"), BPM, "B minor", DIVA_BARS, seed,
                      TAKES_DIR, "chorus", "en", lift=LIFT)


if os.environ.get("TAKES"):
    for s_ in os.environ["TAKES"].split(","):
        print(diva_take(int(s_)))
    raise SystemExit


def diva(bar, seed=DIVA_SEED, amp=1.0):
    """The diva's whole take from the downbeat of `bar`, uncut, lightly band-limited."""
    if not S.live(bar, DIVA_BARS):
        return
    import takes
    x = e.bandpass(takes.mono(os.environ.get("DIVA_WAV") or DIVA_WAV or diva_take(seed)), 120, 10000)
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * .1
    put("vox", S.at(bar), x, .5, amp, wet=.25, echo=.12)


# ---------------------------------------------------------------- the diva: our own melody (SINGER=ours)
# The free ACE-Step takes did not fit (the user, 13:40: "messy and don't fit with the music"): sung a cappella, ACE
# chose its own key (F minor, D minor, B minor for B minor asked) and never heard the chords. So the melody is ours,
# on the chords (Bm Em A F#, a bar each), two bars a line; ACE-Step may re-sing it (ace.py --mode vocals).
DIVA = os.environ.get("SINGER", "ace")   # SINGER=ours: our diva on the written melody (DIVA is the voice env of parts)
CHORUS = [  # (melody: one token a sixteenth over two bars, "-" holds, "." rests; the words as the voice says them)
    ("F#5 - F#5 - A5 - B5 - - - - - A5 - F#5 - G5 - - - E5 - G5 - - - - - - - - .",
     "o ver clocked heart run ning way too hot"),
    ("E5 - E5 - E5 - C#5 - E5 - A5 - - - G5 - F#5 - E5 - C#5 - - - A#4 - - - - - - .",
     "ev ree time you touch me I give all I've got"),
    ("F#5 - F#5 - A5 - B5 - - - - - A5 - F#5 - G5 - - - - - - - E5 - - - - - - .",
     "o ver clocked heart past the red line"),
    ("A5 - G5 - E5 - - - C#5 - E5 - - - E5 - F#5 - F#5 - E5 - - - C#5 - - - - - - .",
     "nine tee five dee grees and I'm feel ing fine"),
    ("F#5 - F#5 - A5 - B5 - - - - - A5 - F#5 - B5 - B5 - - - A5 - G5 - - - - - - .",
     "o ver clocked heart the fans are scream ing loud"),
    ("E5 - E5 - C#5 - E5 - A5 - - - G5 - E5 - F#5 - - - E5 - C#5 - - - - - - - - .",
     "spin ning out of spec in a dance ing crowd"),
    ("F#5 - F#5 - A5 - B5 - - - - - A5 - F#5 - G5 - - - F#5 - E5 - - - - - - - - .",
     "o ver clocked heart don't you throt tull me"),
    ("E5 - E5 - E5 - E5 - A5 - - - G5 - F#5 - E5 - C#5 - - - C#5 - F#5 - - - - - - .",
     "push me to the lim it set my volt idge free"),
]


def our_chorus(bar, first):
    """Our diva on the chorus melody, a line every two bars from `first`."""
    k = bar - first
    if k % 2 == 0:
        line, words = CHORUS[k // 2]
        P.diva(bar, line, words, bars=2, amp=1.0)


# SINGER=ace (the default): seed 2 (the user's "least bad"), sung by ACE-Step in B minor at 104 BPM (asked for A flat minor) and
# only sped up to 128 by Rubber Band (no pitch shift). The band follows HER in the choruses: a chord a bar, picked
# from the notes she sings in that bar (pyworld's f0, the triad of B minor's chords with the most of them).
DIVA_WAV = os.path.join(TAKES_DIR, "chorus_s2_bm_128.wav") if DIVA_SEED == 2 else None
HARM = ["D", "D", "Bm", "F#", "F#", "Em", "Bm", "Bm", "D", "D", "Bm", "Bm", "D", "D", "Bm", None]
# HARM=1: the band follows her. By ear (the user, 14:00): "the first was nicer", the kit's own chords; so off.
# VAMP=1: a slower harmony under the free take, two chords two bars each (research/toolkit-2026-11-19.md: the
# approved rounds had slower harmony under the take; this take's steady notes are B, D, E and F#)
VAMP = ["Bm9", "Bm9", "Em9", "Em9"] if os.environ.get("VAMP") == "1" else None
if VAMP:
    HARM = VAMP * 4
if DIVA == "ace" and (os.environ.get("HARM", "0") == "1" or VAMP):
    _kit_chord = P.chord

    def _chord(bar):
        for first in (48, 80):
            if 0 <= bar - first < 16 and HARM[bar - first]:
                return HARM[bar - first]
        return _kit_chord(bar)
    P.chord = _chord


# ---------------------------------------------------------------- the narrators
RYAN, LESSAC = "en_US-ryan-high", "en_US-lessac-high"
if os.environ.get("NARRATORS"):        # "voice|voice": other narrators, e.g. qwen: or maya: voices (an A/B)
    RYAN, LESSAC = os.environ["NARRATORS"].split("|")


def say(bar, text, voice, amp=1.0, beat=0.0):
    """A narrator: plain speech at its own pace, clean."""
    if not S.live(bar, 2):
        return
    y = V._finish(V.tts(text, voice))
    put("vox", S.at(bar, beat), y * (.14 / (np.sqrt(np.mean(y ** 2)) + 1e-9)), .5, amp, wet=.12, echo=.15)


VERSE = {32: ("She was running at stock speed.", LESSAC), 34: ("Factory settings. Nice and cool.", RYAN),
         36: ("Then you walked onto the dance floor.", LESSAC), 38: ("Her clock went up.", RYAN),
         40: ("And up.", LESSAC), 42: ("And up.", RYAN),
         44: ("Nobody had checked the cooling.", LESSAC), 46: ("Nobody ever does.", RYAN)}
BREAK = {64: ("Warning.", LESSAC), 65: ("Core temperature: ninety-five degrees.", LESSAC),
         68: ("Throttling?", RYAN), 70: ("Never.", LESSAC)}


def chorus(bar, last=False):
    """The kit's chorus without its lead line: the diva sings there."""
    kits.hinrg_drums(S, P, bar, crash=bar % 8 == 0, pew=bar % 4 == 3)
    kits.hinrg_bass(S, P, bar, 1.0, cut=1200)
    kits.hinrg_stabs(S, P, bar, 1.0, cut=6000, hit=bar % 4 == 0 or (last and bar % 2 == 0))
    P.pad(bar, 1.0, cut=2800)


# ---------------------------------------------------------------- the arrangement
for bar in range(BARS):
    if bar < 16 or bar >= 96:                                          # the DJ's drums
        kits.hinrg_drums(S, P, bar, crash=bar in (0, 96))
    elif bar < 32:                                                     # the bass, then the stabs
        kits.play("hi-nrg", S, P, bar, "intro")
        if bar >= 24:
            kits.hinrg_stabs(S, P, bar, .5 + .05 * (bar - 24), cut=1500 + 300 * (bar - 24))
    elif bar < 48:                                                     # the verse: the narrators
        kits.play("hi-nrg", S, P, bar, "verse")
        if bar in VERSE:
            say(bar, *VERSE[bar])
    elif bar < 64 or 80 <= bar < 96:                                   # the chorus: the diva's whole take
        chorus(bar, last=bar >= 80)
        if DIVA == "ace" and bar in (48, 80):
            diva(bar + DIVA_OFFSET)
        elif DIVA == "ours":
            our_chorus(bar, 48 if bar < 64 else 80)
    elif bar < 72:                                                     # the break: no kick, the warning
        kits.play("hi-nrg", S, P, bar, "break")
        if bar in BREAK:
            say(bar, *BREAK[bar], amp=1.1)
    else:                                                              # the build: the fans spin up
        kits.hinrg_drums(S, P, bar, kick=bar < 78, pew=bar % 2 == 1)
        kits.hinrg_bass(S, P, bar, .9, cut=900 * 2 ** ((bar - 72) / 4))
        kits.hinrg_stabs(S, P, bar, .8, cut=3000 + 500 * (bar - 72))
        P.pad(bar, 1.1, cut=1800 + 200 * (bar - 72))

P.roll(76, 4)
put("fx", S.at(72), e.riser(S.bar * 8, .35), .5, wet=.3)
put("fx", S.at(64), e.downlifter(S.bar * 2, .3), .5, wet=.3)
put("fx", S.at(28), e.riser(S.bar * 4, .25), .5, wet=.3)
P.finish()
NAME = f"overclocked-heart_{BPM}bpm_{KEY}"
S.mixdown(parts.out_path(NAME), dict(KIT["mix"], vox=1.3), room=.2, echo_mix=.35, lufs=LUFS,
          ir=room.impulse_response(*KIT["room"]))
print(f"share.SONGS row: (\"{NAME}.wav\", \"{TITLE}\", \"{DAY}\", {BPM}, \"{KEY}\", {BARS}),")
