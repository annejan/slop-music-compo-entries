#!/usr/bin/env python3
"""Rubber Duck: disco, 120 BPM, D minor. The second song of the disco practice round (18 November; the user asked
for this pitch too), built in short rounds with the user listening on a phone.

rubber_duck.py [OUT.wav]           PREVIEW=32-48 rubber_duck.py: only bars 32 to 47, for a quick listen
TAKES=1,2,3 rubber_duck.py         make the diva's ACE-Step takes (seeds 1, 2, 3) and stop

Rubber duck debugging as a disco love song: you tell the duck your bug and find it yourself. The diva (ACE-Step's own
take, played whole) sings "Talk to the duck, baby", the room answers "Quack! Quack!", and in the break the penny
drops: "And then I said it out loud... oh. OH."

  bars   0-15  intro: the disco drums alone (for the DJ)
        16-31  the octave bass, the strings, the guitar; the room teases the hook
        32-47  A: the diva's chorus (8 bars, her whole take), then the room's "Quack!" with the horns
        48-63  the verse: two narrators and a bug; the room from 56
        64-71  the break: no kick, the strings; explaining it to the duck... "and then... oh." The room: "Oh!"
        72-79  the build: the room faster, a snare roll, a riser
        80-95  the last chorus: her take again, the horns, the room
        96-111 outro: the drums alone (for the DJ)
"""
import json
import os

import numpy as np

import engine as e
import parts
import room
import voice as V

# ---------------------------------------------------------------- the knobs
TITLE = "Rubber Duck"
DAY = "Rehearsal: disco"
BPM, BARS = 120, 112
KEY = "Dm"
KEY_CHANGE = 0
PROG = ["Dm", "Dm", "G", "G"]          # the dorian vamp: two bars each
LUFS = -10.0
GROOVE = parts.GROOVES["disco"]
DIVA_SEED = int(os.environ.get("DIVA_SEED", "1"))

e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)
ST, SR = S.step, e.SR
put = S.put
P = parts.Band(S, PROG, scale="minor")
HERE = os.path.dirname(os.path.abspath(__file__))
TAKES_DIR = os.path.join(HERE, "renders", "ace", "rubber_duck")

# ---------------------------------------------------------------- the diva: ACE-Step's own take, played whole
DIVA_REQUEST = {"caption": "late 1970s disco, a soulful female diva, warm and playful, soaring, a cappella vocals only, "
                           "no instruments",
                "lyrics": "[Chorus]\nTalk to the duck, baby\nTell it all night long\nTalk to the duck, baby\nTell it "
                          "where it all went wrong\n",
                "bpm": BPM, "keyscale": "D minor", "timesignature": "4", "vocal_language": "en",
                "output_format": "wav16", "duration": 16,
                "synth_model": "acestep-v15-sft-Q8_0.gguf", "inference_steps": 50, "guidance_scale": 1.0, "shift": 1.0,
                "lm_model": "acestep-5Hz-lm-4B-Q8_0.gguf"}


def diva_take(seed):
    """The take for this seed: made from DIVA_REQUEST when missing (the same seed gives the same audio)."""
    import ace
    wav = os.path.join(TAKES_DIR, f"diva_s{seed}.wav")
    if not os.path.exists(wav):
        os.makedirs(TAKES_DIR, exist_ok=True)
        base = os.path.join(TAKES_DIR, f"diva_s{seed}")
        json.dump(dict(DIVA_REQUEST, seed=seed), open(base + ".json", "w"), indent=1)
        ace.run([os.path.join(ace.ACESTEP, "build", "ace-lm"), "--models", ace.MODELS, "--request", base + ".json",
                 "--device", "Vulkan0"], base + ".lm.log")
        ace.run([os.path.join(ace.ACESTEP, "build", "ace-synth"), "--models", ace.MODELS, "--request", base + "0.json",
                 "--device", "Vulkan0", "--vae-chunk", "512"], base + ".synth.log")
        os.replace(base + "00.wav", wav)
    return wav


if os.environ.get("TAKES"):
    for s_ in os.environ["TAKES"].split(","):
        print(diva_take(int(s_)))
    raise SystemExit


