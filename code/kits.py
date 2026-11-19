#!/usr/bin/env python3
"""Genre kits for surprise day: for each likely genre (research/surprise-genres.md) a tempo, a key, a chord loop and
the genre's band, one bar at a time, on parts.Band. A new song starts from its kit: call kits.play(name, S, P, bar,
part) in the arrangement loop and add the words, the hook and the shape.

kits.py NAME           a 24-bar sketch: 8 bars of the drums alone, then 16 bars of the whole band:
                       renders/kits/<name>_<BPM>bpm_<KEY>.wav and .mp3
kits.py --list         the kits, their tempo, key and chords
kits.py --all          a sketch of every kit, one after the other

Built on the night of 19 November, one genre at a time; not heard by the user yet when written. Each kit says in
its docstring what makes it the genre, and which sounds of engine.py, parts.py and dx7.py it uses.
"""
import os
import sys

import numpy as np

import dx7
import engine as e
import parts
import room
import share

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "renders", "kits")
MIX = {"drums": .95, "perc": .7, "bass": .9, "pads": .75, "keys": .8, "lead": .7, "vox": 1.2, "fx": .5}
KITS = {}


def kit(name, bpm, key, prog, scale="minor", lufs=-9.0, mix=None, room_size=(9.0, 6.0, 3.5), rt60=1.4):
    """Register a kit: `play(S, P, bar, part)` plays one bar of the band. part: "drums" (the DJ's intro and outro:
    the drums alone), "intro" (the band coming in, thinner), "verse", "chorus" (all of it), "break" (no kick)."""
    def reg(play):
        KITS[name] = dict(bpm=bpm, key=key, prog=prog, scale=scale, lufs=lufs, mix=dict(MIX, **(mix or {})),
                          room=(room_size, rt60), play=play)
        return play
    return reg


def play(name, S, P, bar, part="chorus"):
    KITS[name]["play"](S, P, bar, part)


def band(name, S):
    """The kit's parts.Band for a song S (its chord loop and scale)."""
    k = KITS[name]
    return parts.Band(S, k["prog"], scale=k["scale"])


def sketch(name, bars=24):
    """8 bars of the drums alone, 4 of the intro, 12 of the chorus: the WAV and an MP3."""
    k = KITS[name]
    e.seed(k["bpm"])
    S = e.Song(bpm=k["bpm"], bars=bars)
    P = band(name, S)
    for bar in range(bars):
        k["play"](S, P, bar, "drums" if bar < 8 else "intro" if bar < 12 else "chorus")
    P.finish()
    os.makedirs(OUT, exist_ok=True)
    slug = name.replace(" ", "-")
    wav = os.path.join(OUT, f"{slug}_{k['bpm']}bpm_{k['key']}.wav")
    S.mixdown(wav, k["mix"], room=.2, echo_mix=.35, lufs=k["lufs"], ir=room.impulse_response(*k["room"]))
    mp3 = wav[:-4] + ".mp3"
    share.encode(wav, mp3, ["-metadata", f"title=Kit: {name}", "-metadata", "artist=sunA"], [])
    return mp3


# ---------------------------------------------------------------- the kits (one section per genre, added below)


# ---------------------------------------------------------------- trance
TRANCE_GROOVE = dict(clap="....x.......x...", hat="xoxoxoxoxoxoxoxo", open="..x...x...x...x.")   # kick: trance_drums
TRANCE_GATE = "x.xx.xx.x.xx.x.x"        # the supersaw's gate, 16 steps: x open, o half, . shut
TRANCE_ARP = (0, 1, 2, 3, 4, 3, 2, 1, 0, 2, 3, 5, 4, 3, 2, 1)     # into the chord tones (two octaves), per sixteenth
TRANCE_LEAD = ["D5 - - D5 - - G5 - - F5 - - D5 - - -",           # Gm: 3 + 3 + 3 + 3 + 4 sixteenths, the trance rhythm
               "G5 - - F5 - - Eb5 - - D5 - - Bb4 - - -",         # Eb
               "F5 - - D5 - - F5 - - Bb5 - - A5 - F5 -",         # Bb
               "C5 - - F5 - - A5 - - G5 - - F5 - - -"]           # F


def trance_drums(S, P, bar, kick=True, amp=1.0, crash=False):
    """A 909-style kick tuned to G (49 Hz) on every beat, the clap on 2 and 4, sixteenth hats, open hats on the
    offbeats."""
    if kick and S.live(bar):
        for k in range(0, 16, 4):
            S.kick(S.at(bar) + k * S.step, amp, punch=150, base=49, length=.45, click=.5)
    P.drums(bar, TRANCE_GROOVE, amp=amp, kick=False, crash=crash)


def trance_bass_note(m, d, cut=800):
    """A rolling bass note: saw and sub, a filter that snaps shut, short."""
    t = e.tt(d + .02)
    g = e.saw(e.hz(m), t) * .7 + e.sine(e.hz(m), t) * .8
    g = e.sweep(g, cut * (1 + 3 * np.exp(-t * 40)), .9, 64)
    return g * e.rise(t, .002) * e.gate(t, d, .015)


def trance_bass(S, P, bar, amp=1.0, cut=800):
    """The rolling bass: the root on the three sixteenths after each kick, the offbeat the loudest."""
    if not S.live(bar):
        return
    root = e.root_note(P.chord(bar), P.key_of(bar))
    for k in range(16):
        if k % 4:
            v = (.75, 1.0, .85)[k % 4 - 1]
            S.put("bass", S.at(bar) + k * S.step, trance_bass_note(root, S.step * .8, cut), .5, .45 * v * amp, wet=0)


def trance_gate(S, P, bar, amp=1.0, cut=6000, pattern=TRANCE_GATE):
    """The JP-8000 supersaw chord (seven saws a note, wide), held for the bar and chopped by a 16-step gate."""
    if not S.live(bar):
        return
    notes = e.close_voicing(P.chord(bar), P.key_of(bar), lo=60, hi=74)
    notes = notes + [notes[0] + 12]
    g = e.supersaw(notes, S.bar, spread=.3, voices=7, a=.003, r=.03, cut=cut)
    on, a, r = int(S.step * .72 * e.SR), int(.003 * e.SR), int(.015 * e.SR)
    shape = np.r_[np.linspace(0, 1, a), np.ones(on - a), np.exp(-np.arange(r) / (r / 4))]
    env = np.zeros(len(g))
    for k, c in enumerate(pattern):
        if c in "xo":
            i = int(round(k * S.step * e.SR))
            j = min(i + len(shape), len(env))
            env[i:j] = np.maximum(env[i:j], shape[:j - i] * (1.0 if c == "x" else .6))
    S.put("keys", S.at(bar), g * env[:, None], .5, 1.2 * amp, wet=.3, echo=.15)


def trance_arp(S, P, bar, amp=1.0, cut=5000):
    """A sixteenth arpeggio on the trance pluck (engine.pluck), up and down the chord, left and right."""
    if not S.live(bar):
        return
    notes = e.close_voicing(P.chord(bar), P.key_of(bar), lo=65, hi=77)
    tones = notes + [m + 12 for m in notes]
    for k, i in enumerate(TRANCE_ARP):
        S.put("keys", S.at(bar) + k * S.step, e.pluck(tones[i], S.step * .7, cut=cut), .25 + .5 * (k % 2), .3 * amp,
              wet=.25, echo=.3)


@kit("trance", 138, "Gm", ["Gm", "Eb", "Bb", "F"], scale="minor", lufs=-9.0,
     room_size=(12.0, 9.0, 5.0), rt60=2.4)
def play_trance(S, P, bar, part):
    """Trance at 138 BPM, the late 1990s uplifting kind (Paul van Dyk, Robert Miles). The signature is the JP-8000
    supersaw chord chopped by a 16-step trance gate (trance_gate). Under it: a 909-style kick tuned to G, open hats on
    the offbeats, a rolling bass on the three sixteenths after each kick, a sixteenth pluck arpeggio (engine.pluck)
    on the dotted-eighth echo and a supersaw string pad (parts.Band.pad). The chorus adds the anthem lead
    (engine.lead) in the 3-3-3-3-4 rhythm. The chords go i-VI-III-VII (Gm Eb Bb F), one a bar. The break has no beat:
    the pad, and the gate and the arpeggio behind a filter that opens over 8 bars, as in a breakdown. A big hall."""
    if part == "drums":
        trance_drums(S, P, bar)
    elif part == "intro":
        trance_drums(S, P, bar)
        trance_bass(S, P, bar, .8)
        trance_arp(S, P, bar, .8, cut=1500)
    elif part == "verse":
        trance_drums(S, P, bar)
        trance_bass(S, P, bar)
        trance_arp(S, P, bar, .9, cut=3500)
        trance_gate(S, P, bar, .7, cut=2500)
        P.pad(bar, 1.1)
    elif part == "chorus":
        trance_drums(S, P, bar, crash=bar % 8 == 0)
        trance_bass(S, P, bar)
        trance_arp(S, P, bar, .8, cut=6000)
        trance_gate(S, P, bar, 1.0, cut=7000)
        P.pad(bar, 1.2)
        P.lead(bar, TRANCE_LEAD[bar % 4], 1.8)
    elif part == "break":
        cut = 700 * 2 ** (bar % 8 / 2.5)          # 700 Hz to about 5 kHz over 8 bars
        P.pad(bar, 1.3, cut=1500 + 300 * (bar % 8))
        trance_gate(S, P, bar, .8, cut=cut)
        trance_arp(S, P, bar, .7, cut=cut)


# ---------------------------------------------------------------- eurobeat
EUROBEAT_GROOVE = dict(kick="x...x...x...x...", clap="....x.......x...", hat="xoxoxoxoxoxoxoxo",
                       open="..x...x...x...x.")
EUROBEAT_RIFF = ["C5 - C5 Eb5 - G5 - C6 - Bb5 - G5 Ab5 - G5 -",        # Cm
                 "Eb5 - Eb5 Ab5 - C6 - Eb6 - C6 - Ab5 Bb5 - C6 -",     # Ab
                 "D6 - D6 C6 - Bb5 - F5 - Bb5 - D6 C6 - Bb5 -",        # Bb
                 "B5 - B5 C6 - D6 - B5 - G5 - F5 Eb5 - D5 -"]          # G: B natural, the harmonic minor's pull home


def eurobeat_snare(a=1.0):
    """The gated-reverb snare: the snare, then a burst of room noise that stops dead at 0.18 s."""
    t = e.tt(.2)
    tail = e.lowpass(e.highpass(e.rng.standard_normal(len(t)), 500), 7000) * .35 * np.exp(-t * 3)
    tail *= np.clip((.18 - t) / .006, 0, 1)
    return (e.snare(1.0)[:len(t)] + tail) * a


def eurobeat_drums(S, P, bar, kick=True, amp=1.0, crash=False, fill=False):
    """Four to the floor, the clap and the gated snare on 2 and 4, sixteenth hats, open hats on the offbeats.
    fill: a sixteenth snare run on the last beat (the end of an 8-bar phrase)."""
    P.drums(bar, EUROBEAT_GROOVE, amp=amp, kick=kick, crash=crash)
    if not S.live(bar):
        return
    for k in (4, 12):
        S.put("drums", S.at(bar) + k * S.step, eurobeat_snare(.45 * amp), .5, wet=.15)
    if fill:
        for k in range(13, 16):
            S.put("drums", S.at(bar) + k * S.step, eurobeat_snare((.25 + .1 * (k - 13)) * amp), .45, wet=.2)


def eurobeat_bass_note(m, d, cut=1500):
    """A bright, tight synth bass note: saw, square and sine, a filter blip on the attack."""
    t = e.tt(d + .02)
    g = e.saw(e.hz(m), t) * .5 + e.pulse(e.hz(m), t) * .35 + e.sine(e.hz(m), t) * .7
    g = e.sweep(g, cut * (1 + 2.5 * np.exp(-t * 30)), 1.2, 64)
    return g * e.rise(t, .002) * e.gate(t, d, .02)


def eurobeat_bass(S, P, bar, amp=1.0, cut=1500):
    """The fast octave bass: eighths, the root on the beat and the octave on every "and". The roots from G1 up, so
    the loop moves in small steps (C2 Ab1 Bb1 G1)."""
    if not S.live(bar):
        return
    root = e.root_note(P.chord(bar), P.key_of(bar), lo=31)
    for k in range(0, 16, 2):
        g = eurobeat_bass_note(root + 12 * (k % 4 == 2), S.step * 1.6, cut)
        S.put("bass", S.at(bar) + k * S.step, g, .5, .4 * amp, wet=0)


def eurobeat_brass(m, d, cut=5000):
    """Stereo: the riff's synth brass. Four detuned saws and a square, a scoop up into the note, a filter that swells
    open in 30 ms (the brass player's blat) and closes a little after."""
    t = e.tt(d + .08)
    f = e.hz(m - .4 * np.exp(-t * 50))
    out = np.zeros((len(t), 2))
    for v, det in enumerate((-.1, -.035, .035, .1)):
        out[:, v % 2] += e.saw(f * 2 ** (det / 12), t)
    out += .6 * e.pulse(f, t, .35)[:, None]
    cutoff = cut * (.15 + .85 * (1 - np.exp(-t / .03))) * (.7 + .3 * np.exp(-t * 4))
    for ch in range(2):
        out[:, ch] = e.sweep(out[:, ch], cutoff, 1.1, 64)
    return out * (e.rise(t, .004) * e.gate(t, d, .05))[:, None] * .3


def eurobeat_riff(S, P, bar, amp=1.0, cut=5000, layers=True):
    """The riff, layered: the synth brass, and the DX7 brass an octave under it (layers=False: the synth brass
    alone)."""
    if not S.live(bar):
        return
    for t, m, d in S.notes(bar, EUROBEAT_RIFF[bar % 4], P.key_of(bar)):
        S.put("lead", t, eurobeat_brass(m, d * .9, cut), .5, .55 * amp, wet=.2, echo=.12)
        if layers:
            g = dx7.note("brass", m - 12, d * .9, .9, tail=.15)
            S.put("lead", t, g if cut >= 5000 else e.lowpass(g, cut), .5, .3 * amp, wet=.2)


def ks_string(m, n, loss=.996, bright=6000):
    """A plucked string (Karplus-Strong): a burst of noise around a loop one period long that loses a little each
    time; n samples."""
    N = max(int(round(e.SR / float(e.hz(m)) - .5)), 2)    # the loop's averaging adds half a sample
    x = np.zeros(n)
    x[:N] = e.lowpass(e.rng.standard_normal(N), bright)
    y = np.zeros(n + N + 1)                               # y[k] is at y[k + N + 1]: N + 1 zeros before it
    for i in range(0, n, N):                              # one period per block: each block hears only the ones before
        j = min(i + N, n)
        y[i + N + 1:j + N + 1] = x[i:j] + loss * .5 * (y[i + 1:j + 1] + y[i:j])
    return y[N + 1:]


def eurobeat_guitar(notes, d, mute=True):
    """A distorted electric guitar power chord: plucked strings 4 ms apart (a down stroke), a hard overdrive and the
    band of a guitar speaker. mute: palm-muted, short and dark."""
    t = e.tt(d + .03)
    g = np.zeros(len(t))
    for j, m in enumerate(notes):
        i = int(j * .004 * e.SR)
        g[i:] += ks_string(m, len(t) - i, .99 if mute else .997, 2500 if mute else 6000)
    if mute:
        g = e.lowpass(g * np.exp(-t * 18), 1800)
    g = np.tanh(6 * g / (np.abs(g).max() + 1e-9))
    g = e.peaking(e.lowpass(e.highpass(g, 90), 4500, order=4), 2200, 4.0, 1.2)
    return g * e.gate(t, d, .02) * .25


