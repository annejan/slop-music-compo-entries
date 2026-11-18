#!/usr/bin/env python3
"""S.D.I.O. (I Love You So): the surprise-theme rehearsal, Italo disco (theme drawn at 11:52:39). The ESP32-P4 and
the ESP32-C6 on one Tanmatsu are in love over the six SDIO wires (ESP-Hosted, 4-bit: CLK, CMD, D0-D3). He has the
screen, the keys and Doom, but he cannot hear the sky; she hears all the WiFi and Bluetooth, but when someone opens
her ttyACM she resets and he crashes with her. In the break he flashes her over UART, "heart to heart", while the
launcher's real radio-update dialogs read out.

sdio_love.py [OUT.wav]          PREVIEW=48-64 sdio_love.py: only bars 48 to 63, for a quick listen

  bars   0-15  intro: the drum machine only (for the DJ)
        16-23  octave bass and pad
        24-31  DX7 e-piano stabs; the hook on DX7 bells, the vocoder robot spells it
        32-39  verse: HIM (the P4)
        40-47  verse: HER (the C6)
        48-63  chorus (x2): his letters, her answers, the choir
        64-71  break: no kick, the filter closed; the radio update, "heart to heart, over UART"
        72-79  build: the update's dialogs, snare roll, riser
        80-95  last chorus, up a tone to E minor, the big choir
        96-111 outro: the drum machine only (for the DJ)
"""
import os

import engine as e
import parts
import room

# ---------------------------------------------------------------- the knobs
TITLE = "sdio-love"
BPM, BARS = 120, 112                   # 3:46 with the reverb tail, one bar = 2 s
PROG = ["Dm", "Bb", "F", "C"]          # i-VI-III-VII, the dreamy Italo loop
SCALE = "minor"
GROOVE = parts.GROOVES["techno"]       # the LinnDrum/DMX disco machine: 4/4 kick, clap on 2 and 4, 16th hats
BASS = "eighths"                       # only the fallback: octave_bass() below
KEYS = "epiano"                        # DX7
LUFS = -10.0
KEY_CHANGE = 2                         # the last chorus in E minor
DIVA = os.environ.get("DIVA", "en_US-amy-medium")    # HER, the C6
HIM = "en_GB-alan-medium"              # the P4: always octave=-24, an octave under her. Ryan alone: 7 of 39 words
                                       # of his verse heard; Alan 32, Bryce 30, John 30, Joe 14, Norman 5
RAPPER = "en_US-joe-medium"            # unused: Italo has no rap, her verse takes the rap slot

# One token is a sixteenth. CHORUS: one bar a line. VERSE, VERSE2: two bars a line (32 tokens).
CHORUS = [  # CHORUS[bar % 8]. Lines 0 and 4 are HIM, the rest are HER.
    ("A5 - - - A5 - - - G5 - - - F5 - - -", "S! D! I! O!"),                 # Dm  HIM
    (". . F5 - G5 - A5 - - - Bb5 - - A5 - .", "I love you so +"),           # Bb  HER ("so" falls Bb to A)
    ("A5 - - - G5 - F5 - G5 - - - - - - .", "six lit tul wires"),           # F   HER
    (". . G5 - A5 - - - G5 - E5 - - - - .", "from me to you"),              # C   HER
    ("A5 - - - A5 - - - C6 - - - D6 - - -", "S! D! I! O!"),                 # Dm  HIM (climbs the second time)
    (". . F5 - G5 - A5 - - - Bb5 - - A5 - .", "don't let me go +"),         # Bb  HER
    ("A5 - A5 - G5 - A5 - - - G5 - F5 - - -", "I am your ray dee oh"),      # F   HER
    (". . G5 - A5 - - - G5 - E5 - - - - .", "your ray dee oh"),             # C   HER
]
VERSE = [  # HIM, bars 32-39
    (". . . . D5 - F5 - A5 - - - G5 - - - F5 - F5 - G5 - F5 - - - - - - - . .", "I'm the P! four I've got the keys"),
    (". . C5 - F5 - F5 - A5 - - - G5 - F5 - G5 - - - F5 - E5 - - - - - - - . .", "I run the lawn chur and Doom with ease"),
    (". . . . D5 - F5 - A5 - - - G5 - - - A5 - C6 - - - A5 - F5 - - - - - . .", "but I can't hear the sky oh no"),
    (". . . . C5 - F5 - F5 - A5 - - - G5 - G5 - - - G5 - - - F5 - - - E5 - - -", "un til you wiss per S! D! I! O!"),
]
VERSE2 = [  # HER, bars 40-47 (in place of the rap)
    (". . . . D5 - F5 - A5 - - - G5 - - - F5 - F5 - G5 - F5 - - - - - - - . .", "I'm the C! six I've got the air"),
    ("A5 - - - G5 - F5 - A5 - - - G5 - - - E5 - F5 - G5 - - - - - - - - - . .", "why fye and blue tooth ev ree where"),
    (". . D5 - F5 - F5 - A5 - - - G5 - F5 - D5 - - - F5 - - - Bb5 - - - . . . .", "but when they o pen my T! T! Y!"),
    ("A5 - C6 - - - A5 - G5 - - - F5 - G5 - E5 - - - D5 - - - C5 - - - - - . .", "I go to sleep and you crash bye bye"),
]

# ---------------------------------------------------------------- the song
e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)


def key_of(bar):
    return KEY_CHANGE if 80 <= bar < 96 else 0


