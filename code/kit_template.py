#!/usr/bin/env python3
"""KIT TEMPLATE: the start of a surprise-round song on one of kits.py's 11 genre kits (kits.py --list), the way
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
KIT_NAME = "hi-nrg"                    # kits.py --list: trance, eurobeat, hardstyle, gabber, happy hardcore, ...
TITLE = "Kit Template"
DAY = "Rehearsal: test"                # "Saturday: <genre>" or "Sunday: <genre>": the set it plays in
CHORUS_LEAD = False                    # the kit's lead and hook (its "lead" bus) under the diva: off
DIVA_GAIN = 1.0                        # the diva's level: dense kits need more (happy hardcore 2.5: at 1.0 the
                                       # rehearsal's diva was not heard at all over the band)
VOICE_GAIN = 1.0                       # the spoken lines' level (the rehearsal's MC needed 2.0 over the build)
NARRATOR_A, NARRATOR_B, ANNOUNCER = "cast:narrator", "cast:diva", "cast:announcer"   # voice.CAST roles or names

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
DIVA_OFFSET = int(os.environ.get("DIVA_OFFSET", "0"))   # whole bars: fit.py's offset, -1 earlier, 1 later
HAS_DIVA = os.path.exists(DIVA_WAV)
if not HAS_DIVA:
    print(f"no diva yet: {DIVA_WAV} (pin a take with takes.pin)")

e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)
put = S.put
P = kits.band(KIT_NAME, S)

# ---------------------------------------------------------------- the words (spoken; tags like <excited> reach Maya)
VERSE = {32: ("It started as a normal night.", NARRATOR_A), 34: ("Then the music came on.", NARRATOR_B),
         36: ("Nobody was ready.", NARRATOR_A), 38: ("Nobody ever is.", NARRATOR_B),
         40: ("The lights went down.", NARRATOR_A), 42: ("<excited> And the room went up!", NARRATOR_B)}
BREAK = {66: ("Attention please.", ANNOUNCER), 68: ("This is a test of the template.", ANNOUNCER)}   # from bar 66: the
# first chorus's take may ring into bar 64


def say(bar, text, voice, amp=1.0, beat=0.0):
    """A spoken line at its own pace from `bar` (beat), clean."""
    if not S.live(bar, 2):
        return
    y = V._finish(V.tts(text, voice))
    put("vox", S.at(bar, beat), y * (.14 / (np.sqrt(np.mean(y ** 2)) + 1e-9)), .5, amp * VOICE_GAIN, wet=.12,
        echo=.15)


def diva(bar, limit, amp=1.0):
    """The pinned ACE-Step take, whole, from the downbeat of `bar`, lightly band-limited, DIVA_GAIN louder; cut
    with an 80 ms fade at the quietest 50 ms of the bar before `limit` if it would run past it (drafts are made
    2 s longer than their bars, and the DJ's outro from bar 96 must stay drums only)."""
    if not HAS_DIVA or not S.live(bar, DIVA_BARS):
        return
    import takes
    x = e.bandpass(takes.mono(DIVA_WAV), 120, 10000)
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * .1 * DIVA_GAIN
    n = int((limit - bar) * S.bar * e.SR)
    if len(x) > n:
        a, w = max(0, n - int(S.bar * e.SR)), int(.05 * e.SR)
        env = np.convolve(np.abs(x[a:n]), np.ones(w) / w, "valid")
        cut = a + int(np.argmin(env)) + w // 2 if len(env) else n
        f = min(int(.08 * e.SR), cut)
        x = x[:cut].copy()
        x[len(x) - f:] *= np.linspace(1, 0, f)
    put("vox", S.at(bar), x, .5, amp, wet=.25, echo=.12)


def chorus(bar):
    """The kit's chorus; its "lead" bus (the lead line or hook of every kit: trance, Hi-NRG, happy hardcore,
    eurobeat, ...) stays out while the diva sings, unless CHORUS_LEAD."""
    if HAS_DIVA and not CHORUS_LEAD:
        put0 = S.put
        S.put = lambda bus, *a, **k: None if bus == "lead" else put0(bus, *a, **k)
        try:
            kits.play(KIT_NAME, S, P, bar, "chorus")
        finally:
            del S.put                  # back to the Song's own put
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
        if bar in (48, 80):
            diva(bar + DIVA_OFFSET, limit=65 if bar == 48 else 96)
    elif bar < 72:
        kits.play(KIT_NAME, S, P, bar, "break")
        if bar in BREAK:
            say(bar, *BREAK[bar], amp=1.1)
    else:                                                              # the build
        kits.play(KIT_NAME, S, P, bar, "verse")

P.roll(76, 4)
put("fx", S.at(72), e.riser(S.bar * 8, .35), .5, wet=.3)
put("fx", S.at(64), e.downlifter(S.bar * 2, .3), .5, wet=.3)
put("fx", S.at(28), e.riser(S.bar * 4, .25), .5, wet=.3)
P.finish()
S.mixdown(parts.out_path(NAME), dict(KIT["mix"], vox=1.3), room=.2, echo_mix=.35, lufs=LUFS,
          ir=room.impulse_response(*KIT["room"]))
print(f"share.SONGS row: (\"{NAME}.wav\", \"{TITLE}\", \"{DAY}\", {BPM}, \"{KEY}\", {BARS}),")