def eurobeat_guitar_part(S, P, bar, amp=1.0):
    """Two takes of the guitar, hard left and right: the power chord rings on the first sixteenth, palm-muted eighths
    after it."""
    if not S.live(bar):
        return
    r = e.root_note(P.chord(bar), P.key_of(bar), lo=40)
    notes = [r, r + 7, r + 12]
    for side, late in ((.1, 0.0), (.9, .006)):
        for k in range(0, 16, 2):
            g = eurobeat_guitar(notes, S.step * 1.8, mute=k > 0)
            S.put("keys", S.at(bar) + k * S.step + late, g, side, (.75 if k else .95) * amp, wet=.12)


@kit("eurobeat", 155, "Cm", ["Cm", "Ab", "Bb", "G"], scale="minor", lufs=-9.0)
def play_eurobeat(S, P, bar, part):
    """Eurobeat at 155 BPM, the Italian dance music made for Japan (Super Eurobeat, Initial D: Dave Rodgers, Max
    Coveri). The signature is the fast, dramatic riff on layered synth brass (eurobeat_brass with the DX7 brass an
    octave under it), the chords i-VI-VII-V in C minor (Cm Ab Bb G) with the major V, and the fast octave bass on the
    eighths. The mid-1990s electric guitar plays power chords (Karplus-Strong strings through an overdrive), two
    takes left and right. The drums: four to the floor, the clap and a gated-reverb snare on 2 and 4, open hats on the
    offbeats, a snare run at the end of each 8 bars. The verse leaves the riff out for the singer; the break is the
    string pad and the riff behind a low filter."""
    if part == "drums":
        eurobeat_drums(S, P, bar)
    elif part == "intro":
        eurobeat_drums(S, P, bar)
        eurobeat_bass(S, P, bar, .8)
        eurobeat_riff(S, P, bar, .8, cut=1800, layers=False)
    elif part == "verse":
        eurobeat_drums(S, P, bar, fill=bar % 8 == 7)
        eurobeat_bass(S, P, bar)
        eurobeat_guitar_part(S, P, bar, .7)
        P.pad(bar, 1.0)
    elif part == "chorus":
        eurobeat_drums(S, P, bar, crash=bar % 8 == 0, fill=bar % 8 == 7)
        eurobeat_bass(S, P, bar)
        eurobeat_guitar_part(S, P, bar)
        eurobeat_riff(S, P, bar)
        P.pad(bar, 1.1)
    elif part == "break":
        P.pad(bar, 1.4, cut=2000)
        eurobeat_riff(S, P, bar, .8, cut=1200)


# ---------------------------------------------------------------- hardstyle
HARDSTYLE_GROOVE = dict(hat="..x...x...x...x.", open="..x...x...x...x.")    # kick: hardstyle_kick; clap: own
HARDSTYLE_LEAD = ["C#5 - - C#5 - - F#5 - - A5 - - G#5 - F#5 -",       # F#m: 3 + 3 + 3 + 3 + 2 + 2 sixteenths
                  "A5 - - A5 - - F#5 - - D5 - - E5 - F#5 -",          # D
                  "E5 - - E5 - - A5 - - C#6 - - B5 - A5 -",           # A
                  "B5 - - G#5 - - E5 - - G#5 - - B5 - - -"]           # E: B5 glides down to the C#5 of the next bar
HARDSTYLE_DRIFT = (0, .7, -.4, 1.0, -.9, .3, -.7, .5)    # the kick's sweep, faster or slower by up to 10 %, per beat
_HARDSTYLE_KICKS = {}


def hardstyle_kick(m, d, drift=0.0):
    """The hardstyle kick, d seconds: a 909-style sweep from 11 times the note down to it (the punch, about 80 ms),
    then the tail on the note itself. All of it driven hard into tanh, a little lopsided (even harmonics), so the
    tail rings as a distorted, pitched tone; a click on top. The tail falls to a third and fades out in its last 10 ms,
    where the reverse bass fades in. drift (-1 to 1): the sweep 10 % faster or slower, as an analog drum machine
    drifts. Identical hits would also line up the ripples inside the distorted tail, beat after beat, and the beat
    finder (master.beat_phase) would take them for the beat. Made once per note, length and drift."""
    if (m, d, drift) not in _HARDSTYLE_KICKS:
        t = e.tt(d)
        f = e.hz(m) * (1 + 9 * np.exp(-t * 110 * (1 + .1 * drift)) + 1.2 * np.exp(-t * 40 * (1 + .1 * drift)))
        x = np.sin(2 * np.pi * np.cumsum(f) / e.SR) * np.exp(-t * 5)
        g = np.tanh(7 * (x + .2 * x ** 2))
        g = g + e.bandpass(e.rng.standard_normal(len(t)), 1500, 7000) * np.exp(-t * 400) * .8
        g = e.peaking(e.lowpass(e.highpass(g, 30), 6000), 1200, -4.0, .7)     # a little less of the harsh middle
        g *= (1 - .65 * (t / d) ** 1.5) * np.clip((d - t) / .01, 0, 1)
        _HARDSTYLE_KICKS[(m, d, drift)] = g / np.abs(g).max()
    return _HARDSTYLE_KICKS[(m, d, drift)]


def hardstyle_reverse_bass(m, d):
    """The reverse bass: a kick's tail played backwards, on the chord's root. It fades in over 10 ms at a fifth of its
    level (under the kick's tail, so there is no gap between them), swells, sweeps up in its last 30 ms and stops
    dead."""
    t = e.tt(d)
    r = d - t                                                  # the time left to the next kick
    f = e.hz(m) * (1 + 1.5 * np.exp(-r * 70))
    x = np.sin(2 * np.pi * np.cumsum(f) / e.SR) * np.exp(-r * 8)
    g = np.tanh(5 * (x + .2 * x ** 2)) * (.2 + .8 * (t / d) ** 1.5)
    g = e.lowpass(e.highpass(g, 30), 3500)
    return g * np.clip(r / .004, 0, 1) * np.clip(t / .01, 0, 1)


def hardstyle_clap(a=1.0):
    """Stereo: the big hardstyle clap, three claps at once (each its own noise), left, middle and right. Not one after
    the other: a flam would blur the beat."""
    out = np.zeros((len(e.clap()), 2))
    for pan in (.15, .5, .85):
        c = e.clap(1.0)
        out[:, 0] += c * np.cos(pan * np.pi / 2)
        out[:, 1] += c * np.sin(pan * np.pi / 2)
    return e.highpass(out, 350) * a * .6