P = parts.Band(S, PROG, scale=SCALE, key_of=key_of, diva_voice=DIVA, rapper_voice=RAPPER)


def octave_bass(bar, amp=1.0):
    """The Italo gallop: eighths, the root on the beat, the octave on the "and"."""
    root = e.root_note(P.chord(bar), key_of(bar), lo=33)
    for k in range(0, 16, 2):
        S.put("bass", S.at(bar) + k * S.step,
              e.bass_note(root + 12 * (k % 4 == 2), S.step * 1.6, cut=1400, decay=3), .5, .9 * amp, wet=0)


def chorus_line(bar):
    """His letters with the choir an octave above him (at her octave), or her line with the choir."""
    line, words = CHORUS[bar % 8]
    if bar % 4 == 0:   # his letters a little louder, and no lead synth on his notes (the mix hid them)
        P.diva(bar, line, words, voice=HIM, octave=-24, amp=1.4)
        P.diva(bar, line, words, amp=.01, choir=15, big=bar >= 80)   # choir only: amp*choir = .15, her at -40 dB
        # (at .37 the choir's vowels hid his letters: in the mix the ear heard "as we all go" for S! D! I! O!)
    else:
        P.diva(bar, line, words, choir=.37, big=bar >= 80)
        P.lead(bar, line, amp=.5)


for bar in range(BARS):
    intro, outro = bar < 16, bar >= 96
    chorus = 48 <= bar < 64 or 80 <= bar < 96
    brk, build = 64 <= bar < 72, 72 <= bar < 80

    if intro or outro:
        P.drums(bar, GROOVE, clap=8 <= bar < 108, crash=bar in (0, 96))
    elif brk:
        P.drums(bar, GROOVE, kick=False, clap=False, amp=.7)
    elif build:
        P.drums(bar, GROOVE, kick=bar < 76, clap=False)
    else:
        P.drums(bar, GROOVE, crash=bar in (32, 48, 80))

    if 16 <= bar < 64 or 72 <= bar < 96:
        octave_bass(bar, amp=.7 if bar < 24 or build else 1.0)
    if 24 <= bar < 96 and not brk:
        P.stabs(bar, steps=(2, 6, 10, 14), sound=KEYS, amp=.6 if chorus else .9)   # offbeats, out of the words' way
    if 16 <= bar < 96:
        P.pad(bar, 1.2 if brk or build else 1.0)

    if 24 <= bar < 32:   # the hook on DX7 bells before anyone sings it; the vocoder robot spells it, in his octave
        P.lead(bar, CHORUS[bar % 8][0], amp=.5, sound="bells")
        if bar in (24, 28):
            hi = bar == 28
            S.sing(S.at(bar), [("", ["e"], 57, S.beat, "s"), ("d", ["i"], 57, S.beat, ""),
                               ("", ["ah", "i"], 60 if hi else 55, S.beat, ""),
                               ("", ["o", "u"], 62 if hi else 53, S.beat, "")], amp=.8)
        if bar == 31:    # the robot sings "ray dee oh" on chorus line 7's tune
            S.sing(S.at(31, 1), [("", ["r", "e", "i"], 57, S.beat, ""), ("d", ["i"], 55, S.beat / 2, ""),
                                 ("", ["o", "u"], 52, S.beat * 1.5, "")], amp=.8)
    if 32 <= bar < 40 and bar % 2 == 0:   # he sits low, in the pad's and the stabs' range: louder than her
        P.diva(bar, *VERSE[(bar - 32) // 2], bars=2, amp=1.3, voice=HIM, octave=-24)
    if 40 <= bar < 48 and bar % 2 == 0:
        P.diva(bar, *VERSE2[(bar - 40) // 2], bars=2, amp=.9)
    if chorus:
        chorus_line(bar)

    if bar == 64:
        P.say(64, "Radio update. Stopping WiFi.", phone=True)
    if bar == 66:
        P.say(66, "Starting updater.", phone=True)
    if bar == 68:
        P.say(68, "Ciao, bella. Heart to heart, over UART.", voice=HIM, amp=.9)   # close and warm, not the phone
    if bar == 70:
        P.diva(70, *CHORUS[0], voice=HIM, octave=-24)   # he sings the letters alone, into the echo
    if bar == 71:
        P.diva(71, *CHORUS[5])                          # she answers alone: "don't let me go"
    if build and bar % 2 == 0:
        P.say(bar, {72: "Synchronizing with radio.", 74: "Detecting radio.", 76: "Erasing.",
                    78: "Radio update completed successfully!"}[bar], phone=True, amp=1.0)

P.roll(76, 4)
S.put("fx", S.at(76), e.riser(S.bar * 4, .4), .5, wet=.3)
S.put("fx", S.at(64), e.downlifter(S.bar * 2, .3), .5, wet=.3)

P.finish()
cut = [(0, 18000), (S.at(64), 18000), (S.at(64) + .05, 2500), (S.at(72), 2500), (S.at(80) - .02, 12000),
       (S.at(80), 18000), (S.n / e.SR, 18000)]   # the master filter: closed in the break
S.mixdown(parts.out_path(f"{TITLE}_{BPM}bpm_Dm"), {"drums": .95, "perc": .7, "bass": .85, "pads": .8, "keys": 1.0,
                                                    "lead": 1.0, "vox": 1.4, "fx": .55},
          cut_keys=cut, room=.2, echo_mix=.4, lufs=LUFS, ir=room.impulse_response((9.0, 6.0, 3.5), rt60=1.6))
