"""Parts for a new song in a hurry (the surprise themes): drums from step patterns, basslines, chords, keys, a
diva with a choir of other voices, a rapper, a spoken voice. The same parts as in segfault.py, made reusable.

    import engine as e
    import parts
    S = e.Song(bpm=174, bars=128)
    P = parts.Band(S, prog=["Am", "F", "C", "G"], scale="minor")
    P.drums(bar, parts.GROOVES["dnb"])
    P.bass(bar, "offbeat")
    P.diva(bar, "E5 - D5 - C5 - - - . . . . . . . .", "hel lo + world")
    P.rap(bar, "Ten print hello, twenty go to ten.")

Every part takes `bar` and works out the chord and the key change (key_of) itself. The words for the diva are as
the voice should say them, one per note; "+" holds a word over one more note.
"""
import os

import numpy as np

import dx7
import engine as e
import voice as V

# drum patterns, 16 steps a bar: x = hit, o = soft hit, . = rest (kick, clap, closed hat, open hat, extra)
GROOVES = {
    "four":      dict(kick="x...x...x...x...", clap="....x.......x...", hat="..x...x...x...x.", open="..x...x...x...x."),
    "house":     dict(kick="x...x...x...x...", clap="....x.......x...", hat="o.x.o.x.o.x.o.x.", open="..x...x...x...x.",
                      swing=.16),
    "garage":    dict(kick="x......x..x.....", clap="....x.......x...", hat="o.x.o.xoo.x.o.xo", swing=.2),
    "techno":    dict(kick="x...x...x...x...", clap="....x.......x...", hat="xoxoxoxoxoxoxoxo", open="..x...x...x...x."),
    "eurodance": dict(kick="x...x...x...x...", clap="....x.......x...", hat="o...o...o...o...", open="..x...x...x...x."),
    "dnb":       dict(kick="x.........x.....", clap="....x.......x...", hat="x.x.x.x.x.x.x.x.", extra="..o.......o..o.."),
    "breakbeat": dict(kick="x.........x..x..", clap="....x.......x...", hat="x.x.x.x.x.x.x.x.", extra=".......o.o......"),
    "hardstyle": dict(kick="x...x...x...x...", clap="....x.......x...", hat="..x...x...x...x.", open="..x...x...x...x."),
    "hiphop":    dict(kick="x......x..x.....", clap="....x.......x...", hat="x.x.x.x.x.x.x.x.", swing=.18),
    "reggaeton": dict(kick="x...x...x...x...", clap="...x..x....x..x.", hat="x.x.x.x.x.x.x.x."),
    "schlager":  dict(kick="x...x...x...x...", clap="....x.......x...", hat="..x...x...x...x."),
    "halftime":  dict(kick="x.......x.......", clap="........x.......", hat="x.x.x.x.x.x.x.x."),
}

SCALES = {"minor": (0, 2, 3, 5, 7, 8, 10), "major": (0, 2, 4, 5, 7, 9, 11)}
TONIC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
         "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}

CHOIR = ["en_US-ljspeech-high", "en_US-kristin-medium", "en_GB-cori-high", "en_US-hfc_male-medium",
         "en_GB-alan-medium"]


def words_on(notes, words):
    """Pair words with notes: a word takes its note and one more for each "+" after it (sung as one word)."""
    out, toks, i = [], words.split(), 0
    for k, w in enumerate(toks):
        if w == "+":
            continue
        span = 1
        while k + span < len(toks) and toks[k + span] == "+":
            span += 1
        out.append((w, notes[i:i + span]))
        i += span
    assert i == len(notes), f"{len(notes)} notes but the words fill {i}: {words!r}"
    return out