def hardstyle_drums(S, P, bar, amp=1.0, crash=False, clap=True):
    """The kick on every beat, tuned to the key's root (F#1, 46 Hz), an eighth long: the reverse bass has the rest of
    the beat. The big clap on 2 and 4, hats on the offbeats."""
    if not S.live(bar):
        return
    m = e.root_note(P.prog[0], P.key_of(bar), lo=30)
    for k in range(0, 16, 4):
        t = S.at(bar) + k * S.step
        g = hardstyle_kick(m, round(2 * S.step, 4), HARDSTYLE_DRIFT[(4 * bar + k // 4) % 8])
        S.put("drums", t, g, .5, amp, wet=0)
        S.kicks.append(t)
    if clap:
        for k in (4, 12):
            S.put("drums", S.at(bar) + k * S.step, hardstyle_clap(.8 * amp), .5, wet=.35)
    P.drums(bar, HARDSTYLE_GROOVE, amp=amp, kick=False, clap=False, crash=crash)


def hardstyle_bass(S, P, bar, amp=1.0):
    """The reverse bass on the chord's root (F#1 to E2), from 10 ms before each offbeat eighth (under the kick's
    fading tail) to 12 ms before the next kick: the gap lets the kick start from quiet, so its attack (and the beat
    grid) stays clear."""
    if not S.live(bar):
        return
    m = e.root_note(P.chord(bar), P.key_of(bar), lo=29)
    for k in (2, 6, 10, 14):
        S.put("bass", S.at(bar) + k * S.step - .01, hardstyle_reverse_bass(m, 2 * S.step - .002), .5, .55 * amp,
              wet=0)


def hardstyle_lead_note(m0, m, d, cut=8000):
    """Stereo: the anthem lead, one note: seven detuned saws and one an octave under, gliding in from the note before
    (m0) in about 60 ms, a vibrato that comes in late, a little overdrive."""
    t = e.tt(d + .15)
    curve = m + (m0 - m) * np.exp(-t / .02) + .15 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - .25) / .3, 0, 1)
    out = np.zeros((len(t), 2))
    for v in range(7):
        s = e.saw(e.hz(curve + (v / 6 - .5) * .5), t)
        out[:, v % 2] += s
        out[:, 1 - v % 2] += .35 * s
    out += .7 * e.saw(e.hz(curve - 12), t)[:, None]
    out = e.lowpass(np.tanh(out / 3), cut)
    return out * (e.rise(t, .004) * e.gate(t, d, .06))[:, None] * .5


def hardstyle_pump(t0, n, beat, depth=.9, tau=.06):
    """The sidechain, n samples from second t0: a gain that dips by `depth` on every beat (the kick) and comes back
    in about 3 * tau seconds. It starts to dip 6 ms before the beat, so the kick starts from quiet and its attack
    (and the beat grid) stands clear of the lead and the pad."""
    ph = (t0 + np.arange(n) / e.SR + beat / 2) % beat - beat / 2         # seconds from the nearest beat
    return 1 - depth * np.where(ph < 0, np.clip(1 + ph / .006, 0, 1), np.exp(-ph / tau))


def hardstyle_pad(S, P, bar, amp=1.0, cut=2500):
    """parts.Band.pad (the string pad), pumping with the kick (hardstyle_pump)."""
    if not S.live(bar):
        return
    g = e.pad(e.voicing(P.chord(bar), P.key_of(bar), lo=55), S.bar, cut=cut, a=.3, r=.6)
    S.put("pads", S.at(bar), g * hardstyle_pump(S.at(bar), len(g), S.beat)[:, None], amp=.45 * amp, wet=.4)


def hardstyle_lead(S, P, bar, amp=1.0, cut=8000):
    """The anthem lead (HARDSTYLE_LEAD), every note gliding in from the one before it, pumping with the kick."""
    if not S.live(bar):
        return
    prev = S.notes(bar - 1, HARDSTYLE_LEAD[(bar - 1) % 4], P.key_of(bar - 1))[-1][1]
    for t, m, d in S.notes(bar, HARDSTYLE_LEAD[bar % 4], P.key_of(bar)):
        g = hardstyle_lead_note(prev, m, d * .97, cut)
        S.put("lead", t, g * hardstyle_pump(t, len(g), S.beat)[:, None], .5, .8 * amp, wet=.35, echo=.15)
        prev = m


@kit("hardstyle", 150, "F#m", ["F#m", "D", "A", "E"], scale="minor", lufs=-8.5,
     mix=dict(drums=.85, bass=1.1, lead=1.0), room_size=(12.0, 9.0, 5.0), rt60=2.4)
def play_hardstyle(S, P, bar, part):
    """Hardstyle at 150 BPM, the Dutch euphoric kind of the late 2000s (Headhunterz, Brennan Heart, Coone). The
    signature is the kick (hardstyle_kick): a 909-style sweep driven into distortion, so its tail is a pitched,
    buzzing tone on the key's root (F#1). After each kick the reverse bass (hardstyle_reverse_bass) swells up on the
    chord's root and cuts off just before the next kick: the "boom-wom" of the 2000s. Over it, a big clap on 2 and 4,
    hats on the offbeats, and in the chorus the anthem lead (hardstyle_lead): wide detuned saws that glide from note
    to note, in the 3-3-3-3-2-2 rhythm; it and the pad pump with the kick (hardstyle_pump). The chords go i-VI-III-VII
    (F#m D A E), one a bar. The verse has the lead behind a low filter; the break has no beat: the pad, a piano and
    the lead behind a filter that opens over 8 bars. A big hall."""
    if part == "drums":
        hardstyle_drums(S, P, bar)
    elif part == "intro":
        hardstyle_drums(S, P, bar, clap=bar % 2 == 1)
        hardstyle_bass(S, P, bar, .8)
        hardstyle_pad(S, P, bar, .8, cut=1200)
    elif part == "verse":
        hardstyle_drums(S, P, bar)
        hardstyle_bass(S, P, bar)
        hardstyle_pad(S, P, bar, 1.0, cut=2000)
        hardstyle_lead(S, P, bar, .5, cut=1800)
    elif part == "chorus":
        hardstyle_drums(S, P, bar, crash=bar % 8 == 0)
        hardstyle_bass(S, P, bar)
        hardstyle_pad(S, P, bar, 1.1)
        hardstyle_lead(S, P, bar, 1.0)
    elif part == "break":
        cut = 700 * 2 ** (bar % 8 / 2.5)          # 700 Hz to about 5 kHz over 8 bars
        P.pad(bar, 1.3, cut=1500 + 300 * (bar % 8))
        P.stabs(bar, steps=(0, 6, 12), sound="piano", amp=.8)
        hardstyle_lead(S, P, bar, .8, cut=cut)


# ---------------------------------------------------------------- gabber
GABBER_GROOVE = dict(hat="x.x.x.x.x.x.x.x.", open="..x...x...x...x.")    # kick: gabber_kick; clap: gabber_clap
GABBER_RIFF = [(0, 3, 0), (3, 3, 0), (6, 4, 3), (10, 2, 2), (12, 4, 1)]   # (sixteenth, sixteenths, chord tone)
GABBER_POING = [(2, 3), (6, 3), (10, 2), (14, 3)]                         # (sixteenth, chord tone): the offbeats
GABBER_DRIFT = (0, .7, -.4, 1.0, -.9, .3, -.7, .5)       # the kick's sweep, faster or slower by up to 10 %, per beat
_GABBER_KICKS = {}


def gabber_tones(P, bar, lo):
    """The chord's tones from its root at or above lo: root, third, fifth, octave, the octave's third."""
    root = e.root_note(P.chord(bar), P.key_of(bar), lo=lo)
    iv = e.chord(P.chord(bar), P.key_of(bar))[1]
    return [root, root + iv[1], root + iv[2], root + 12, root + 12 + iv[1]]


def gabber_kick(m, d, drift=0.0):
    """The Rotterdam kick, d seconds: a 909 kick on the note (a sweep down from 9 times it, a long decay, the click),
    driven into tanh at 20 times, a little lopsided, then once more through an overdriven channel with the middle
    (700 Hz) pushed up 8 dB. It booms and buzzes for the whole beat and stops 12 ms before the next one, so the next
    attack starts from quiet. drift (-1 to 1): the sweep 10 % faster or slower, as an analog drum machine drifts;
    identical hits would line up the ripples inside the buzz, beat after beat, and the beat finder
    (master.beat_phase) would take them for the beat. Made once per note, length and drift."""
    if (m, d, drift) not in _GABBER_KICKS:
        t = e.tt(d)
        f = e.hz(m) * (1 + 7 * np.exp(-t * 80 * (1 + .1 * drift)) + .8 * np.exp(-t * 30 * (1 + .1 * drift)))
        x = np.sin(2 * np.pi * np.cumsum(f) / e.SR) * np.exp(-t * 3)
        x = x + e.bandpass(e.rng.standard_normal(len(t)), 2000, 8000) * np.exp(-t * 300) * 1.5   # a loud click: a clear
        g = e.highpass(np.tanh(20 * (x + .1)), 30)                                               # attack in the mix
        g = e.lowpass(np.tanh(2.5 * e.peaking(g, 700, 8.0, .9)), 7000)
        g *= np.exp(-t * 2) * np.clip((d - t) / .008, 0, 1)
        _GABBER_KICKS[(m, d, drift)] = g / np.abs(g).max()
    return _GABBER_KICKS[(m, d, drift)]


def gabber_clap(a=1.0):
    """The 909 clap and snare together, distorted (tanh at 3 times)."""
    c, s = e.clap(.7), e.snare(.5)
    c[:len(s)] += s
    return np.tanh(3 * c) * .5 * a


def gabber_drums(S, P, bar, amp=1.0, crash=False, clap=True, fill=False):
    """The kick on every beat, tuned to the key's root (A1, 55 Hz): it is the bass as well. The distorted clap on 2
    and 4, closed hats on the eighths, open hats on the offbeats. fill: a distorted snare on the sixteenths of the
    last beat, louder and louder (the end of an 8-bar phrase)."""
    if not S.live(bar):
        return
    m = e.root_note(P.prog[0], P.key_of(bar), lo=33)
    for k in range(0, 16, 4):
        t = S.at(bar) + k * S.step
        S.put("drums", t, gabber_kick(m, round(S.beat - .012, 4), GABBER_DRIFT[(4 * bar + k // 4) % 8]), .5, amp,
              wet=0)
        S.kicks.append(t)
    if clap:
        for k in (4, 12):
            S.put("drums", S.at(bar) + k * S.step, gabber_clap(.8 * amp), .5, wet=.2)
    if fill:
        for k in range(12, 16):
            S.put("drums", S.at(bar) + k * S.step, np.tanh(3 * e.snare(.4 + .15 * (k - 12))) * .45 * amp, .5, wet=.2)
    P.drums(bar, GABBER_GROOVE, amp=amp, kick=False, clap=False, crash=crash)


def gabber_chorus(x, depth=.0025, base=.009, rates=(.7, .9)):
    """Stereo from mono: two delay lines that wobble, one left and one right, mixed with the dry (a chorus)."""
    i = np.arange(len(x))
    out = np.zeros((len(x), 2))
    for ch, (rate, ph) in enumerate(zip(rates, (0, 1.7))):
        d = (base + depth * np.sin(2 * np.pi * rate * i / e.SR + ph)) * e.SR
        out[:, ch] = .6 * x + .55 * np.interp(i - d, i, x, left=0)
    return out


def gabber_pwm(f, t, rate=5.0, depth=.18):
    """A saw minus a copy of itself whose phase offset wobbles (the pulse width of the Alpha Juno): it cuts moving
    holes in the spectrum. The copy's offset moves by running it a little faster or slower than the first saw."""
    duty = .5 + depth * np.sin(2 * np.pi * rate * t + e.rng.uniform(0, 6.3))
    p0 = e.rng.random()
    f2 = np.asarray(f, float) + np.diff(duty, prepend=duty[0]) * e.SR
    return e.saw(f, t, p0) - .7 * e.saw(f2, t, (p0 + duty[0]) % 1.0)


def gabber_hoover(m, d, cut=3200, dive=False):
    """Stereo: the hoover (the Alpha Juno's "What the..." patch of Mentasm and Dominator), one note: PWM saws in three
    octaves, out of tune with each other, a scoop up from a fifth under the note, a chorus and a little overdrive.
    dive: the note falls an octave as it ends."""
    r = .3 if dive else .06
    t = e.tt(d + r)
    bend = -7 * np.exp(-t / .05)
    if dive:
        bend = bend - 12 * np.clip((t - d) / r, 0, 1) ** 1.5
    g = np.zeros(len(t))
    for det, octave, a in ((-.13, 0, 1.0), (.12, 0, 1.0), (0, 0, .8), (-.07, 12, .5), (.08, 12, .5), (0, -12, .45)):
        g += a * gabber_pwm(e.hz(m + octave + det + bend), t, rate=4.0 + 2.0 * e.rng.random())
    g = e.lowpass(e.lowpass(np.tanh(g / 2.5), cut), cut * 1.5)
    return gabber_chorus(g * e.rise(t, .006) * e.gate(t, d, r / 2.5)) * .45


def gabber_riff(S, P, bar, amp=1.0, cut=3200):
    """The hoover riff (GABBER_RIFF) on the chord's tones from A2 up; every other bar the last note dives."""
    if not S.live(bar):
        return
    tones = gabber_tones(P, bar, 45)
    for k, n, i in GABBER_RIFF:
        dive = bar % 2 == 1 and k == 12
        S.put("lead", S.at(bar) + k * S.step, gabber_hoover(tones[i], n * S.step * .92, cut, dive), .5, amp,
              wet=.2, echo=.1 if dive else 0)


def gabber_poing(m, d, cut=5000):
    """The poing: a square wave that drops an octave into its note in about 60 ms, through a resonant filter that
    closes fast, a little overdrive: a rubber "boing"."""
    t = e.tt(d + .05)
    g = e.pulse(e.hz(m) * 2 ** np.exp(-t / .02), t)
    g = e.sweep(g, 250 + cut * np.exp(-t * 18), 4.0, 64)
    return np.tanh(1.5 * g) * e.rise(t, .002) * np.exp(-t * 6) * e.gate(t, d, .03) * .5


def gabber_poings(S, P, bar, amp=1.0, cut=5000):
    """The poing on the offbeats (GABBER_POING), on the chord's tones from A3 up, left and right in turn."""
    if not S.live(bar):
        return
    tones = gabber_tones(P, bar, 57)
    for j, (k, i) in enumerate(GABBER_POING):
        S.put("keys", S.at(bar) + k * S.step, gabber_poing(tones[i], S.step * 1.5, cut), .35 + .3 * (j % 2),
              .6 * amp, wet=.15, echo=.2)


def gabber_stab(S, P, bar, steps=(0, 3, 6), amp=1.0):
    """The rave stab: the chord on detuned saws, short, driven into tanh."""
    if not S.live(bar):
        return
    notes = e.close_voicing(P.chord(bar), P.key_of(bar), lo=57, hi=72)
    g = np.tanh(3 * e.supersaw(notes + [notes[0] + 12], S.step * 1.2, spread=.3, voices=5, a=.002, r=.08,
                               cut=5000)) * .5
    for k in steps:
        S.put("keys", S.at(bar) + k * S.step, g, .5, amp, wet=.25, echo=.1)


def gabber_hold(S, P, bar, amp=1.0, cut=1000):
    """The hoover holding the chord's root (A2 up) for the whole bar, diving at the end of every other bar."""
    if not S.live(bar):
        return
    m = gabber_tones(P, bar, 45)[0]
    S.put("lead", S.at(bar), gabber_hoover(m, S.bar * .95, cut, dive=bar % 2 == 1), .5, amp, wet=.3, echo=.15)


@kit("gabber", 180, "Am", ["Am", "Am", "F", "E"], scale="minor", lufs=-8.5,
     mix=dict(drums=.9, lead=1.2, keys=1.0))
def play_gabber(S, P, bar, part):
    """Gabber at 180 BPM, the early-1990s Rotterdam sound (Rotterdam Termination Source, DJ Paul Elstak, Party
    Animals). The signature is the kick (gabber_kick): a 909 kick tuned to A with a long decay, driven into the red
    and then through an overdriven channel with the middle pushed up, so it booms and buzzes for the whole beat. It is
    the bass too: there is no bassline. Over it the hoover (gabber_hoover): PWM saws in three octaves that scoop up
    into each note, with a chorus and some overdrive, in a 3-3-4-2-4 riff on the chord's tones that dives an octave
    every other bar. On the offbeats the poing (gabber_poing), a rubbery square that drops into its note, after the
    1992 record "Poing" (a guess from its name, not a copy of it), and distorted rave stabs (gabber_stab). Distorted
    909 claps on 2 and 4, closed hats on the eighths, open hats on the offbeats, a snare run at the end of each
    8 bars. The chords: A minor with the major E (Am Am F E). The shouted MC is the song's to add. The verse is the
    kick, the poing and the stabs; the break has no kick: the pad, and the hoover holding the roots behind a filter
    that opens over 8 bars. A small, hard room."""
    if part == "drums":
        gabber_drums(S, P, bar)
    elif part == "intro":
        gabber_drums(S, P, bar)
        gabber_riff(S, P, bar, .7, cut=700)
    elif part == "verse":
        gabber_drums(S, P, bar, fill=bar % 8 == 7)
        gabber_poings(S, P, bar)
        if bar % 2 == 0:
            gabber_stab(S, P, bar)
    elif part == "chorus":
        gabber_drums(S, P, bar, crash=bar % 8 == 0, fill=bar % 8 == 7)
        gabber_riff(S, P, bar)
        gabber_poings(S, P, bar, .6)
        if bar % 2 == 0:
            gabber_stab(S, P, bar, steps=(0,))
    elif part == "break":
        cut = 500 * 2 ** (bar % 8 / 2.5)          # 500 Hz to about 4 kHz over 8 bars
        P.pad(bar, 1.2, cut=1200 + 200 * (bar % 8))
        gabber_hold(S, P, bar, .8, cut=cut)


# ---------------------------------------------------------------- happy hardcore
HH_GROOVE = dict(clap="....x.......x...", open="..x...x...x...x.")    # kick: hh_kick; the break: hh_break
HH_BREAK = dict(kick="x.x.......xx....", snare="....x..o.o..x..o", ride="x.x.x.x.x.x.x.x.")    # the Amen, its first bar
HH_BREAK_B = dict(kick="x.x.......x.....", snare="....x..o.o..x.oo", ride="x.x.x.x.x.x.xoxo")  # its turn, every 4th bar
HH_PIANO = "x..x..x.x..x..x."        # the piano riff's chords: 3 + 3 + 2 sixteenths, twice
HH_DRIFT = (0, .7, -.4, 1.0, -.9, .3, -.7, .5)           # the kick's sweep, faster or slower by up to 10 %, per beat
HH_LEAD = ["A5 - - C6 - - F6 - E6 - - C6 - - A5 -",      # F: the same 3-3-2 rhythm as the piano
           "G5 - - C6 - - E6 - D6 - - C6 - - G5 -",      # C
           "A5 - - D6 - - F6 - E6 - - D6 - - A5 -",      # Dm
           "F5 - - Bb5 - - D6 - C6 - - D6 - - C6 -"]     # Bb: ends on C6, the fifth of F, to lead back
_HH_KICKS = {}


def hh_kick(m, d, drift=0.0):
    """The happy hardcore kick, d seconds: a 909 kick on the note (a sweep down from 9 times it, the click), driven
    into tanh at 4 times: harder than a house kick, much shorter and cleaner than the gabber kick. drift (-1 to 1):
    the sweep 10 % faster or slower, so the ripples of its low tail do not line up beat after beat (the beat finder,
    master.beat_phase, would take them for the beat). Made once per note, length and drift."""
    if (m, d, drift) not in _HH_KICKS:
        t = e.tt(d)
        f = e.hz(m) * (1 + 7 * np.exp(-t * 90 * (1 + .1 * drift)) + .8 * np.exp(-t * 25 * (1 + .1 * drift)))
        x = np.sin(2 * np.pi * np.cumsum(f) / e.SR) * np.exp(-t * 9)
        x = x + e.bandpass(e.rng.standard_normal(len(t)), 2000, 8000) * np.exp(-t * 350) * .8
        g = e.lowpass(e.highpass(np.tanh(4 * x), 30), 8000) * np.clip((d - t) / .008, 0, 1)
        _HH_KICKS[(m, d, drift)] = g / np.abs(g).max()
    return _HH_KICKS[(m, d, drift)]


def hh_gap(t0, n, beat, depth=.7):
    """A gain, n samples from second t0, that dips by `depth` in the last 8 ms before every beat and is back about
    15 ms after it: the keys, the lead and the pad leave a hole for the kick, so its attack (and the beat grid)
    stands clear of what rings over the beat."""
    ph = (t0 + np.arange(n) / e.SR + beat / 2) % beat - beat / 2         # seconds from the nearest beat
    return 1 - depth * np.where(ph < 0, np.clip(1 + ph / .008, 0, 1), np.exp(-ph / .005))


def hh_break_snare(a=1.0):
    """The break's snare, as a sampled acoustic snare played faster: a body at 240 Hz that drops a little, the wires
    (noise, 1.5 to 10 kHz), a little tanh."""
    t = e.tt(.18)
    body = np.sin(2 * np.pi * np.cumsum(240 * (1 + .3 * np.exp(-t * 60))) / e.SR) * np.exp(-t * 30)
    wires = e.bandpass(e.rng.standard_normal(len(t)), 1500, 10000) * np.exp(-t * 22)
    return np.tanh(1.5 * (.7 * body + wires)) * .6 * a


def hh_ride(a=1.0):
    """The break's ride: the 808's six squares tuned up, and noise, above 5 kHz, a short ring."""
    t = e.tt(.25)
    g = sum(np.sign(np.sin(2 * np.pi * f * 3.1 * t)) for f in e.METAL) / 6 + e.rng.standard_normal(len(t)) * .3
    return e.highpass(g, 5000) * np.exp(-t * 14) * (1 + 2 * np.exp(-t * 200)) * .4 * a


def hh_break(S, P, bar, amp=1.0):
    """The breakbeat under the kick: the Amen's pattern (HH_BREAK, the turn HH_BREAK_B every 4th bar) on a small
    acoustic kit, the ghost snares soft. Its own kick is high, short and high-passed at 150 Hz: the four-on-the-floor
    kick keeps the low end."""
    if not S.live(bar):
        return
    groove = HH_BREAK_B if bar % 4 == 3 else HH_BREAK
    for k in range(16):
        t = S.at(bar) + k * S.step
        if groove["kick"][k] == "x":
            g = e.highpass(e.kick(1.0, punch=200, base=75, length=.12, click=.6), 150)
            S.put("drums", t, g, .5, .35 * amp, wet=.1)
        if groove["snare"][k] in "xo":
            S.put("drums", t, hh_break_snare(1.0 if groove["snare"][k] == "x" else .4), .48, amp, wet=.15)
        if groove["ride"][k] in "xo":
            S.put("perc", t, hh_ride(1.0 if groove["ride"][k] == "x" else .5), .62, amp, wet=.05)


def hh_drums(S, P, bar, amp=1.0, crash=False, brk=True):
    """The kick on every beat, tuned to the key's root (F1, 44 Hz), the breakbeat under it (hh_break), the 909 clap
    on 2 and 4, open hats on the offbeats."""
    if not S.live(bar):
        return
    m = e.root_note(P.prog[0], P.key_of(bar), lo=29)
    for k in range(0, 16, 4):
        t = S.at(bar) + k * S.step
        S.put("drums", t, hh_kick(m, round(S.beat - .01, 4), HH_DRIFT[(4 * bar + k // 4) % 8]), .5, amp, wet=0)
        S.kicks.append(t)
    if brk:
        hh_break(S, P, bar, .8 * amp)
    P.drums(bar, HH_GROOVE, amp=amp, kick=False, crash=crash)


def hh_bass_note(m, d, cut=1200):
    """A bouncy bass note: saw, pulse and sine, a resonant filter that blips open on the attack."""
    t = e.tt(d + .02)
    g = e.saw(e.hz(m), t) * .55 + e.pulse(e.hz(m), t, .3) * .3 + e.sine(e.hz(m), t) * .8
    g = e.sweep(g, cut * (1 + 3 * np.exp(-t * 35)), 1.3, 64)
    return g * e.rise(t, .002) * e.gate(t, d, .02)


def hh_bass(S, P, bar, amp=1.0, cut=1200):
    """The offbeat bass on the chord's root (Bb1 to A2), the last offbeat of the bar an octave up: the bounce."""
    if not S.live(bar):
        return
    root = e.root_note(P.chord(bar), P.key_of(bar), lo=34)
    for k in (2, 6, 10, 14):
        g = hh_bass_note(root + 12 * (k == 14), S.step * 1.7, cut)
        S.put("bass", S.at(bar) + k * S.step, g, .5, .45 * amp, wet=0)


def hh_piano(S, P, bar, amp=1.0, cut=None, pattern=HH_PIANO, gap=True):
    """The rave piano (engine.piano) riff: the chord from F4 up with its lowest note an octave up on top, on the
    3-3-2 rhythm (HH_PIANO), spread a little left to right. cut: behind a lowpass. gap: a hole for the kick
    (hh_gap)."""
    if not S.live(bar):
        return
    notes = e.close_voicing(P.chord(bar), P.key_of(bar), lo=65, hi=79)
    notes = notes + [notes[0] + 12]
    for k, c in enumerate(pattern):
        if c not in "xo":
            continue
        v = 1.0 if c == "x" else .6
        for j, m in enumerate(notes):
            t = S.at(bar) + k * S.step + j * .002
            g = e.piano(m, S.step * 2.5, .95 * v)
            g = g if cut is None else e.lowpass(g, cut)
            S.put("keys", t, g * hh_gap(t, len(g), S.beat) if gap else g, .3 + .13 * j, .3 * amp * v, wet=.25,
                  echo=.12)


def hh_roll(S, P, bar, amp=1.0):
    """The piano roll: on the last two beats, the chord on every sixteenth, each one an inversion higher, louder and
    louder, from C4 up to the top of the piano's bright end (about C7)."""
    if not S.live(bar):
        return
    root, iv = e.chord(P.chord(bar), P.key_of(bar))
    tones = [m for m in range(60, 104) if (m - root) % 12 in {i % 12 for i in iv}]
    for i, k in enumerate(range(8, 16)):
        v = .6 + .4 * i / 7
        for j, m in enumerate(tones[i:i + 3]):
            t = S.at(bar) + k * S.step + j * .002
            g = e.piano(m, S.step * 1.2, v)
            S.put("keys", t, g * hh_gap(t, len(g), S.beat), .3 + .2 * j, .3 * amp * v, wet=.25, echo=.1)


def hh_lead_note(m, d, cut=7000):
    """Stereo: the hook's synth, one note: five detuned saws and a square an octave up (the bright, whistling top),
    a quick bend up into the note, a little decay so the fast notes stay apart."""
    t = e.tt(d + .12)
    f = m - .5 * np.exp(-t / .015)
    out = np.zeros((len(t), 2))
    for v in range(5):
        s = e.saw(e.hz(f + (v / 4 - .5) * .3), t)
        out[:, v % 2] += s
        out[:, 1 - v % 2] += .4 * s
    out += .5 * e.pulse(e.hz(f + 12), t)[:, None]
    out = e.lowpass(out, cut) / 4
    return out * (e.rise(t, .003) * e.gate(t, d, .06) * (.75 + .25 * np.exp(-t * 8)))[:, None]


def hh_lead(S, P, bar, amp=1.0, cut=7000):
    """The hook (HH_LEAD) on hh_lead_note, the notes a little short, on the dotted-eighth echo, a hole for the kick
    (hh_gap)."""
    if not S.live(bar):
        return
    for t, m, d in S.notes(bar, HH_LEAD[bar % 4], P.key_of(bar)):
        g = hh_lead_note(m, d * .85, cut)
        S.put("lead", t, g * hh_gap(t, len(g), S.beat)[:, None], .5, .7 * amp, wet=.25, echo=.2)


def hh_pad(S, P, bar, amp=1.0, cut=2500, gap=True):
    """parts.Band.pad (the string pad); gap: a hole for the kick (hh_gap)."""
    if not S.live(bar):
        return
    g = e.pad(e.voicing(P.chord(bar), P.key_of(bar), lo=55), S.bar, cut=cut, a=.3, r=.6)
    S.put("pads", S.at(bar), g * hh_gap(S.at(bar), len(g), S.beat)[:, None] if gap else g, amp=.45 * amp, wet=.4)


def hh_stab(S, P, bar, amp=1.0):
    """The 1990s orchestra hit (engine.orch_hit) on the chord, on the downbeat: the rave stab."""
    if not S.live(bar):
        return
    notes = e.close_voicing(P.chord(bar), P.key_of(bar), lo=60, hi=74)
    S.put("lead", S.at(bar), e.orch_hit(notes), .5, .5 * amp, wet=.3, echo=.1)


@kit("happy hardcore", 170, "F", ["F", "C", "Dm", "Bb"], scale="major", lufs=-9.0, mix=dict(keys=1.0),
     room_size=(12.0, 8.0, 4.5), rt60=1.8)
def play_happy_hardcore(S, P, bar, part):
    """Happy hardcore at 170 BPM, the UK and Dutch kind of the mid-1990s (DJ Paul Elstak "Luv U More", Force &
    Styles). It is fast, in a major key and euphoric. The signature is the rave piano (engine.piano) playing the
    chords on a 3-3-2 rhythm (hh_piano), with a piano roll up the inversions at the end of every 4 bars (hh_roll).
    Under it, a breakbeat (the Amen's pattern on a small acoustic kit, hh_break) runs under a four-on-the-floor 909
    kick, driven a little (hh_kick, tuned to F1). There are a 909 clap on 2 and 4, open hats and a bouncy bass
    (hh_bass) on the offbeats, and an orchestra hit as the rave stab on every 4th downbeat (hh_stab). The chorus adds
    the hook (hh_lead): bright detuned saws with a square an octave up, in the piano's rhythm. The chords go
    I-V-vi-IV (F C Dm Bb), one a bar. The pitched-up female vocal is the song's to add; the verse leaves room for it.
    The break has no beat: the pad and the piano riff behind a filter that opens over 8 bars. Where the kick plays,
    the piano, the hook and the pad leave a short hole at each beat (hh_gap), so the beat grid stays clear."""
    if part == "drums":
        hh_drums(S, P, bar)
    elif part == "intro":
        hh_drums(S, P, bar)
        hh_bass(S, P, bar, .8)
        hh_piano(S, P, bar, .7, cut=1500)
    elif part == "verse":
        hh_drums(S, P, bar)
        hh_bass(S, P, bar)
        hh_piano(S, P, bar, .7, pattern="x.....x...x.....")
        hh_pad(S, P, bar, 1.0)
    elif part == "chorus":
        hh_drums(S, P, bar, crash=bar % 8 == 0)
        hh_bass(S, P, bar)
        if bar % 4 == 3:
            hh_piano(S, P, bar, pattern=HH_PIANO[:8] + "." * 8)
            hh_roll(S, P, bar)
        else:
            hh_piano(S, P, bar)
        if bar % 4 == 0:
            hh_stab(S, P, bar)
        hh_lead(S, P, bar)
        hh_pad(S, P, bar, 1.0)
    elif part == "break":
        cut = 600 * 2 ** (bar % 8 / 2.5)          # 600 Hz to about 4.5 kHz over 8 bars
        hh_pad(S, P, bar, 1.3, cut=1500 + 300 * (bar % 8), gap=False)
        hh_piano(S, P, bar, .8, cut=cut, gap=False)


# ---------------------------------------------------------------- chiptune
CHIP_FRAME = 1 / 50            # a C64 (PAL) music player sets the sound chip's registers 50 times a second: a frame
CHIP_KICK = [("p", 180, 15), ("p", 120, 13), ("t", 85, 11), ("t", 65, 7), ("t", 55, 3)]    # (wave, Hz, volume)
CHIP_SNARE = [("n", 12000, 15), ("p", 220, 12), ("n", 9000, 11), ("n", 9000, 8), ("n", 8000, 6), ("n", 8000, 4),
              ("n", 7000, 2), ("n", 7000, 1)]
CHIP_HAT = [("n", 40000, 9), ("n", 40000, 4), ("n", 40000, 1)]
CHIP_CRASH = [("n", 30000, v) for v in range(15, 0, -1) for _ in range(4)]          # 1.2 seconds
CHIP_BASS = ((0, 0, 2), (2, 12, 1), (3, 0, 1))      # per beat (sixteenth, semitones up, sixteenths): the gallop
CHIP_CHORDS = "x..x..x...x..x.."                     # the fake chord's rhythm: 3 + 3 + 4 + 3 + 3 sixteenths
CHIP_ARP = (0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3)        # into the chord tones (two octaves), per sixteenth
CHIP_LEAD = ["E5 - - B5 - - G5 - A5 - B5 - D6 - B5 -",            # Em
             "C6 - - G5 - - E5 - G5 - C6 - E6 - C6 -",            # C
             "A5 - - E5 - - C6 - B5 - A5 - G5 - E5 -",            # Am
             "F#5 - - D#5 - - B4 - D#5 - F#5 - A5 - B5 -"]        # B: the major V, D# the leading note


def chip_pulse(f, t, duty=.5):
    """A pulse wave from -duty to 1 - duty, band-limited: a saw minus a copy of itself running ahead by the width.
    f and duty: a number or one per sample (a moving width is the SID's pulse width modulation)."""
    f = np.broadcast_to(np.asarray(f, float), t.shape)
    duty = np.broadcast_to(np.asarray(duty, float), t.shape)
    p0 = e.rng.random()
    f2 = f + np.diff(duty, prepend=duty[0]) * e.SR
    return (e.saw(f, t, p0) - e.saw(f2, t, (p0 + duty[0]) % 1.0)) * .5


def chip_triangle(f, t):
    """The NES triangle: 16 levels up and 16 down, so it buzzes a little."""
    ph, _ = e.phase(f, len(t))
    tri = 1 - 4 * np.abs(ph % 1.0 - .5)
    return (np.minimum(np.floor((tri + 1) * 8), 15) - 7.5) / 7.5


def chip_noise(n, rate):
    """The noise wave, n samples: a new random level `rate` times a second, held in between (low rates: grittier)."""
    i = (np.arange(n) * min(rate, e.SR) / e.SR).astype(int)
    return e.rng.uniform(-1, 1, i[-1] + 1)[i]


def chip_env(env):
    """An envelope as the chip's 4-bit volume plays it: 16 steps, each edge smoothed over 1 ms (no clicks)."""
    return e.one_pole(np.round(np.clip(env, 0, 1) * 15) / 15, .001)


def chip_gap(t0, n, beat, depth=.7):
    """A gain, n samples from second t0, that dips by `depth` in the last 8 ms before every beat and is back about
    15 ms after it: the chip voices leave a hole for the kick, so its attack (and the beat grid) stands clear of the
    chirps and the 50 Hz steps that follow each attack."""
    ph = (t0 + np.arange(n) / e.SR + beat / 2) % beat - beat / 2         # seconds from the nearest beat
    return 1 - depth * np.where(ph < 0, np.clip(1 + ph / .008, 0, 1), np.exp(-ph / .005))


def chip_table(rows):
    """A drum as a C64 player's drum table plays it: one row a frame, each row a wave ("p" pulse, "t" triangle,
    "n" noise), a pitch in Hz (for the noise: how often it changes) and a volume (0 to 15). The tone keeps its
    phase from row to row (one oscillator)."""
    n = int(round(CHIP_FRAME * e.SR))
    t = np.arange(n * len(rows)) / e.SR
    f = np.repeat([100.0 if w == "n" else float(hz) for w, hz, _ in rows], n)
    tone = {"p": chip_pulse(f, t), "t": chip_triangle(f, t)}
    out = np.zeros(len(t))
    for i, (w, hz, _) in enumerate(rows):
        s = slice(i * n, (i + 1) * n)
        out[s] = chip_noise(n, hz) if w == "n" else tone[w][s]
    return out * e.one_pole(np.repeat([v / 15 for _, _, v in rows], n), .001)


def chip_drums(S, P, bar, amp=1.0, kick=True, crash=False, fill=False):
    """The club's kick (engine.kick) on every beat with the chip's drum (CHIP_KICK: a pulse and a triangle that
    drop in pitch frame by frame) on top, the noise snare on 2 and 4, noise hats on the eighths (the offbeats
    louder). fill: the noise snare on the sixteenths of the last beat. A noise crash on request."""
    if not S.live(bar):
        return
    for k in range(16):
        t = S.at(bar) + k * S.step
        if kick and k % 4 == 0:
            S.kick(t, 1.4 * amp, punch=130, base=50, length=.3, click=.8)
            S.put("drums", t, chip_table(CHIP_KICK), .5, .45 * amp, wet=0)
        if k in (4, 12) or (fill and k > 12):
            S.put("drums", t, chip_table(CHIP_SNARE), .5, (.55 if k in (4, 12) else .3 + .05 * (k - 12)) * amp,
                  wet=.08)
        if k % 2 == 0:
            S.put("perc", t, e.highpass(chip_table(CHIP_HAT), 6000), .6, (.6 if k % 4 == 2 else .36) * amp, wet=.03)
    if crash:
        S.put("perc", S.at(bar), e.highpass(chip_table(CHIP_CRASH), 3000), .45, .35 * amp, wet=.1)


def chip_bass_note(m, d, cut=1400):
    """The SID bass, one note: a pulse wave (35 % wide) through the SID's resonant lowpass, which snaps shut, over
    a 4-bit triangle on the same note for the low end; a 4-bit volume envelope."""
    t = e.tt(d + .02)
    g = e.sweep(chip_pulse(e.hz(m), t, .35), cut * (.4 + 2.5 * np.exp(-t * 30)), 2.5, 64)
    g = g + .8 * chip_triangle(e.hz(m), t)
    return g * chip_env(np.minimum(t / .002, 1) * (.7 + .3 * np.exp(-t * 20)) * e.gate(t, d, .015))


def chip_bass(S, P, bar, amp=1.0, cut=1400):
    """The galloping octave bass (CHIP_BASS) on the chord's root (A1 to G#2): on each beat the root for an eighth,
    then the octave and the root for a sixteenth each."""
    if not S.live(bar):
        return
    root = e.root_note(P.chord(bar), P.key_of(bar), lo=33)
    for beat in range(4):
        for k, up, n in CHIP_BASS:
            S.put("bass", S.at(bar) + (4 * beat + k) * S.step, chip_bass_note(root + up, n * S.step * .85, cut), .5,
                  .4 * amp, wet=0)


def chip_chord(notes, d, duty=.25, cut=8000, decay=True):
    """The fake chord: one pulse wave that steps through the chord's notes, a new one every frame (50 a second),
    so the ear hears a chord that warbles. A 4-bit volume envelope that falls to half (decay=False: it holds).
    duty: a number or one per sample."""
    t = e.tt(d + .03)
    i = (t / CHIP_FRAME).astype(int) % len(notes)
    g = chip_pulse(e.hz(np.asarray(notes)[i]), t, duty if np.ndim(duty) == 0 else duty[:len(t)])
    env = np.minimum(t / .003, 1) * ((.5 + .5 * np.exp(-t * 8)) if decay else 1.0) * e.gate(t, d, .02)
    return e.lowpass(g, cut) * chip_env(env)


def chip_tones(P, bar, lo):
    """The chord in root position from its root at or above lo: root, third, fifth (a C64 arpeggio table)."""
    root, iv = e.chord(P.chord(bar), P.key_of(bar))
    base = lo + (root - lo) % 12
    return [base + i for i in iv]


def chip_chords(S, P, bar, amp=1.0, cut=8000, pattern=CHIP_CHORDS):
    """The fake chord (chip_chord) from the root at A3 to G#4 up, on the pattern's sixteenths (CHIP_CHORDS), each
    held to just before the next, a hole for the kick (chip_gap)."""
    if not S.live(bar):
        return
    notes = chip_tones(P, bar, 57)
    hits = [k for k, c in enumerate(pattern) if c == "x"] + [16]
    for k, nxt in zip(hits, hits[1:]):
        t = S.at(bar) + k * S.step
        g = chip_chord(notes, (nxt - k) * S.step * .85, .25, cut)
        S.put("keys", t, g * chip_gap(t, len(g), S.beat), .4, .65 * amp, wet=.06, echo=.05)


def chip_arp(S, P, bar, amp=1.0, cut=6000, gap=True):
    """The sixteenth arpeggio (CHIP_ARP) on a thin pulse (12.5 %, the NES's narrowest), up and down two octaves of
    the chord from its root at G4 to F#5 up, short notes, left of centre. gap: a hole for the kick (chip_gap)."""
    if not S.live(bar):
        return
    tones = chip_tones(P, bar, 67)
    tones = tones + [m + 12 for m in tones]
    for k, i in enumerate(CHIP_ARP):
        t = e.tt(S.step * .7 + .02)
        g = chip_pulse(e.hz(tones[i]), t, .125) * chip_env(np.minimum(t / .002, 1) * np.exp(-t * 10)
                                                             * e.gate(t, S.step * .7, .01))
        g = e.lowpass(g, cut) * (chip_gap(S.at(bar) + k * S.step, len(g), S.beat) if gap else 1)
        S.put("keys", S.at(bar) + k * S.step, g, .3, .3 * amp, wet=.06, echo=.12)


def chip_lead_note(m, d, cut=9000):
    """The SID lead, one note: a pulse wave whose width sweeps from 49 % down to 15 % and back (PWM), its first
    frame an octave up (the chirp on the attack), a vibrato of a third of a semitone that comes in after 150 ms,
    a 4-bit volume envelope that holds at 80 %."""
    t = e.tt(d + .05)
    pitch = m + 12 * (t < CHIP_FRAME) + .33 * np.sin(2 * np.pi * 6 * t) * np.clip((t - .15) / .1, 0, 1)
    g = chip_pulse(e.hz(pitch), t, .32 + .17 * np.cos(2 * np.pi * 1.5 * t))
    env = np.minimum(t / .004, 1) * (.8 + .2 * np.exp(-t * 12)) * e.gate(t, d, .02)
    return e.lowpass(g, cut) * chip_env(env)


def chip_lead(S, P, bar, amp=1.0, cut=9000):
    """The lead (CHIP_LEAD) on chip_lead_note, and a second channel that plays it again a dotted eighth later,
    softer, darker and to the right: the chip musician's echo. Both leave a hole for the kick (chip_gap)."""
    if not S.live(bar):
        return
    for t, m, d in S.notes(bar, CHIP_LEAD[bar % 4], P.key_of(bar)):
        for late, pan, a, c in ((0, .5, .45, cut), (3 * S.step, .75, .15, cut / 3)):
            g = chip_lead_note(m, d * .9, c)
            S.put("lead", t + late, g * chip_gap(t + late, len(g), S.beat), pan, a * amp, wet=.08)


def chip_hold(S, P, bar, amp=1.0, cut=2000, cut1=None):
    """The fake chord held for the bar, its width sweeping slowly (PWM), through the SID's resonant lowpass, which
    moves from cut to cut1 over the bar (the C64's filter sweep): the chiptune pad."""
    if not S.live(bar):
        return
    t = e.tt(S.bar + .03)
    g = chip_chord(chip_tones(P, bar, 57), S.bar, .3 + .2 * np.sin(2 * np.pi * .5 * t), 12000, decay=False)
    g = e.sweep(g, np.geomspace(cut, cut1 or cut, len(g)), 3.0, 64)
    S.put("pads", S.at(bar), g, .5, .45 * amp, wet=.15, echo=.1)


@kit("chiptune", 130, "Em", ["Em", "C", "Am", "B"], scale="minor", lufs=-9.0, room_size=(6.0, 4.5, 3.0), rt60=.8)
def play_chiptune(S, P, bar, part):
    """Chiptune dance at 130 BPM, in the C64 and NES style (Rob Hubbard, early Anamanaguchi), on a club beat. The
    signature is the sound chip's square waves: the fake chord (chip_chord), one pulse wave that steps through the
    chord's notes 50 times a second and warbles; a sixteenth arpeggio on a thin pulse (chip_arp); and the lead
    (chip_lead): a pulse whose width sweeps (PWM), a chirp an octave up on each attack, a late vibrato, and a second
    channel that echoes it a dotted eighth later. The galloping octave bass is a SID pulse through a resonant filter
    over a 4-bit NES triangle (chip_bass). The volumes step in 16 levels, as the chips' 4-bit volume does. The drums
    are a club kick on every beat with a chip drum on top, and noise-channel snares and hats, all from drum tables
    played frame by frame (chip_table). The chords go i-VI-iv-V (Em C Am B), one a bar, B major for the pull home.
    The verse leaves the lead out; the break has no beat: the fake chord held through a resonant filter that opens
    over 8 bars (the C64 filter sweep) and the arpeggio behind it. A small, dry room. Where the kick plays, the
    chip voices leave a short hole at each beat (chip_gap), so the beat grid stays clear."""
    if part == "drums":
        chip_drums(S, P, bar)
    elif part == "intro":
        chip_drums(S, P, bar)
        chip_bass(S, P, bar, .8, cut=700)
        chip_arp(S, P, bar, 1.0, cut=2500)
    elif part == "verse":
        chip_drums(S, P, bar, fill=bar % 8 == 7)
        chip_bass(S, P, bar)
        chip_arp(S, P, bar)
        chip_chords(S, P, bar, .7, cut=4000)
    elif part == "chorus":
        chip_drums(S, P, bar, crash=bar % 8 == 0, fill=bar % 8 == 7)
        chip_bass(S, P, bar)
        chip_chords(S, P, bar)
        chip_arp(S, P, bar, .6)
        chip_lead(S, P, bar)
    elif part == "break":
        cut = 400 * 2 ** (bar % 8 / 2)          # 400 Hz to about 4.5 kHz over 8 bars, half an octave a bar
        chip_hold(S, P, bar, 1.2, cut, cut * 2 ** .5)
        chip_arp(S, P, bar, .7, cut=cut * 1.5, gap=False)


# ---------------------------------------------------------------- techno
TECHNO_GROOVE = dict(clap="....x.......x...", hat="xooxxooxxooxxoox", open="..x...x...x...x.")   # kick: techno_kick
TECHNO_PERC = ["...l..m.r..l..h.", "...l..m.r..l.mhm"]   # two bars of 909 toms (low, mid, high) and the rim
TECHNO_STAB = "..x..x....x..x.."        # the chord stab: the same 3 + 5 sixteenths in each half bar, hypnotic
TECHNO_BASS = ((2, 0, 1.0), (3, 0, .6), (6, 0, 1.0), (7, 12, .7), (10, 0, 1.0), (11, 0, .6), (14, 7, .9),
               (15, 12, .7))            # (sixteenth, semitones over the chord's root, level): never on the kick
TECHNO_STRINGS = ["Ab5 - - - - - - - G5 - - - - - - -",      # Fm9
                  "F5 - - - - - - - Eb5 - - - C5 - - -",      # Fm9
                  "F5 - - - - - - - Ab5 - - - C6 - - -",      # Dbmaj7
                  "Bb5 - - - - - - - Eb6 - - - Bb5 - - -"]    # Ebsus4
TECHNO_DRIFT = (0, .7, -.4, 1.0, -.9, .3, -.7, .5)       # the kick's sweep, faster or slower, per beat
_TECHNO_KICKS = {}


def techno_kick(m, d, drift=0.0):
    """The 909 kick, d seconds, tuned to the note: a sine that sweeps down from 7 times the note (the punch) to it,
    a boom that falls over about 300 ms, a loud noise click (a clear attack in the mix), all a little driven (tanh).
    It stops 10 ms before d, so the next kick starts from quiet. drift (-1 to 1): the sweep 20 % faster or slower,
    as an analog drum machine drifts; identical hits would line up the ripples of the boom, beat after beat, and the
    beat finder (master.beat_phase) would take them for the beat. Made once per note, length and drift."""
    if (m, d, drift) not in _TECHNO_KICKS:
        t = e.tt(d)
        r = 1 + .2 * drift
        f = e.hz(m) * (1 + 6 * np.exp(-t * 60 * r) + .6 * np.exp(-t * 14 * r))
        body = np.sin(2 * np.pi * np.cumsum(f) / e.SR) * np.exp(-t * 7)
        click = e.bandpass(e.rng.standard_normal(len(t)), 1500, 7000) * np.exp(-t * 350) * 1.2
        g = np.tanh(1.6 * (body + click)) * np.clip((d - t) / .01, 0, 1)
        _TECHNO_KICKS[(m, d, drift)] = g / np.abs(g).max()
    return _TECHNO_KICKS[(m, d, drift)]


def techno_ride(a=1.0):
    """The 909 ride: the six squares of the 808 cymbal (engine.METAL) three times higher, and some noise, through a
    band of 4 to 12 kHz; a bright ping that rings for about half a second."""
    t = e.tt(.9)
    g = sum(np.sign(np.sin(2 * np.pi * f * 3.1 * t + e.rng.uniform(0, 6.3))) for f in e.METAL) / 6
    g = e.bandpass(g + .3 * e.rng.standard_normal(len(t)), 4000, 12000)
    return g * (np.exp(-t * 6) + .5 * np.exp(-t * 40)) * a * .5


def techno_tom(m, a=1.0):
    """A 909 tom on the note: a sine that drops a little in pitch, a short thump of noise, a little driven."""
    t = e.tt(.35)
    f = e.hz(m) * (1 + .6 * np.exp(-t * 30))
    g = np.sin(2 * np.pi * np.cumsum(f) / e.SR) * np.exp(-t * 9)
    g = g + e.bandpass(e.rng.standard_normal(len(t)), 300, 3000) * np.exp(-t * 60) * .25
    return np.tanh(1.5 * g) * a


def techno_drums(S, P, bar, amp=1.0, crash=False, clap=True, kick=True):
    """The 909 kick on every beat, tuned to the key's fifth (C2, 65 Hz: on F1 the boom's ripples pulled the beat
    finder 22 ms late), the clap on 2 and 4, closed hats on the sixteenths (loud on the beat and on its last
    sixteenth, which drives), open hats on the offbeats."""
    if not S.live(bar):
        return
    if kick:
        m = e.root_note(P.prog[0], P.key_of(bar), lo=29) + 7
        for k in range(0, 16, 4):
            t = S.at(bar) + k * S.step
            S.put("drums", t, techno_kick(m, round(S.beat - .01, 4), TECHNO_DRIFT[(4 * bar + k // 4) % 8]), .5, amp,
                  wet=0)
            S.kicks.append(t)
    P.drums(bar, TECHNO_GROOVE, amp=amp, kick=False, clap=clap, crash=crash)


def techno_perc(S, P, bar, amp=1.0, ride=True):
    """The rolling percussion: 909 toms on the key's root, fifth and octave (F2, C3, F3) and the rim, on a two-bar
    pattern (TECHNO_PERC), a little left and right; ride: the 909 ride on the offbeats."""
    if not S.live(bar):
        return
    root = e.root_note(P.prog[0], P.key_of(bar), lo=40)
    for k, c in enumerate(TECHNO_PERC[bar % 2]):
        t = S.at(bar) + k * S.step
        if c in "lmh":
            j = "lmh".index(c)
            S.put("perc", t, techno_tom(root + (0, 7, 12)[j], .5 * amp), (.35, .55, .7)[j], wet=.25)
        elif c == "r":
            S.put("perc", t, e.rim(.6 * amp), .4, wet=.2, echo=.1)
    if ride:
        for k in (2, 6, 10, 14):
            S.put("perc", S.at(bar) + k * S.step, techno_ride(.45 * amp), .7, wet=.1)


def techno_bass_note(m, d, cut=500):
    """A sequencer bass note: a square and a sine on the note, through a resonant lowpass that snaps shut."""
    t = e.tt(d + .02)
    g = e.pulse(e.hz(m), t, .5) * .35 + e.sine(e.hz(m), t) * .7
    g = e.sweep(g, cut * (1 + 4 * np.exp(-t * 35)), 1.4, 64)
    return g * e.rise(t, .002) * e.gate(t, d, .012)


def techno_bass(S, P, bar, amp=1.0, cut=500):
    """The sequencer bass (TECHNO_BASS) on the chord's root (F1 to E2): two sixteenths after each kick, the octave and
    the fifth now and then, never on the kick itself."""
    if not S.live(bar):
        return
    root = e.root_note(P.chord(bar), P.key_of(bar), lo=29)
    for k, up, v in TECHNO_BASS:
        S.put("bass", S.at(bar) + k * S.step, techno_bass_note(root + up, S.step * .8, cut), .5, .65 * v * amp, wet=0)


def techno_stab_note(notes, d, cut=1500, reso=3.0):
    """The chord stab (a Juno's chord memory): two detuned saws a note, through a resonant lowpass whose envelope
    opens it 6 times wider on the attack, a short decay, a little driven."""
    t = e.tt(d + .15)
    g = sum(e.saw(e.hz(m + det), t) for m in notes for det in (-.07, .07)) / (2 * len(notes))
    g = e.sweep(g, cut * (1 + 5 * np.exp(-t * 25)), reso, 64)
    return np.tanh(1.8 * g) * e.rise(t, .002) * np.exp(-t * 7) * e.gate(t, d, .05)


def techno_stabs(S, P, bar, amp=1.0, lo=500, hi=3000, reso=3.0):
    """The chord stab on TECHNO_STAB, a close cluster of the chord (C4 to Eb5), into the dotted-eighth echo. Its
    cutoff moves from lo to hi and back over 8 bars, by time, as a hand on the knob does: the hypnotic part."""
    if not S.live(bar):
        return
    notes = e.close_voicing(P.chord(bar), P.key_of(bar), lo=60, hi=75)
    for k, c in enumerate(TECHNO_STAB):
        if c == "x":
            t = S.at(bar) + k * S.step
            u = .5 - .5 * np.cos(2 * np.pi * t / (8 * S.bar))
            g = techno_stab_note(notes, S.step * 1.5, lo * (hi / lo) ** u, reso)
            S.put("keys", t, g, .5, 1.1 * amp, wet=.25, echo=.35)


def techno_strings(S, P, bar, amp=1.0, cut=5000):
    """The Detroit string line (TECHNO_STRINGS) in octaves on the string pad (engine.pad): long notes, a quick
    attack."""
    if not S.live(bar):
        return
    for t, m, d in S.notes(bar, TECHNO_STRINGS[bar % 4], P.key_of(bar)):
        S.put("lead", t, e.pad([m - 12, m], d * .95, cut=cut, a=.06, r=.35), .5, .5 * amp, wet=.35, echo=.12)


@kit("techno", 132, "Fm", ["Fm9", "Fm9", "Dbmaj7", "Ebsus4"], scale="minor", lufs=-9.0,
     room_size=(20.0, 14.0, 6.0), rt60=1.8)
def play_techno(S, P, bar, part):
    """Techno at 132 BPM, the 1990s Detroit kind (Derrick May, Inner City, Jeff Mills): rhythm over melody, a loop
    that hardly changes, for a DJ. The signature is the drum machine and the stab. The 909 kick (techno_kick), tuned
    to C2 and a little driven, on every beat; the 909 clap on 2 and 4; closed hats on the sixteenths and open hats on
    the offbeats; rolling 909 toms and a rim on a two-bar pattern and a 909 ride on the offbeats (techno_perc). The
    chord stab (techno_stabs) is a Juno-style chord memory, a close cluster of the minor ninth, on the same 3 + 5
    sixteenths each half bar, into the dotted-eighth echo; its resonant filter opens and closes over 8 bars, as a
    hand on the knob does. A sequencer bass on the sixteenths between the kicks (techno_bass). The string pad
    (parts.Band.pad) plays the chords; the chorus adds a Detroit string line in octaves (techno_strings). The chords
    stay on F minor nine for two bars, then Dbmaj7 and Ebsus4: open, never quite home. The break has no beat: the
    strings and the stab behind a filter that opens over 8 bars. A big warehouse."""
    if part == "drums":
        techno_drums(S, P, bar)
    elif part == "intro":
        techno_drums(S, P, bar)
        techno_perc(S, P, bar, .7, ride=False)
        techno_bass(S, P, bar, .8, cut=300)
        techno_stabs(S, P, bar, .8, lo=300, hi=900)
    elif part == "verse":
        techno_drums(S, P, bar)
        techno_perc(S, P, bar)
        techno_bass(S, P, bar)
        techno_stabs(S, P, bar, 1.0, lo=500, hi=2500)
        P.pad(bar, .8, cut=2000)
    elif part == "chorus":
        techno_drums(S, P, bar, crash=bar % 8 == 0)
        techno_perc(S, P, bar)
        techno_bass(S, P, bar, cut=700)
        techno_stabs(S, P, bar, 1.0, lo=900, hi=5000, reso=4.0)
        P.pad(bar, 1.0, cut=3500)
        techno_strings(S, P, bar)
    elif part == "break":
        cut = 400 * 2 ** (bar % 8 / 2)          # 400 Hz to about 4.5 kHz over 8 bars, half an octave a bar
        P.pad(bar, 1.3, cut=1500 + 300 * (bar % 8))
        techno_stabs(S, P, bar, .9, lo=cut, hi=cut * 1.4, reso=5.0)
        techno_strings(S, P, bar, .7, cut=cut * 1.5)


# ---------------------------------------------------------------- acid house
ACID_GROOVE = dict(clap="....x.......x...", hat="xoxoxoxoxoxoxoxo", open="..x...x...x...x.", swing=.12)   # kick: own
ACID_BELL = "...x..x...x..x.."      # the 808 cowbell
# the TB-303's sequencer, 16 steps: semitones over the chord's root, "a" for an accent, "s" for a slide into the
# next step, "." a rest. Line A, and line B with more slides for the fourth bar.
ACID_LINES = ["0a 0 12s 0 . 0a 3 0 12as 10 0 . 7s 5a 0 12",
              "0 12a 0 0s 3 . 0a 12s 15 0 0a 10s 7 0 12as 3"]
ACID_DRIFT = (0, .7, -.4, 1.0, -.9, .3, -.7, .5)        # the kick's sweep, faster or slower, per beat
_ACID_KICKS = {}


def acid_kick(m, d, drift=0.0):
    """The 909 kick, d seconds, tuned to the note: a sine that sweeps down from 6 times the note to it, a short boom
    (about 250 ms), a loud noise click, a little driven. It stops 10 ms before d. drift (-1 to 1): the sweep 20 %
    faster or slower, so the ripples of the boom do not line up beat after beat (the beat finder would take them for
    the beat). Made once per note, length and drift."""
    if (m, d, drift) not in _ACID_KICKS:
        t = e.tt(d)
        r = 1 + .2 * drift
        f = e.hz(m) * (1 + 5 * np.exp(-t * 55 * r) + .5 * np.exp(-t * 14 * r))
        body = np.sin(2 * np.pi * np.cumsum(f) / e.SR) * np.exp(-t * 9)
        click = e.bandpass(e.rng.standard_normal(len(t)), 1500, 7000) * np.exp(-t * 350) * 1.2
        g = np.tanh(1.4 * (body + click)) * np.clip((d - t) / .01, 0, 1)
        _ACID_KICKS[(m, d, drift)] = g / np.abs(g).max()
    return _ACID_KICKS[(m, d, drift)]


def acid_cowbell(a=1.0):
    """The 808 cowbell: two square waves (540 and 800 Hz) through a band, a sharp hit and a short ring."""
    t = e.tt(.3)
    g = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (540, 800)) / 2
    g = e.bandpass(g, 500, 3000)
    return g * (.6 * np.exp(-t * 60) + .4 * np.exp(-t * 12)) * a


def acid_drums(S, P, bar, amp=1.0, kick=True, crash=False, bell=False):
    """Chicago drum machines: the 909 kick on every beat, tuned to the key's root (A1, 55 Hz), the 909 clap on 2 and
    4, the 808's closed hats on the sixteenths with a little swing, open hats on the offbeats; bell: the 808
    cowbell (ACID_BELL), to the right."""
    if not S.live(bar):
        return
    if kick:
        m = e.root_note(P.prog[0], P.key_of(bar), lo=29)
        for k in range(0, 16, 4):
            t = S.at(bar) + k * S.step
            S.put("drums", t, acid_kick(m, round(S.beat - .01, 4), ACID_DRIFT[(4 * bar + k // 4) % 8]), .5, amp,
                  wet=0)
            S.kicks.append(t)
    P.drums(bar, ACID_GROOVE, amp=amp, kick=False, crash=crash)
    if bell:
        swing = ACID_GROOVE["swing"] * S.step
        for k, c in enumerate(ACID_BELL):
            if c == "x":
                t = S.at(bar) + k * S.step + (swing if k % 2 else 0)
                S.put("perc", t, acid_cowbell(.22 * amp), .72, wet=.15, echo=.1)


def acid_303(line, root, step, cut=400, cut1=None, reso=8.0, env=2.5, decay=.3, drive=2.0):
    """One bar of a TB-303 line (16 tokens as in ACID_LINES) from the MIDI note root, a sixteenth `step` seconds long.
    A saw (engine.saw), and a sine on its fundamental for the club's subs, through a resonant lowpass of four poles:
    one biquad with resonance (Q reso) and one without, their cutoff moving per 32 samples. The filter envelope opens
    it `env` octaves on each new note and falls in `decay` seconds (200 ms on an accent). An accent is louder, opens
    the filter more, and its bump builds up over accents in a row (the 303's accent sweep). A slide holds the gate
    open into the next step: the pitch glides there in about 60 ms and the envelopes do not start again. A normal
    note's gate closes after half a step. cut to cut1: the cutoff knob, turned during the bar. Every bar is brought to
    the same loudness, then a little overdrive (tanh)."""
    toks = line.split()
    n_step = int(round(step * e.SR))
    n = 16 * n_step + int(.06 * e.SR)
    t = np.arange(n) / e.SR
    pitch = np.full(n, float(root))
    gate = np.zeros(n)
    feg = np.zeros(n)
    acc = np.zeros(n)
    prev, slid = None, False
    for k, tok in enumerate(toks):
        i0, i1 = k * n_step, (k + 1) * n_step
        if tok == ".":
            prev, slid = None, False
            continue
        m = root + int(tok.rstrip("as"))
        accent, slide = "a" in tok, "s" in tok
        u = t[i0:] - t[i0]
        if slid and prev is not None:          # the slide from the step before: glide, no new envelope
            pitch[i0:] = m + (prev - m) * np.exp(-u / .02)
        else:
            pitch[i0:] = m
            feg[i0:] = np.exp(-u / (.2 if accent else decay))
        if accent:
            acc[i0:] += np.exp(-u / .12)
        nxt = toks[k + 1] if k + 1 < len(toks) else "."
        hold = i1 if slide and nxt != "." else i0 + n_step // 2
        gate[i0:hold] = 1.0 if accent else .7
        prev, slid = m, slide
    acc = np.minimum(e.one_pole(acc, .03), 2.0)
    vca = e.one_pole(gate, .003)
    knob = np.geomspace(cut, cut1 or cut, n)
    cutoff = np.clip(knob * 2 ** (env * feg + 1.2 * acc), 40, 16000)
    p0 = e.rng.random()                      # the sine in phase with the saw's fundamental, so they always add up
    y = e.saw(e.hz(pitch), t, p0) + .4 * e.sine(e.hz(pitch), t, (p0 + .5) % 1.0)
    y = e.sweep(e.sweep(y, cutoff, reso, 32), cutoff, .6, 32) * vca
    y = y * (.35 / (np.sqrt(np.mean(y[vca > .3] ** 2)) + 1e-9))     # the same loudness in every bar, whatever the
    return np.tanh(drive * y) / np.tanh(drive)                       # knob and the resonance do


def acid_line(S, P, bar, amp=1.0, cut=400, cut1=None, reso=8.0, env=2.5, drive=2.0, echo=.0):
    """The 303 (acid_303) on the chord's root (A1 to G#2): line A three bars, line B in the fourth."""
    if not S.live(bar):
        return
    root = e.root_note(P.chord(bar), P.key_of(bar), lo=33)
    g = acid_303(ACID_LINES[bar % 4 == 3], root, S.step, cut, cut1, reso, env, drive=drive)
    S.put("bass", S.at(bar), g, .5, .55 * amp, wet=.06, echo=echo)


@kit("acid house", 124, "Am", ["Am7", "Am7", "Dm7", "Am7"], scale="minor", lufs=-9.0)
def play_acid_house(S, P, bar, part):
    """Acid house at 124 BPM, the Chicago kind of 1986-88 (Phuture, Sleezy D, Baby Ford): sparse, hypnotic, the
    drum machine and one squelching bass synth. The signature is the Roland TB-303 (acid_303): a saw through a
    resonant four-pole lowpass, an envelope that opens it on each note, accents that open it further and build up,
    slides that glide the pitch and keep the filter from starting again, all on a 16-step line of roots, octaves,
    minor thirds, fifths and sevenths (ACID_LINES), a little overdriven. The cutoff knob turns over 8 bars and the
    resonance is high: the squelch. The drums: the 909 kick on every beat (A1), the 909 clap on 2 and 4, the 808's
    hats on the sixteenths with a little swing and open on the offbeats, in the chorus the 808 cowbell (acid_drums).
    A soft string pad (parts.Band.pad) holds the chords: i, i, iv, i (Am7 Am7 Dm7 Am7), and the 303 moves with the
    root. The break has no beat: the pad and the 303 with the resonance up and the cutoff opening over 8 bars. A
    club."""
    sweep = 2 ** np.sin(2 * np.pi * (bar % 8) / 8)              # the hand on the cutoff knob: 0.5 to 2 times
    sweep1 = 2 ** np.sin(2 * np.pi * (bar % 8 + 1) / 8)
    if part == "drums":
        acid_drums(S, P, bar)
    elif part == "intro":
        acid_drums(S, P, bar)
        acid_line(S, P, bar, .7, cut=180 + 30 * (bar % 4), cut1=210 + 30 * (bar % 4), reso=5.0, env=1.5)
    elif part == "verse":
        acid_drums(S, P, bar)
        acid_line(S, P, bar, 1.0, cut=350 * sweep, cut1=350 * sweep1, reso=9.0, env=2.2)
        P.pad(bar, .6, cut=1500)
    elif part == "chorus":
        acid_drums(S, P, bar, crash=bar % 8 == 0, bell=True)
        acid_line(S, P, bar, 1.0, cut=600 * sweep, cut1=600 * sweep1, reso=12.0, env=2.8, drive=3.0, echo=.15)
        P.pad(bar, .8, cut=2200)
    elif part == "break":
        cut = 150 * 2 ** (bar % 8 / 2)          # 150 Hz to about 1.7 kHz over 8 bars, half an octave a bar
        P.pad(bar, 1.3, cut=1200 + 250 * (bar % 8))
        acid_line(S, P, bar, .9, cut=cut, cut1=cut * 2 ** .5, reso=14.0, env=2.0, echo=.2)


# ---------------------------------------------------------------- synthwave
SW_GROOVE = dict(hat="x.o.x.o.x.o.x.o.", open="..............x.")   # kick and snare: synthwave_drums
SW_BASS = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 12, 0)    # semitones over the chord's root, per sixteenth
SW_ARP = (0, 1, 2, 3, 4, 3, 2, 1, 0, 1, 2, 3, 5, 4, 3, 2)      # into the chord tones (two octaves), per sixteenth
SW_LEAD = ["D5 - - - - - A4 - C5 - D5 - - - F5 -",             # Dm
           "F5 - - - D5 - - - - - Bb4 - C5 - - -",             # Bb
           "E5 - - - - - G5 - - - E5 - C5 - - -",              # C
           "E5 - - - - - - - D5 - C5 - A4 - - -"]              # Am
SW_TOMS = ((12, 55, .9), (13, 50, .9), (14, 45, 1.0), (15, 40, 1.0))   # the fill: (sixteenth, MIDI note, level)


def synthwave_gated(n, gate_s, level=.3, seed_lo=400, seed_hi=6500):
    """Stereo: the tail of a 1980s gated reverb, n samples: dense noise (left and right apart, so it is wide) that
    holds its level, then stops dead after gate_s seconds (the noise gate on the room mics)."""
    t = np.arange(n) / e.SR
    tail = e.lowpass(e.highpass(e.rng.standard_normal((n, 2)), seed_lo), seed_hi)
    env = e.rise(t, .008) * np.exp(-t * 2.5) * np.clip((gate_s - t) / .006, 0, 1)
    return tail * (env * level)[:, None]


def synthwave_snare(a=1.0):
    """Stereo: the big gated snare of the 1980s (LinnDrum, Phil Collins): a crack of noise, a body that drops in
    pitch from 240 to 180 Hz, a quiet clap on top, and the gated reverb (synthwave_gated) that cuts off at 0.28 s."""
    t = e.tt(.3)
    crack = e.bandpass(e.rng.standard_normal(len(t)), 1200, 9000) * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(180 * (1 + .33 * np.exp(-t * 40))) / e.SR) * np.exp(-t * 22)
    dry = crack + .7 * body + .5 * e.clap(1.0)[:len(t)]
    return (dry[:, None] * .7 + synthwave_gated(len(t), .28, .55)) * a


def synthwave_tom(m, a=1.0):
    """Stereo: an 80s tom with the gated room: a sine that falls a little in pitch, a stick click, the gate at 0.3 s."""
    t = e.tt(.32)
    body = np.sin(2 * np.pi * np.cumsum(e.hz(m) * (1 + .5 * np.exp(-t * 25))) / e.SR) * np.exp(-t * 9)
    click = e.bandpass(e.rng.standard_normal(len(t)), 2000, 7000) * np.exp(-t * 300) * .4
    room = synthwave_gated(len(t), .3, .25, 200, 3000)
    return ((body + click)[:, None] * .8 + room) * a


def synthwave_drums(S, P, bar, amp=1.0, kick=True, crash=False, fill=False):
    """A drum machine with a gated room: a short punchy kick on every beat, the gated snare on 2 and 4, closed
    hats on the eighths (the offbeat softer), an open hat into the next bar. fill: gated toms down on the last beat
    (SW_TOMS), the end of an 8-bar phrase."""
    if not S.live(bar):
        return
    if kick:
        for k in range(0, 16, 4):
            S.kick(S.at(bar) + k * S.step, amp, punch=120, base=52, length=.3, click=.45)
    for k in (4, 12):
        S.put("drums", S.at(bar) + k * S.step, synthwave_snare(.55 * amp), .5, wet=.08)
    P.drums(bar, SW_GROOVE, amp=amp, kick=False, clap=False, crash=crash)
    if fill:
        for k, m, v in SW_TOMS:
            S.put("drums", S.at(bar) + k * S.step, synthwave_tom(m, .5 * v * amp), .3 + .1 * (k - 12), wet=.08)


def synthwave_bass_note(m, d, cut=500, acc=1.0):
    """The pulsing analog bass: two saws a little apart and a sine on the fundamental, a low-pass that blips open on
    each note (more on an accent) and closes, short."""
    t = e.tt(d + .02)
    f = e.hz(m)
    g = .45 * (e.saw(f * 2 ** (.07 / 12), t) + e.saw(f * 2 ** (-.07 / 12), t)) + .7 * e.sine(f, t)
    g = e.sweep(g, cut * (1 + 3 * acc * np.exp(-t * 30)), 1.3, 64)
    return g * e.rise(t, .002) * e.gate(t, d, .015)


def synthwave_bass(S, P, bar, amp=1.0, cut=500):
    """Sixteenths on the chord's root (SW_BASS), the note on the beat accented: the driving bass of outrun."""
    if not S.live(bar):
        return
    root = e.root_note(P.chord(bar), P.key_of(bar), lo=33)
    for k, iv in enumerate(SW_BASS):
        acc = 1.0 if k % 4 == 0 else .55
        g = synthwave_bass_note(root + iv, S.step * .72, cut, acc)
        S.put("bass", S.at(bar) + k * S.step, g, .5, (.42 if k % 4 == 0 else .34) * amp, wet=0)


def synthwave_chorus(x, depth=.0018, base=.006, rates=(.52, .86)):
    """Stereo from mono: the Juno-60 chorus, two delay lines of about 6 ms swaying slowly, one left, one right."""
    n = len(x)
    i = np.arange(n)
    out = np.zeros((n, 2))
    for ch, r in enumerate(rates):
        d = (base + depth * np.sin(2 * np.pi * r * i / e.SR + ch * np.pi)) * e.SR
        out[:, ch] = .6 * x + .6 * np.interp(i - d, i, x, left=0.0)
    return out


def synthwave_pad(notes, d, cut=1800, a=.35, r=.8):
    """Stereo: the lush retro pad, a Juno-60 patch: for each note a saw and a pulse whose width drifts (two saws a
    hair apart, one taken from the other), a low-pass, a slow swell and release, the Juno chorus."""
    t = e.tt(d + r)
    g = np.zeros(len(t))
    for m in notes:
        f = e.hz(m)
        g += .5 * e.saw(f, t) + .5 * (e.saw(f, t) - e.saw(f * 1.003, t))
    g = e.lowpass(g / len(notes), cut) * e.rise(t, a) * e.gate(t, d, r / 3)
    return synthwave_chorus(g)


def synthwave_pads(S, P, bar, amp=1.0, cut=1800):
    """The chord, held for the bar on the Juno pad, voiced from G3 up."""
    if not S.live(bar):
        return
    notes = e.voicing(P.chord(bar), P.key_of(bar), lo=55)
    S.put("pads", S.at(bar), synthwave_pad(notes, S.bar, cut), .5, .55 * amp, wet=.45)


def synthwave_arp_note(m, d, cut=4000):
    """A square pluck: a pulse wave through a low-pass that closes fast."""
    t = e.tt(d + .05)
    g = e.pulse(e.hz(m), t, .4)
    g = e.sweep(g, cut * (.25 + np.exp(-t * 25)), 1.1, 64)
    return g * e.rise(t, .002) * e.gate(t, d, .04)


def synthwave_arp(S, P, bar, amp=1.0, cut=4000):
    """A sixteenth arpeggio up and down the chord (SW_ARP) on the square pluck, left and right, into the
    dotted-eighth echo: the sequencer of 80s film scores."""
    if not S.live(bar):
        return
    notes = e.close_voicing(P.chord(bar), P.key_of(bar), lo=62, hi=74)
    tones = notes + [m + 12 for m in notes]
    for k, i in enumerate(SW_ARP):
        S.put("keys", S.at(bar) + k * S.step, synthwave_arp_note(tones[i], S.step * .6, cut), .3 + .4 * (k % 2),
              .22 * amp, wet=.25, echo=.35)


def synthwave_lead(S, P, bar, line, amp=1.0, cut=4500):
    """Stereo: the lead, a mono synth over the bar's line ("D5 - A4 ..."): two saws and a square an octave down,
    the pitch gliding from note to note (portamento, 40 ms), a vibrato that comes in late, the gate falling between
    notes, the Juno chorus and a long echo."""
    if not S.live(bar):
        return
    n = int((S.bar + .4) * e.SR)
    t = np.arange(n) / e.SR
    pitch = np.zeros(n)
    gate = np.zeros(n)
    notes = S.notes(bar, line, P.key_of(bar))
    if not notes:
        return
    t0 = S.at(bar)
    for j, (ts, m, d) in enumerate(notes):
        i0 = int((ts - t0) * e.SR)
        pitch[i0:] = m
        gate[i0:i0 + int(d * .92 * e.SR)] = 1.0
    pitch[:int((notes[0][0] - t0) * e.SR)] = notes[0][1]
    pitch = e.one_pole(pitch - pitch[0], .04) + pitch[0]      # from the first note, not from zero
    since = np.zeros(n)                     # the vibrato starts 0.25 s into each note
    for ts, m, d in notes:
        i0 = int((ts - t0) * e.SR)
        since[i0:] = t[:n - i0]
    vib = .15 * np.sin(2 * np.pi * 5.5 * t) * np.clip((since - .25) / .3, 0, 1)
    f = e.hz(pitch + vib)
    g = .4 * (e.saw(f * 2 ** (.08 / 12), t) + e.saw(f * 2 ** (-.08 / 12), t)) + .35 * e.pulse(f / 2, t)
    g = e.lowpass(g, cut) * e.one_pole(gate, .006)
    S.put("lead", t0, synthwave_chorus(g), .5, .3 * amp, wet=.35, echo=.35)


@kit("synthwave", 118, "Dm", ["Dm", "Bb", "C", "Am"], scale="minor", lufs=-9.0, mix=dict(pads=.85),
     room_size=(14.0, 10.0, 6.0), rt60=2.2)
def play_synthwave(S, P, bar, part):
    """Synthwave (outrun) at 118 BPM, the research's tempo next to house; the 2010s revival of 1980s film and game
    music (Kavinsky, College, The Midnight). The signatures: the gated-reverb snare on 2 and 4 (synthwave_snare: a
    dense room tail cut dead at 0.28 s) and gated tom fills; the pulsing bass of analog sixteenths on the root
    (synthwave_bass); a lush Juno-60 pad, saws and drifting pulses through its chorus (synthwave_pad); a square-wave
    sequencer arpeggio into the dotted-eighth echo (synthwave_arp); in the chorus a gliding saw lead with late
    vibrato and a long echo (synthwave_lead). A short punchy kick on every beat (four to the floor, for the DJ),
    eighth hats. The chords go i-VI-VII-v (Dm Bb C Am): a night drive that does not come home. Mostly instrumental,
    as the genre is. The break has no kick: the pad, and the arpeggio and lead behind a filter that opens over 8
    bars. A big hall."""
    if part == "drums":
        synthwave_drums(S, P, bar, fill=bar % 8 == 7)
    elif part == "intro":
        synthwave_drums(S, P, bar)
        synthwave_bass(S, P, bar, .8, cut=300)
        synthwave_pads(S, P, bar, .7, cut=900)
    elif part == "verse":
        synthwave_drums(S, P, bar, fill=bar % 8 == 7)
        synthwave_bass(S, P, bar)
        synthwave_pads(S, P, bar, 1.0, cut=1500)
        synthwave_arp(S, P, bar, .8, cut=2500)
    elif part == "chorus":
        synthwave_drums(S, P, bar, crash=bar % 8 == 0, fill=bar % 8 == 7)
        synthwave_bass(S, P, bar, 1.0, cut=650)
        synthwave_pads(S, P, bar, 1.1, cut=2400)
        synthwave_arp(S, P, bar, .9, cut=4500)
        synthwave_lead(S, P, bar, SW_LEAD[bar % 4], 1.0)
    elif part == "break":
        cut = 600 * 2 ** (bar % 8 / 2.5)          # 600 Hz to about 4 kHz over 8 bars
        synthwave_pads(S, P, bar, 1.3, cut=1200 + 200 * (bar % 8))
        synthwave_arp(S, P, bar, .8, cut=cut)
        synthwave_lead(S, P, bar, SW_LEAD[bar % 4], .7, cut=cut)
        if bar % 8 == 7 and S.live(bar):          # the gated toms lead back in
            for k, m, v in SW_TOMS:
                S.put("drums", S.at(bar) + k * S.step, synthwave_tom(m, .5 * v), .3 + .1 * (k - 12), wet=.08)


# ---------------------------------------------------------------- hi-nrg
HINRG_GROOVE = dict(hat="x.x.x.x.x.x.x.x.", open="..x...x...x...x.")   # kick and claps: hinrg_drums
HINRG_BASS = (0, 12, 0, 12, 0, 12, 0, 12, 0, 12, 0, 12, 0, 12, 7, 12)   # semitones over the root, per sixteenth
HINRG_STAB = "x..x..x...x.x..."    # the brass stabs: 3 + 3 + 4 + 2 + 4 sixteenths, pushing against the kick
HINRG_LEAD = ["F#5 - - - F#5 - D5 - - - B4 - D5 - F#5 -",      # Bm
              "G5 - - - - - F#5 - E5 - - - B4 - - -",           # Em
              "E5 - - - C#5 - - - E5 - A5 - - - G5 -",          # A
              "F#5 - - - - - E5 - - - C#5 - A#4 - - -"]         # F#: A sharp, the harmonic minor's pull home


def hinrg_clap(a=1.0):
    """Stereo: the big handclap of the 1980s drum machines, doubled: two claps from different noise, one a little
    left and one 7 ms later a little right, a bright one and a darker one, and a short room."""
    t = e.tt(.35)
    out = np.zeros((len(t), 2))
    lag = int(.007 * e.SR)
    for ch, (lo, hi) in enumerate(((1000, 6500), (700, 4500))):
        env = sum((t >= o) * np.exp(-np.maximum(t - o, 0) * 150) for o in (0, .008, .017, .025))
        env = env + (t >= .03) * np.exp(-np.maximum(t - .03, 0) * 14) * .6
        g = e.bandpass(e.rng.standard_normal(len(t)), lo, hi) * env
        out[ch * lag:, ch] += g[:len(t) - ch * lag]
        out[ch * lag:, 1 - ch] += .45 * g[:len(t) - ch * lag]
    return out * .8 * a


def hinrg_syndrum(m, a=1.0):
    """The Syndrum (Simmons) "pew": a sine that falls an octave and a half in 0.4 s, with a little noise on the
    attack. The disco tom of the late 1970s and 1980s."""
    t = e.tt(.45)
    f = e.hz(m) * 2 ** (-1.5 * np.minimum(t / .4, 1))
    g = np.sin(2 * np.pi * np.cumsum(f) / e.SR) * np.exp(-t * 6)
    g += e.bandpass(e.rng.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 200) * .2
    return g * a


def hinrg_drums(S, P, bar, amp=1.0, kick=True, crash=False, pew=False, hats=True):
    """Four to the floor, a short punchy kick (the bass fills the gaps); the big doubled handclap (hinrg_clap) on 2
    and 4; eighth hats and open hats on the offbeats, disco's legacy. pew: two Syndrum hits falling on the last
    beat, left then right (hinrg_syndrum)."""
    if not S.live(bar):
        return
    if kick:
        for k in range(0, 16, 4):
            S.kick(S.at(bar) + k * S.step, amp, punch=140, base=52, length=.26, click=.5)
    for k in (4, 12):
        S.put("drums", S.at(bar) + k * S.step, hinrg_clap(.6 * amp), .5, wet=.15)
    P.drums(bar, HINRG_GROOVE, amp=amp, kick=False, clap=False, hats=hats, crash=crash)
    if pew:
        for k, m, pan in ((12, 74, .3), (14, 69, .7)):
            S.put("perc", S.at(bar) + k * S.step, hinrg_syndrum(m, .35 * amp), pan, wet=.2, echo=.15)


def hinrg_bass_note(m, d, cut=900, acc=1.0):
    """The sequenced synth bass (a Moog-style patch): a saw and a square on the note, a resonant low-pass that
    snaps open on the attack and shuts, tight as a sequencer plays it."""
    t = e.tt(d + .015)
    f = e.hz(m)
    g = .55 * e.saw(f, t) + .35 * e.pulse(f, t, .5) + .5 * e.sine(f, t)
    g = e.sweep(g, cut * (1 + 4 * acc * np.exp(-t * 45)), 2.0, 32)
    return g * e.rise(t, .0015) * e.gate(t, d, .01)


def hinrg_bass(S, P, bar, amp=1.0, cut=900):
    """The octave-jumping sixteenths (HINRG_BASS): the root and its octave in turn, the fifth on the last beat, the
    note on each beat accented. This is the genre: it drives like the hi-hat would."""
    if not S.live(bar):
        return
    root = e.root_note(P.chord(bar), P.key_of(bar), lo=33)
    for k, iv in enumerate(HINRG_BASS):
        acc = 1.0 if k % 4 == 0 else .6
        g = hinrg_bass_note(root + iv, S.step * .7, cut, acc)
        S.put("bass", S.at(bar) + k * S.step, g, .5, (.4 if k % 4 == 0 else .32) * amp, wet=0)


def hinrg_brass(notes, d, cut=5000):
    """Stereo: an OB-X synth brass stab: per note four detuned saws, left and right, a filter that opens in 15 ms and
    closes over the note, short."""
    t = e.tt(d + .1)
    out = np.zeros((len(t), 2))
    for m in notes:
        for v, det in enumerate((-.12, -.04, .04, .12)):
            out[:, v % 2] += e.saw(e.hz(m + det), t)
    cutoff = cut * (.12 + .88 * (1 - np.exp(-t / .015))) * (.35 + .65 * np.exp(-t * 7))
    for ch in range(2):
        out[:, ch] = e.sweep(out[:, ch], cutoff, 1.0, 64)
    return out / (2 * len(notes)) * (e.rise(t, .003) * e.gate(t, d, .06))[:, None]


def hinrg_stabs(S, P, bar, amp=1.0, cut=5000, hit=False):
    """The chord as synth brass stabs (HINRG_STAB), into the echo; hit: the Fairlight orchestra hit (engine.orch_hit)
    on the one as well."""
    if not S.live(bar):
        return
    notes = e.close_voicing(P.chord(bar), P.key_of(bar), lo=62, hi=76)
    for k, c in enumerate(HINRG_STAB):
        if c == "x":
            S.put("keys", S.at(bar) + k * S.step, hinrg_brass(notes, S.step * 1.4, cut), .5, .55 * amp, wet=.25,
                  echo=.12)
    if hit:
        S.put("keys", S.at(bar), e.orch_hit(notes, .45 * amp), .5, wet=.3, echo=.1)


@kit("hi-nrg", 128, "Bm", ["Bm", "Em", "A", "F#"], scale="minor", lufs=-9.0)
def play_hi_nrg(S, P, bar, part):
    """Hi-NRG at 128 BPM, the research's tempo between house and eurodance; the fast 1980s disco of the gay clubs
    (Donna Summer's "I Feel Love", Dead or Alive, Divine, Stock Aitken Waterman). The signature is the sequenced bass
    (hinrg_bass): sixteenths that jump between the root and its octave on a tight resonant synth, driving like a
    hi-hat. Over it the 1980s drum machine: a short kick on every beat, a big doubled handclap on 2 and 4
    (hinrg_clap), eighth and open offbeat hats, Syndrum "pews" (hinrg_syndrum) at the end of phrases; OB-X brass
    stabs that push against the kick (hinrg_brass), with the Fairlight orchestra hit on the one in the chorus; a
    string pad (parts.Band.pad) and a dramatic lead line where the big vocal would go (engine.lead). The chords go
    i-iv-VII-V (Bm Em A F#): the major V, the harmonic minor, is the drama. The break has no kick: the pad, the
    bass and the stabs behind a filter that opens over 8 bars, the claps coming back in its last bars."""
    if part == "drums":
        hinrg_drums(S, P, bar)
    elif part == "intro":
        hinrg_drums(S, P, bar)
        hinrg_bass(S, P, bar, .85, cut=500)
    elif part == "verse":
        hinrg_drums(S, P, bar, pew=bar % 4 == 3)
        hinrg_bass(S, P, bar)
        hinrg_stabs(S, P, bar, .7, cut=3000)
        P.pad(bar, .8, cut=2000)
    elif part == "chorus":
        hinrg_drums(S, P, bar, crash=bar % 8 == 0, pew=bar % 4 == 3)
        hinrg_bass(S, P, bar, 1.0, cut=1200)
        hinrg_stabs(S, P, bar, 1.0, cut=6000, hit=bar % 4 == 0)
        P.pad(bar, 1.0, cut=2800)
        P.lead(bar, HINRG_LEAD[bar % 4], 1.8)
    elif part == "break":
        cut = 300 * 2 ** (bar % 8 / 2.5)          # 300 Hz to about 2 kHz over 8 bars
        P.pad(bar, 1.3, cut=1400 + 250 * (bar % 8))
        hinrg_bass(S, P, bar, .8, cut=cut)
        hinrg_stabs(S, P, bar, .7, cut=2 * cut)
        if bar % 8 >= 6 and S.live(bar):          # the claps come back for the last two bars
            for k in (4, 12):
                S.put("drums", S.at(bar) + k * S.step, hinrg_clap(.5), .5, wet=.2)


# ---------------------------------------------------------------- carnaval
CARN_GROOVE = dict(hat="o.x.o.x.o.x.o.x.", open="..x...x...x...x.")   # kick and snare: carnaval_drums
CARN_PAH = (2, 6, 10, 14)            # the afterbeats ("pah"): every "and", between the kicks
CARN_TUBA = [(0, 5, 0, 5), (0, 5, 0, 5), (0, 5, 0, 5), (0, 5, 0, -8)]   # per beat: 0 the root, 5 its fifth, -8 the
                                                                        # leading tone down to the next root
CARN_LEAD = ["D5 - D5 - D5 - Eb5 - F5 - - - D5 - - -",          # Bb
             "Eb5 - Eb5 - Eb5 - F5 - G5 - - - Eb5 - - -",       # Eb
             "F5 - F5 - F5 - G5 - F5 - Eb5 - D5 - Bb4 -",       # Bb
             "Eb5 - D5 - C5 - - - A4 - - - C5 - - -"]           # F


def carnaval_tuba(m, d):
    """The tuba (or sousaphone): a saw and a sine on the note, a scoop up into it, a lowpass that blats open in 20 ms
    and closes again (the lips), a little driven. A soft start, as a tuba speaks."""
    t = e.tt(d + .06)
    f = e.hz(m - .3 * np.exp(-t * 40))
    g = .7 * e.saw(f, t) + .7 * e.sine(f, t)
    cutoff = 220 + 1100 * (1 - np.exp(-t / .02)) * (.35 + .65 * np.exp(-t * 6))
    g = np.tanh(1.6 * e.sweep(g, cutoff, 1.0, 64))
    return g * e.rise(t, .012) * e.gate(t, d, .04) * (.75 + .25 * np.exp(-t * 6))


def carnaval_brass(notes, d, cut=4500):
    """Stereo: the "pah" of the brass section (trombones and horns), one short chord: per note three detuned saws,
    left and right, a scoop up into the note and a filter that opens in 25 ms (the blat) and closes over the note."""
    t = e.tt(d + .08)
    out = np.zeros((len(t), 2))
    scoop = .35 * np.exp(-t * 45)
    for m in notes:
        for v, det in enumerate((-.08, 0, .08)):
            out[:, v % 2] += e.saw(e.hz(m + det - scoop), t) * (1.0 if v == 1 else .7)
    cutoff = cut * (.15 + .85 * (1 - np.exp(-t / .025))) * (.5 + .5 * np.exp(-t * 8))
    for ch in range(2):
        out[:, ch] = np.tanh(1.5 * e.sweep(out[:, ch], cutoff, 1.1, 64) / len(notes))
    return out * (e.rise(t, .006) * e.gate(t, d, .05))[:, None] * .5


def carnaval_accordion(notes, d, cut=4000, bellows=.0):
    """Stereo: the accordion in musette tuning: per note three reeds, one in tune, one 14 cents sharp, one 11 cents
    flat (their beating is the accordion's wobble), each a narrow pulse, the sharp one left and the flat one right.
    A lowpass and a body around 1.2 kHz. bellows: a slow swell of the bellows on long notes (0 to 1)."""
    t = e.tt(d + .05)
    out = np.zeros((len(t), 2))
    for m in notes:
        for cents, side in ((0, (.5, .5)), (14, (.75, .25)), (-11, (.25, .75))):
            r = e.pulse(e.hz(m + cents / 100), t, .3)
            out[:, 0] += r * side[0]
            out[:, 1] += r * side[1]
    out = e.lowpass(out, cut) + .5 * e.bandpass(out, 900, 1600)
    env = e.rise(t, .015) * e.gate(t, d, .03) * (1 + bellows * (.25 * np.sin(np.pi * np.minimum(t / max(d, .1), 1))))
    return out / (2.5 * len(notes)) * env[:, None]


def carnaval_trumpet(m, d, cut=6500):
    """A trumpet: a saw and a narrow pulse, a scoop up into the note, a filter that blats open, a vibrato after 150
    ms, a little breath on the attack, a little driven (a trumpet played loud is bright and edgy)."""
    t = e.tt(d + .08)
    vib = .15 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - .15) / .2, 0, 1)
    f = e.hz(m - .5 * np.exp(-t * 35) + vib)
    g = .6 * e.saw(f, t) + .4 * e.pulse(f, t, .3)
    g = e.sweep(g, cut * (.2 + .8 * (1 - np.exp(-t / .025))) * (.75 + .25 * np.exp(-t * 3)), 1.3, 64)
    g = np.tanh(1.8 * g) / np.tanh(1.8)
    breath = e.bandpass(e.rng.standard_normal(len(t)), 1500, 5000) * np.exp(-t * 40) * .08
    return (g + breath) * e.rise(t, .008) * e.gate(t, d, .05)


def carnaval_snare(a=1.0):
    """The marching snare of the blaaskapel: a tight, high drum (a body falling from 310 to 240 Hz) and bright
    snare wires, short."""
    t = e.tt(.18)
    body = np.sin(2 * np.pi * np.cumsum(240 * (1 + .3 * np.exp(-t * 80))) / e.SR) * np.exp(-t * 30)
    wires = e.bandpass(e.rng.standard_normal(len(t)), 2500, 9000) * np.exp(-t * 22)
    return (.5 * body + wires) * a


def carnaval_bekken(a=1.0):
    """The hand cymbals (bekkens) of a brass band clashed on the afterbeat: noise and the 808's six squares a little
    higher, above 2.5 kHz, choked after about 0.2 s ("tsj")."""
    t = e.tt(.3)
    g = e.rng.standard_normal(len(t)) + sum(np.sign(np.sin(2 * np.pi * f * 3.1 * t)) for f in e.METAL) * .15
    g = e.highpass(g, 2500) * np.exp(-t * 9) * np.clip((.22 - t) / .04, 0, 1)
    return g * a * .45


def carnaval_crowd(a=1.0, n=6):
    """Stereo: a tent full of people clapping along: n claps, each a few milliseconds late (the first on the beat)
    and somewhere else between left and right."""
    t = e.tt(.35)
    out = np.zeros((len(t), 2))
    for i in range(n):
        lag = 0 if i == 0 else int(e.rng.uniform(.002, .022) * e.SR)
        c = e.clap(1.0)[:len(t) - lag] * e.rng.uniform(.6, 1.0)
        pan = e.rng.uniform(.15, .85)
        out[lag:lag + len(c), 0] += c * np.cos(pan * np.pi / 2)
        out[lag:lag + len(c), 1] += c * np.sin(pan * np.pi / 2)
    return out / np.sqrt(n) * a


def carnaval_drums(S, P, bar, amp=1.0, kick=True, crash=False, bekken=False, fill=False):
    """The modern carnaval beat: four to the floor (the party house kick), the marching snare and a clap on 2 and 4,
    the open hat on every "and" (the "pah" of the humpa); bekken: the hand cymbals on every "and" as well, as in a
    brass band; fill: a snare roll (a roffel) over the last beat, into the next 8 bars."""
    if not S.live(bar):
        return
    if kick:
        for k in range(0, 16, 4):
            S.kick(S.at(bar) + k * S.step, amp, punch=120, base=52, length=.3, click=.45)
    for k in (4, 12):
        S.put("drums", S.at(bar) + k * S.step, carnaval_snare(.5 * amp), .5, wet=.15)
        S.put("drums", S.at(bar) + k * S.step, e.clap(.35 * amp), .5, wet=.2)
    P.drums(bar, CARN_GROOVE, amp=amp, kick=False, clap=False, crash=crash)
    if bekken:
        for k in CARN_PAH:
            S.put("perc", S.at(bar) + k * S.step, carnaval_bekken(.4 * amp), .42, wet=.15)
    if fill:
        for j in range(8):                   # thirty-seconds over the last beat, getting louder
            S.put("drums", S.at(bar, 3 + j / 8), carnaval_snare((.2 + .05 * j) * amp), .45, wet=.2)


def carnaval_oompah(S, P, bar, amp=1.0, cut=None):
    """The "oom": the tuba on every beat, the root and its fifth in turn (CARN_TUBA), and the leading tone to the next
    chord at the end of the loop. The roots from Bb1 up; the fifth a fourth down when the root is high enough, the
    nearest place, as a tuba player picks it. cut: a lowpass over it (the break)."""
    if not S.live(bar):
        return
    root = e.root_note(P.chord(bar), P.key_of(bar), lo=33)
    for k, iv in enumerate(CARN_TUBA[bar % 4]):
        m = root + (iv if iv != 5 else (7 if root < 36 else -5))
        g = carnaval_tuba(m, S.beat * .55)
        if cut:
            g = e.lowpass(g, cut)
        S.put("bass", S.at(bar, k), g, .5, .6 * amp, wet=.05)


def carnaval_pah(S, P, bar, amp=1.0, brass=True, accordion=True, cut=4500, steps=CARN_PAH):
    """The "pah": a short chord on every "and" between the tuba's notes, the brass a little left, the accordion's
    left-hand chord buttons a little right."""
    if not S.live(bar):
        return
    notes = e.close_voicing(P.chord(bar), P.key_of(bar), lo=58, hi=72)
    for k in steps:
        t = S.at(bar) + k * S.step
        if brass:
            S.put("keys", t, carnaval_brass(notes, S.step * 1.3, cut), .5, .9 * amp, wet=.2)
        if accordion:
            g = carnaval_accordion([m + 12 for m in notes], S.step * 1.1, min(cut, 4000))
            S.put("keys", t, g * np.array([.8, 1.0]), .5, .6 * amp, wet=.2)


def carnaval_melody(S, P, bar, amp=1.0, sound="trumpet"):
    """The sing-along hook (CARN_LEAD): two trumpets, the second a third under the first (the brass band's way), or
    the accordion alone (sound="accordion"), every note tongued a little short."""
    if not S.live(bar):
        return
    key = P.key_of(bar)
    for t, m, d in S.notes(bar, CARN_LEAD[bar % 4], key):
        if sound == "trumpet":
            S.put("lead", t, carnaval_trumpet(m, d * .85), .44, .3 * amp, wet=.25, echo=.08)
            S.put("lead", t + .004, carnaval_trumpet(P.step_down(m, 2, key), d * .85), .58, .22 * amp, wet=.25)
        else:
            S.put("lead", t, carnaval_accordion([m], d * .9, bellows=.5), .5, .55 * amp, wet=.2, echo=.06)


def carnaval_hold(S, P, bar, amp=1.0, cut=2000):
    """The accordion holding the chord for the whole bar, the bellows swelling, behind a lowpass (the break)."""
    if not S.live(bar):
        return
    notes = e.close_voicing(P.chord(bar), P.key_of(bar), lo=60, hi=74)
    S.put("pads", S.at(bar), carnaval_accordion(notes, S.bar - .05, cut, bellows=1.0), .5, .9 * amp, wet=.35)


@kit("carnaval", 140, "Bb", ["Bb", "Eb", "Bb", "F"], scale="major", lufs=-9.0, room_size=(16.0, 11.0, 5.0), rt60=1.3)
def play_carnaval(S, P, bar, part):
    """Dutch carnaval (the carnavalskraker, schlager with a brass band) at 140 BPM, the research's prompt tempo in
    the middle of the measured 125-150. The signature is the humpa: the oom of a tuba on every beat, the root and its
    fifth in turn (carnaval_oompah, carnaval_tuba), against the pah of the brass section and the accordion's chord
    buttons on every "and" (carnaval_pah, carnaval_brass, carnaval_accordion in musette tuning). Under it the modern
    party beat: a house kick on every beat, a marching snare and clap on 2 and 4, open hats on the "and"s, and in the
    chorus the hand cymbals of a blaaskapel on the "and"s too and a snare roll every 8 bars (carnaval_drums). The
    hook is short, repeated and in the middle of the voice, so a tent can sing it after one listen: the accordion
    plays it in the verse, two trumpets a third apart in the chorus (carnaval_trumpet). Bb major, the brass band's
    key: I-IV-I-V (Bb Eb Bb F), the tuba walking down to the root through the leading tone. A big tent's room. The
    break has no kick: the accordion holds the chords behind a lowpass that opens over 8 bars, a soft string pad,
    the humpa filtered, and the crowd clapping on every beat."""
    if part == "drums":
        carnaval_drums(S, P, bar)
    elif part == "intro":
        carnaval_drums(S, P, bar)
        carnaval_oompah(S, P, bar, .85)
        carnaval_pah(S, P, bar, .7, brass=False)
    elif part == "verse":
        carnaval_drums(S, P, bar, fill=bar % 8 == 7)
        carnaval_oompah(S, P, bar)
        carnaval_pah(S, P, bar, .6, cut=3000, steps=(6, 14))
        carnaval_pah(S, P, bar, .7, brass=False)
        carnaval_melody(S, P, bar, .8, sound="accordion")
    elif part == "chorus":
        carnaval_drums(S, P, bar, crash=bar % 8 == 0, bekken=True, fill=bar % 8 == 7)
        carnaval_oompah(S, P, bar, 1.1)
        carnaval_pah(S, P, bar, 1.0)
        carnaval_melody(S, P, bar, 1.0)
    elif part == "break":
        cut = 400 * 2 ** (bar % 8 / 2.5)          # 400 Hz to about 2.7 kHz over 8 bars
        carnaval_hold(S, P, bar, .7, cut=cut + 600)
        P.pad(bar, .7, cut=1500)
        carnaval_oompah(S, P, bar, .7, cut=cut / 2)
        carnaval_pah(S, P, bar, .6, accordion=False, cut=cut)
        if S.live(bar):
            for k in range(4):
                S.put("drums", S.at(bar, k), carnaval_crowd(.45 if bar % 8 >= 4 else .3), .5, wet=.3)


def main():
    if not sys.argv[1:] or sys.argv[1] == "--list":
        for name, k in KITS.items():
            print(f"{name:16s} {k['bpm']:3d} BPM  {k['key']:4s} {' '.join(k['prog'])}")
        return
    for name in (KITS if sys.argv[1] == "--all" else [" ".join(sys.argv[1:])]):
        print(sketch(name))


if __name__ == "__main__":
    main()
