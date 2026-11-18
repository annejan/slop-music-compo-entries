#!/usr/bin/env python3
"""TEMPLATE: the start of a new song for a surprise theme. Copy it (cp template.py my_song.py), set the knobs
below, write the words and the melody, and shape the arrangement. It renders as it is, as a test.

template.py [OUT.wav]          PREVIEW=48-64 template.py: only bars 48 to 63, for a quick listen

For the rest of the route, add one line for the song to share.SONGS (render name, title, day, BPM, key, bars) and
write its lyric sheet in lyrics/: then ace.py (ACE-Step), share.py (MP3s) and dj.py (the USB stick) know it.

  bars   0-15  intro: drums only (for the DJ)
        16-31  the band comes in
        32-47  verse (diva) and rap
        48-63  chorus with the choir
        64-71  break: no kick, a spoken line
        72-79  build: snare roll, riser
        80-95  last chorus, a key change up, the big choir
        96-111 outro: drums only (for the DJ)
"""
import engine as e
import parts
import room

# ---------------------------------------------------------------- the knobs
TITLE = "template"
BPM, BARS = 128, 112
PROG = ["Am", "F", "C", "G"]           # one chord a bar, repeating
SCALE = "minor"                        # minor | major (for the choir's thirds)
GROOVE = parts.GROOVES["four"]         # see parts.GROOVES, or a dict of your own
BASS = "offbeat"                       # offbeat | root | eighths | reese | dx7
KEYS = "piano"                         # piano | epiano | organ | supersaw
LUFS = -9.0                            # -10 for mellow, -9 for loud
KEY_CHANGE = 2                         # semitones up for the last chorus (0: none)
DIVA, RAPPER = "en_US-amy-medium", "en_US-joe-medium"

CHORUS = [  # (melody: one token per note, "-" holds, "." rests; the words as the voice should say them)
    ("E5 - E5 - - - D5 - C5 - E5 - - - - -", "this + is a test"),
    ("D5 - C5 - A4 - - - C5 - - - - - - .", "of the temp late"),
    ("E5 - G5 - - - E5 - D5 - C5 - - - - -", "this + is a test"),
    ("D5 - D5 - - - B4 - C5 - - - - - - .", "it ren ders great"),
]
VERSE = [(". C5 C5 C5 B4 C5 D5 E5 - D5 C5 - - . . .", "set the knobs and then write all the words"),
         (". E5 E5 E5 D5 - C5 - D5 C5 - A4 - - . .", "and then the song will sing it self")]
RAP = ["Copy the template, give it a name,", "change all the numbers, it is not the same.",
       "Write me a hook and a melody line,", "render it twice and it sounds just fine."]

# ---------------------------------------------------------------- the song
e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)


def key_of(bar):
    return KEY_CHANGE if 80 <= bar < 96 else 0


P = parts.Band(S, PROG, scale=SCALE, key_of=key_of, diva_voice=DIVA, rapper_voice=RAPPER)

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
        P.bass(bar, BASS, amp=.7 if bar < 24 or build else 1.0)
    if 24 <= bar < 96 and not brk:
        P.stabs(bar, sound=KEYS, amp=.8 if chorus else 1.0)
    if 16 <= bar < 96:
        P.pad(bar, 1.2 if brk or build else 1.0)

    if 32 <= bar < 40 and bar % 2 == 0:
        P.diva(bar, *VERSE[(bar - 32) // 2 % 2], bars=2, amp=.9)
    if 40 <= bar < 48:
        P.rap(bar, RAP[(bar - 40) % 4])
    if chorus:
        line, words = CHORUS[bar % 4]
        P.diva(bar, line, words, choir=.37, big=bar >= 80)
        P.lead(bar, line, amp=.6)
    if bar == 64:
        P.say(bar, "This is the break. Nothing to see here.", phone=True)

P.roll(76, 4)
S.put("fx", S.at(76), e.riser(S.bar * 4, .4), .5, wet=.3)
S.put("fx", S.at(64), e.downlifter(S.bar * 2, .3), .5, wet=.3)

cut = [(0, 18000), (S.at(64), 18000), (S.at(64) + .05, 2500), (S.at(72), 2500), (S.at(80) - .02, 12000),
       (S.at(80), 18000), (S.n / e.SR, 18000)]   # the master filter: closed in the break
S.mixdown(parts.out_path(f"{TITLE}_{BPM}bpm"), {"drums": .95, "perc": .7, "bass": .85, "pads": .8, "keys": 1.0,
                                                 "lead": 1.0, "vox": 1.4, "fx": .55},
          cut_keys=cut, room=.2, echo_mix=.4, lufs=LUFS, ir=room.impulse_response((9.0, 6.0, 3.5), rt60=1.6))