class Band:
    def __init__(self, S, prog, scale="minor", key_of=None, tonic=None, diva_voice=None, rapper_voice=None,
                 choir=None, kick=None):
        """prog: one chord name a bar, repeating ("Am", "F", "C", "G", "Dm9", ...). tonic: the key's root ("A");
        by default the root of the first chord. key_of(bar): semitones up (a key change)."""
        self.S, self.prog, self.scale = S, prog, SCALES[scale]
        self.key_of = key_of or (lambda bar: 0)
        root = prog[0][:2] if prog[0][1:2] in ("#", "b") else prog[0][:1]
        self.tonic = TONIC[tonic or root]
        self.diva_voice = diva_voice or V.DIVA
        self.rapper_voice = rapper_voice or V.RAPPER
        self.choir = choir or CHOIR
        self.kick_kw = kick or dict(punch=130, base=50, length=.34, click=.4)

    # ------------------------------------------------------------ harmony
    def chord(self, bar):
        return self.prog[bar % len(self.prog)]

    def in_scale(self, m, key=0):
        return (m - self.tonic - key) % 12 in self.scale

    def step_up(self, m, steps=2, key=0):
        """The note `steps` scale steps above m (2 = a third)."""
        for _ in range(steps):
            m += 1
            while not self.in_scale(m, key):
                m += 1
        return m

    def step_down(self, m, steps=2, key=0):
        for _ in range(steps):
            m -= 1
            while not self.in_scale(m, key):
                m -= 1
        return m

    # ------------------------------------------------------------ drums
    def drums(self, bar, groove, amp=1.0, kick=True, clap=True, hats=True, crash=False):
        """One bar of a groove from GROOVES (or your own dict of 16-step strings)."""
        S, t0 = self.S, self.S.at(bar)
        swing = groove.get("swing", 0.0) * S.step

        def when(k):
            return t0 + k * S.step + (swing if k % 2 else 0.0)

        def hits(name):
            return [(k, 1.0 if c == "x" else .55) for k, c in enumerate(groove.get(name, "")) if c in "xo"]

        if kick:
            for k, v in hits("kick"):
                S.kick(when(k), v * amp, **self.kick_kw)
        if clap:
            for k, v in hits("clap"):
                S.put("drums", when(k), e.clap(.6 * v * amp), .5, wet=.2)
                S.put("drums", when(k), e.snare(.4 * v * amp), .5, wet=.25)
        if hats:
            for k, v in hits("hat"):
                S.put("perc", when(k), e.hat(.28 * v * amp), .62, wet=.04)
            for k, v in hits("open"):
                S.put("perc", when(k), e.hat(.5 * v * amp, opened=True), .55, wet=.08)
            for k, v in hits("extra"):
                S.put("drums", when(k), e.snare(.3 * v * amp), .45, wet=.2)
        if crash:
            S.put("perc", t0, e.crash(.7 * amp), .5, wet=.3)

    def roll(self, bar0, bars=4, amp=1.0):
        """A snare roll that climbs to the drop, thirty-seconds in the last bar."""
        S, total = self.S, bars * 16
        for k in range(total):
            u = k / total
            t = S.at(bar0) + k * S.step
            S.put("drums", t, e.snare((.15 + .6 * u ** 1.5) * amp), .5, wet=.25)
            if k >= total - 16:
                S.put("drums", t + S.step / 2, e.snare((.15 + .6 * u ** 1.5) * amp * .8), .5, wet=.25)

    # ------------------------------------------------------------ bass
    def bass(self, bar, style="offbeat", amp=1.0, lo=33, cut=1100):
        """offbeat (eurodance, trance), root (house: on the beats), eighths (rolling), reese (dnb: one long note),
        dx7 (FM bass on the offbeats)."""
        S = self.S
        root = e.root_note(self.chord(bar), self.key_of(bar), lo=lo)
        if style == "reese":
            g = sum(e.saw(e.hz(root) * f, e.tt(S.bar)) for f in (1, 1.007, .993)) / 3
            g = e.lowpass(g, 400) * e.gate(e.tt(S.bar), S.bar - .05, .05)
            S.put("bass", S.at(bar), g, .5, .5 * amp, wet=0)
            return
        steps = {"offbeat": (2, 6, 10, 14), "root": (0, 4, 8, 12), "eighths": tuple(range(0, 16, 2))}.get(style, (2, 6, 10, 14))
        for k in steps:
            if style == "dx7":
                g = dx7.note("bass", root, S.step * 1.6, .9, tail=.1)
            else:
                g = e.bass_note(root, S.step * 1.6, cut=cut, decay=3)
            S.put("bass", S.at(bar) + k * S.step, g, .5, .9 * amp, wet=0)

    # ------------------------------------------------------------ chords
    def stabs(self, bar, steps=(0, 3, 6, 10, 12), sound="piano", amp=1.0, lo=60, hi=76):
        """Chord stabs on these sixteenths: piano (rave piano), epiano (DX7), organ (M1), supersaw."""
        S = self.S
        notes = e.close_voicing(self.chord(bar), self.key_of(bar), lo=lo, hi=hi)
        for k in steps:
            t = S.at(bar) + k * S.step
            if sound == "supersaw":
                S.put("lead", t, e.supersaw(notes, S.step * 1.5, spread=.25, a=.003, r=.12, cut=6000), amp=.5 * amp,
                      wet=.2, echo=.15)
                continue
            for j, m in enumerate(notes):
                g = {"piano": lambda: e.piano(m, S.step * 2, .9), "organ": lambda: e.organ(m, S.step * 1.2),
                     "epiano": lambda: dx7.note("epiano", m, S.step * 2, .7, tail=.6)}[sound]()
                S.put("keys", t + j * .003, g, .4 + .1 * j, .3 * amp, wet=.25)

    def pad(self, bar, amp=1.0, cut=2500):
        S = self.S
        S.put("pads", S.at(bar), e.pad(e.voicing(self.chord(bar), self.key_of(bar), lo=55), S.bar, cut=cut, a=.3,
                                          r=.6), amp=.45 * amp, wet=.4)

    def lead(self, bar, line, amp=1.0, bars=1, sound="lead"):
        """A melody line ("E5 - D5 . ...") on the lead synth, or "epiano" / "bells" / "brass" (DX7)."""
        S = self.S
        for t, m, d in S.notes(bar, line, self.key_of(bar), bars):
            g = e.lead(m, d * .95) if sound == "lead" else dx7.note(sound, m, d * .95, .8, tail=.4)
            S.put("lead", t, g, amp=.25 * amp, wet=.3, echo=.2)

    # ------------------------------------------------------------ voices
    def diva(self, bar, line, words, bars=1, octave=-12, amp=1.0, choir=0.0, big=False, voice=None):
        """The diva sings a line: each word on its notes, the consonants just before the beat, an echo on the last
        word. choir > 0: other voices double her left and right and sing a third above; big: a man an octave down
        and a fifth voice a sixth down as well. The choir sings only the vowels (every voice has its own consonant
        lengths, which would smear hers), with less vibrato."""
        S, key = self.S, self.key_of(bar)
        pairs = words_on(S.notes(bar, line, key, bars), words)
        for i, (w, ns) in enumerate(pairs):
            t = ns[0][0]
            notes = [(m + octave, d * .97) for _, m, d in ns]
            li, y = V.sing(w, notes, voice=voice or self.diva_voice)
            S.put("vox", t - li, y, .5, amp, wet=.12, echo=.35 if i == len(pairs) - 1 else .05)
            if not choir:
                continue
            third = [(self.step_up(m, 2, key), d) for m, d in notes]
            parts = [(self.choir[0], notes, 8, .018, .15, .75), (self.choir[1], notes, -8, .009, .85, .75),
                     (self.choir[2], third, 0, .006, .4, .6)]
            if big:
                parts += [(self.choir[3], [(m - 12, d) for m, d in notes], 0, .012, .55, .7),
                          (self.choir[4], [(m - 12, d) for m, d in third], 5, .015, .7, .45)]
            for v, ns2, cents, late, pan, g in parts:   # vowels only: the diva's consonants stay clean
                _, y = V.sing(w, ns2, voice=v, cents=cents, vibrato=.15, vowel_only=True)
                S.put("vox", t + late, y, pan, amp * choir * g, wet=.15, echo=.05)

    def rap(self, bar, text, bars=1, amp=1.0, voice=None, pitch=.92):
        """A spoken line from the downbeat, fitted to the bars (a sixteenth short, to breathe)."""
        S = self.S
        y = V.rap(text, bars * S.bar - S.step, voice=voice or self.rapper_voice, pitch=pitch)
        S.put("vox", S.at(bar), y, .5, amp, wet=.06, echo=.04)

    def say(self, bar, text, voice="en_US-lessac-high", amp=.8, beat=0.0, phone=False):
        """A spoken announcement at its own pace (a computer, an MC); phone=True: through a small speaker."""
        S = self.S
        y = V._finish(V.tts(text, voice))
        y = y * (.14 / (np.sqrt(np.mean(y ** 2)) + 1e-9))
        if phone:
            y = np.tanh(2 * e.bandpass(y, 300, 3400)) * .6
        S.put("vox", S.at(bar, beat), y, .5, amp, wet=.15, echo=.15)


def out_path(name):
    """renders/<name>.wav, or the first argument."""
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "renders", name + ".wav")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    return out