def diva(bar, seed=DIVA_SEED, amp=.9):
    """Her whole take from the downbeat of `bar`, uncut, lightly band-limited."""
    if not S.live(bar, 8):
        return
    from math import gcd
    from scipy import signal as sg
    import master
    x, sr = master.read(diva_take(seed))
    x = x.mean(1)
    if sr != SR:
        g = gcd(SR, sr)
        x = sg.resample_poly(x, SR // g, sr // g)
    x = e.bandpass(x, 110, 9000)
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * .1
    put("vox", S.at(bar), x, .5, amp, wet=.22, echo=.08)


# ---------------------------------------------------------------- the room and the band's extras
_takes = {}


def shout(text, secs, voice, pitch):
    k = (text, round(secs, 4), voice, pitch)
    if k not in _takes:
        _takes[k] = V.rap(text, secs, voice=voice, pitch=pitch)
    return _takes[k]


GANG = [("en_US-joe-medium", .2), ("en_US-john-medium", .8), ("en_US-amy-medium", .35),
        ("en_US-kristin-medium", .65), ("en_US-bryce-medium", .5)]


def room_call(bar, beat=0.0, amp=1.0):
    """The room: "Quack!", a little apart in time and pitch."""
    if not S.live(bar):
        return
    for i, (v, pan) in enumerate(GANG):
        put("vox", S.at(bar, beat) + .007 * i - .014, shout("Quack!", 1.0 * S.beat, v, .95 + .05 * i), pan,
            .42 * amp, wet=.18, echo=.06)


def wah(bar, amp=1.0):
    """The disco guitar: muted chords on the sixteenths' offbeats, a wah that opens and closes."""
    if not S.live(bar):
        return
    notes = {"Dm": [57, 60, 62, 65], "G": [55, 59, 62, 65]}[PROG[bar % 4]]
    for k in (1, 3, 5, 7, 9, 11, 13, 15):
        t = np.arange(int(ST * 1.2 * SR)) / SR
        g = sum(e.pulse(e.hz(m), t, .3) for m in notes) / 4 * np.exp(-t * 22) * (1 - np.exp(-t * 900))
        c = 700 + 1300 * (.5 + .5 * np.sin(2 * np.pi * k / 16))
        put("keys", S.at(bar) + k * ST, np.tanh(2 * e.bandpass(g, c * .6, c * 1.6)), .3 if k % 4 == 1 else .7,
            .35 * amp, wet=.08)


HORNS = "D5 - . D5 F5 - . . A5 - G5 - F5 - . ."


def horns(bar, amp=1.0):
    """The horn section: a stab line on the DX7 brass."""
    if not S.live(bar):
        return
    P.lead(bar, HORNS, amp=.75 * amp, sound="brass")


RYAN, LESSAC = "en_US-ryan-high", "en_US-lessac-high"        # the two dry narrators, taking turns


def mc(bar, text, voice, amp=1.0, beat=0.0):
    """A narrator: plain speech at its own pace, clean."""
    if not S.live(bar, 2):
        return
    y = V._finish(V.tts(text, voice))
    put("vox", S.at(bar, beat), y * (.14 / (np.sqrt(np.mean(y ** 2)) + 1e-9)), .5, amp, wet=.1, echo=.12)


def gasp(bar, beat=0.0, word="Ooh!", amp=.8):
    """The room, all together, one word."""
    if not S.live(bar):
        return
    for i, (v, pan) in enumerate(GANG):
        put("vox", S.at(bar, beat) + .009 * i - .02, shout(word, 1.2 * S.beat, v, 1.0 + .04 * i), pan, .4 * amp,
            wet=.25, echo=.05)


LINES = {48: ("It worked on my machine.", RYAN), 50: ("Did you try turning it off and on again?", LESSAC),
         52: ("I have been staring at this for six hours.", RYAN), 54: ("Have you tried explaining it to the duck?", LESSAC)}
BREAK = {64: ("So, the function takes the list...", RYAN, 0.0), 66: ("and then it loops...", RYAN, 0.0),
         68: ("and then... oh.", RYAN, 0.0), 70: ("Oh!", LESSAC, 0.0)}
GASPS = {69: "Oh!", 70: "Quack!"}

# ---------------------------------------------------------------- the arrangement
for bar in range(BARS):
    intro, outro = bar < 16, bar >= 96
    P.drums(bar, GROOVE, crash=bar in (0, 16, 32, 40, 48, 80, 88), kick=not 64 <= bar < 76)
    if intro or outro:
        continue
    brk = 64 <= bar < 72
    if not brk:
        P.bass(bar, "octave", amp=.8 if bar < 20 else 1.0)
    P.pad(bar, 1.3 if brk else .8 if bar < 32 else 1.0)
    if not brk:
        wah(bar, .8 if bar < 24 else 1.0)
    if 16 <= bar < 32:
        if bar in (24, 28):
            room_call(bar, 0, .8)
            room_call(bar, 2, .8)
        if bar >= 28:
            horns(bar, .7)
    if 32 <= bar < 48:
        if bar == 32:
            diva(bar)                                                  # her whole take, 32-39
        if bar >= 40:
            horns(bar)
            if bar % 2 == 0:
                room_call(bar, 0)
                room_call(bar, 2)

    if 48 <= bar < 64:                                                 # the verse: the narrators
        horns(bar, .6) if bar >= 56 else None
        if bar in LINES:
            mc(bar, LINES[bar][0], LINES[bar][1])
        if bar >= 56 and bar % 2 == 0:
            room_call(bar, 0)
            room_call(bar, 2)
    if 64 <= bar < 72:                                                 # the break: no kick, the strings, the story
        for b, (text, voice, beat) in BREAK.items():
            if bar == b:
                mc(bar, text, voice, 1.1, beat)
        if bar in GASPS:
            gasp(bar, 2, GASPS[bar])
    if 72 <= bar < 80:                                                 # the build: the room, faster
        horns(bar, .5 + .06 * (bar - 72))
        n = 2 if bar < 76 else 4
        for b in range(0, 4, 4 // n):
            room_call(bar, b, .7 + .05 * (bar - 72))
    if 80 <= bar < 96:                                                 # the last chorus: her again, the horns, the room
        horns(bar)
        if bar == 80:
            diva(bar, amp=1.0)
        if bar >= 88 and bar % 2 == 0:
            room_call(bar, 0)
            room_call(bar, 2)

P.roll(76, 4)
S.put("fx", S.at(76), e.riser(S.bar * 4, .35), .5, wet=.3)
S.put("fx", S.at(64), e.downlifter(S.bar * 2, .3), .5, wet=.3)
S.put("fx", S.at(28), e.riser(S.bar * 4, .3), .5, wet=.3)
NAME = f"rubber-duck_{BPM}bpm_{KEY}"
S.mixdown(parts.out_path(NAME), {"drums": .95, "perc": .7, "bass": .9, "pads": .75, "keys": .8, "lead": .7,
                                 "vox": 1.3, "fx": .5},
          room=.2, echo_mix=.35, lufs=LUFS, ir=room.impulse_response((9.0, 6.0, 3.5), rt60=1.4))
print(f"share.SONGS row: (\"{NAME}.wav\", \"{TITLE}\", \"{DAY}\", {BPM}, \"{KEY}\", {BARS}),")
