#!/usr/bin/env python3
"""Push It To Prod: big beat, 124 BPM, E minor. A practice round for the surprise theme (big beat, drawn at random
at 16:48 on 18 November), built in short rounds with the user listening.

push_it_to_prod.py [OUT.wav]          PREVIEW=32-48 push_it_to_prod.py: only bars 32 to 47, for a quick listen

Friday afternoon, a deploy: a shouted hook looped like a sample ("Push it to prod!"), a soul singer on an old
record ("On a Friday afternoon..."), a squelching 303, a heavy distorted breakbeat, a wah-wah funk guitar. Later
the pager goes off and the drop is "Rollback!".

  bars   0-15  intro: the break alone (for the DJ)
        16-31  the 303 comes in behind a filter, the hook as a teaser
        32-47  A: the hook looped, the guitar, the soul sample
        48-63  B: the MC tells how the deploy went; the hook again from 56
        64-71  the break: no drums, the filter closed, the pager, "It's on fire."
        72-79  the build: the room chants "Rollback!", a snare roll, a riser
        80-95  the drop: "Rollback!", the hook backwards; she comes back at 88
        96-111 outro: the break alone (for the DJ)
"""
import numpy as np

import engine as e
import parts
import room
import voice as V

# ---------------------------------------------------------------- the knobs
TITLE = "Push It To Prod"
DAY = "Rehearsal: big beat"
BPM, BARS = 124, 112
KEY = "Em"
KEY_CHANGE = 0
PROG = ["Em", "Em", "G", "A"]          # one chord a bar
LUFS = -9.0

e.seed(BPM)
S = e.Song(bpm=BPM, bars=BARS)
ST, SR = S.step, e.SR
put = S.put


# ---------------------------------------------------------------- drums: a heavy, crunched breakbeat
def grit(x, drive=2.2, bits=12):
    """A sampler's crunch: soft clipping, then 12 bits (an SP-1200, roughly)."""
    y = np.tanh(drive * x) / np.tanh(drive)
    return np.round(y * (2 ** (bits - 1))) / 2 ** (bits - 1)


KICK = grit(e.kick(1.0, punch=130, base=52, length=.32, click=.45), 1.8)
SNARE = grit(e.snare(.7) + .5 * np.pad(e.clap(.5), (0, max(0, len(e.snare(.7)) - len(e.clap(.5)))))[:len(e.snare(.7))], 2.6)
GHOST = grit(e.snare(.28), 2.0)
HAT = grit(e.hat(.35), 1.5)
OPEN = grit(e.hat(.4, opened=True), 1.5)
CRASH = e.crash(.9)
# the break, two bars (A B): a funky drummer feel, kick on 1, the "and" of 2 and 3, the snare on 2 and 4
BREAK = [dict(kick="x.....x..x......", snare="....x.......x...", ghost=".......o.o....o.", hat="x.x.x.x.x.x.x.o."),
         dict(kick="x.....x...x..x..", snare="....x.......x..o", ghost="..o....o.o......", hat="x.x.x.x.x.x.o.x.")]


def hits(s):
    return [(k, 1.0 if c == "x" else .5) for k, c in enumerate(s) if c in "xo"]


def brk(bar, amp=1.0, kick=True):
    if not S.live(bar):
        return
    p, t0 = BREAK[bar % 2], S.at(bar)
    swing = .12 * ST
    at = lambda k: t0 + k * ST + (swing if k % 2 else 0)
    if kick:
        for k, v in hits(p["kick"]):
            put("drums", at(k), KICK, .5, v * amp, wet=0)
            S.kicks.append(at(k))
    for k, v in hits(p["snare"]):
        put("drums", at(k), SNARE, .5, v * amp, wet=.2)
    for k, v in hits(p["ghost"]):
        put("drums", at(k), GHOST, .46, v * amp * .8, wet=.12)
    for k, v in hits(p["hat"]):
        put("perc", at(k), OPEN if k == 14 and bar % 2 == 0 else HAT, .62, .55 * v * amp, wet=.05)


# ---------------------------------------------------------------- the 303
ACID = [  # 16 steps: note (semitones over E1), accent, slide; "." rests
    "0 a", ".", "0", "12 s", "0", ".", "3 a", "0", "0", "10 s", "12", ".", "0 a", "7", "5 s", "3"]


def acid(bar, amp=1.0, cutoff=900.0, reso=6.0):
    """A TB-303 line: a saw, a resonant low-pass whose envelope opens on each note (more on an accent), slides that
    glide the pitch into the next note, then a little drive. cutoff: the base cutoff for the bar (automate it)."""
    if not S.live(bar):
        return
    root = 28 + {"Em": 0, "G": 3, "A": 5}[PROG[bar % 4]]          # E1, and the line follows the chord's root
    t0, d = S.at(bar), 16 * ST
    t = np.arange(int((d + .05) * SR)) / SR
    f = np.zeros_like(t)
    env = np.zeros_like(t)
    amp_env = np.zeros_like(t)
    cur = None
    for k, tok in enumerate(ACID):
        if tok == ".":
            continue
        parts_ = tok.split()
        m = root + int(parts_[0])
        accent, slide = "a" in parts_[1:], "s" in parts_[1:]
        i0, i1 = int(k * ST * SR), int((k + 1) * ST * SR)
        f_tgt = e.hz(m)
        if cur is not None and slide:
            f[i0:i1] = np.geomspace(cur, f_tgt, i1 - i0)
        else:
            f[i0:i1] = f_tgt
        tau = t[i0:] - t[i0]
        env[i0:] = np.maximum(env[i0:], (1.6 if accent else 1.0) * np.exp(-tau / (.09 if accent else .16)))
        amp_env[i0:i1] = 1.0 if accent else .75
        cur = f_tgt
    f[f == 0] = e.hz(root)
    phase = 2 * np.pi * np.cumsum(f) / SR
    osc = 2 * ((phase / (2 * np.pi)) % 1) - 1
    cut = np.clip(cutoff * (1 + 4.5 * env), 60, 9000)
    y = e.sweep(osc, cut, reso, 32)
    y = np.tanh(2.2 * y * amp_env) * .5
    put("bass", t0, y, .5, amp, wet=.06, echo=.08)


def sub(bar, amp=1.0):
    """A sine under the kick, on the chord's root."""
    if not S.live(bar):
        return
    root = 28 + {"Em": 0, "G": 3, "A": 5}[PROG[bar % 4]]
    for k, v in hits(BREAK[bar % 2]["kick"]):
        t = np.arange(int(.3 * SR)) / SR
        put("bass", S.at(bar) + k * ST, np.sin(2 * np.pi * e.hz(root) * t) * np.exp(-t * 7), .5, .7 * v * amp, wet=0)


# ---------------------------------------------------------------- the guitar: wah-wah funk, as a sample
def wah_stab(m_notes, d, open_=1.0):
    """A muted funk chord: pulse waves, a quick pluck, through a band-pass that sweeps up (the wah pedal)."""
    t = np.arange(int(d * SR)) / SR
    g = sum(e.pulse(e.hz(m), t, .3) for m in m_notes) / len(m_notes)
    g = g * np.exp(-t * 18) * (1 - np.exp(-t * 900))
    centre = 500 + 1800 * open_ * (1 - np.exp(-t * 30))
    y = np.zeros_like(g)
    for i in range(0, len(g), 64):           # a moving band-pass, block by block
        c = centre[i]
        y[i:i + 64] = e.bandpass(g[max(0, i - 256):i + 64], c * .6, c * 1.6)[-len(g[i:i + 64]):]
    return np.tanh(2 * y)


CHORD_NOTES = {"Em": [52, 55, 59, 62], "G": [55, 59, 62, 66], "A": [57, 61, 64, 67]}   # Em7, Gmaj7, A7 voicings


def guitar(bar, amp=1.0):
    if not S.live(bar):
        return
    notes = CHORD_NOTES[PROG[bar % 4]]
    for k, v in ((2, 1.0), (3, .5), (6, .9), (10, 1.0), (11, .5), (14, .8)):     # the "chicka" on the offbeats
        put("keys", S.at(bar) + k * ST, wah_stab(notes, ST * 1.4, v), .3 if k % 4 == 2 else .7, .5 * v * amp,
            wet=.1)


# ---------------------------------------------------------------- the voices
_takes = {}


def shout(text, secs, voice="en_US-hfc_male-medium", pitch=1.08):
    """A shouted take, made once and then looped like a sample: the same take every time."""
    k = (text, secs, voice, pitch)
    if k not in _takes:
        y = V.rap(text, secs, voice=voice, pitch=pitch)
        d = np.tanh(3.5 * e.bandpass(y, 300, 5000))                   # the distorted copy over the clean one
        d *= np.sqrt(np.mean(y ** 2)) / (np.sqrt(np.mean(d ** 2)) + 1e-9)
        _takes[k] = y + .45 * d
    return _takes[k]


def hook(bar, beat=0.0, amp=1.0):
    """"Push it to prod!" over a bar and a half."""
    if not S.live(bar, 2):
        return
    put("vox", S.at(bar, beat), shout("Push it to prod!", 1.5 * S.beat * 4 / 2), .5, amp, wet=.08, echo=.12)


def chop(bar, beat, amp=.9):
    """"Push it!" alone: the first syllables of the same sample, cut short."""
    if not S.live(bar):
        return
    y = shout("Push it to prod!", 1.5 * S.beat * 4 / 2)[:int(.42 * SR)].copy()
    y[-int(.01 * SR):] *= np.linspace(1, 0, int(.01 * SR))
    put("vox", S.at(bar, beat), y, .5, amp, wet=.06, echo=.1)


import os
SOUL_VOICE = os.environ.get("SOUL_VOICE", "en_GB-jenny_dioco-medium")
SOUL_BAND = (200, 4500) if os.environ.get("SOUL_VINYL", "1") == "1" else (120, 8000)   # the record's band
SOUL_CRACKLE = .5 if os.environ.get("SOUL_VINYL", "1") == "1" else .2
SOUL = {"eighths": (". . . . B4 - D5 - E5 - G5 - - - E5 - D5 - E5 - - - - - - - - - - - . .", "on a friday + afternoon + +"),
        "quarters": (". . B4 - - - D5 - - - E5 - - - G5 - - - E5 - - - D5 - - - E5 - - - - - . .",
                     "on a friday + afternoon + +")}[os.environ.get("SOUL_PACE", "eighths")]


def dame_line(bar):
    """The singer's line, dry (no record yet): (start second, mono audio), sung with VOX_HUMAN."""
    line, words = SOUL
    keep = V.HUMAN
    V.HUMAN = 1.0
    t_bar = S.at(bar)
    buf = np.zeros(int(2 * S.bar * SR) + SR)
    for w, ns in parts.words_on(S.notes(bar, line, 0, 2), words):
        li, y = V.sing(w, [(m, d * .97) for _, m, d in ns], voice=SOUL_VOICE, vibrato=.5)
        i = int((ns[0][0] - t_bar - li) * SR)
        if i < 0:
            y, i = y[-i:], 0
        buf[i:i + len(y)] += y[:len(buf) - i]
    V.HUMAN = keep
    return t_bar, buf


def ace_take(path, n):
    """ACE-Step's take of the line (SOUL_ACE): its WAV at 44.1 kHz, mono, as long as ours, at our level."""
    from math import gcd
    from scipy import signal as sg
    import master
    x, sr = master.read(path)
    x = x.mean(1)
    if sr != SR:
        g = gcd(SR, sr)
        x = sg.resample_poly(x, SR // g, sr // g)
    if n:
        x = np.pad(x, (0, max(0, n - len(x))))[:n]
    return x


def soul(bar, amp=2.2):
    """The soul singer on an old record: our line sung with VOX_HUMAN, or (SOUL_ACE=take.wav) ACE-Step's take of it
    with ours under it at SOUL_OURS (default .3); then band-limited, a slow wow, and vinyl crackle, as if sampled
    from a 1971 single."""
    if not S.live(bar, 2):
        return
    t_bar, buf = dame_line(bar)
    if os.environ.get("SOUL_ACE"):
        ours = buf
        a = ace_take(os.environ["SOUL_ACE"], len(buf))
        a *= np.sqrt(np.mean(ours ** 2)) / (np.sqrt(np.mean(a ** 2)) + 1e-9)
        buf = a + float(os.environ.get("SOUL_OURS", ".3")) * ours
    buf = e.bandpass(buf, *SOUL_BAND)
    t = np.arange(len(buf)) / SR
    wow = (t + .0015 * np.sin(2 * np.pi * .55 * t)) * SR
    buf = np.interp(np.clip(wow, 0, len(buf) - 1), np.arange(len(buf)), buf)
    buf = buf + e.crackle(len(buf) / SR, SOUL_CRACKLE)[:len(buf)]
    put("vox", t_bar - .05, buf, .5, amp, wet=.2, echo=.1)


# The soul singer: ACE-Step's own take of the line (text to music, the 4B LM and the SFT DiT), chosen by ear from five
# seeds on 18 November (seed 2; seed 3 over the drop), played whole. Made from this request when it is missing (the same seed gives the same
# audio), cached in renders/ace/push_it_to_prod/.
DAME_REQUEST = {"caption": "1970s soul record, a soulful female singer, warm, expressive, breathy, long legato notes, a "
                           "cappella vocals only, no instruments",
                "lyrics": "[Verse]\nOn a Friday afternoon\nOn a Friday afternoon\n", "bpm": 124, "keyscale": "E minor",
                "timesignature": "4", "vocal_language": "en", "output_format": "wav16", "seed": 2, "duration": 16,
                "synth_model": "acestep-v15-sft-Q8_0.gguf", "inference_steps": 50, "guidance_scale": 1.0, "shift": 1.0,
                "lm_model": "acestep-5Hz-lm-4B-Q8_0.gguf"}


def dame_take(seed=2):
    import json
    import ace
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders", "ace", "push_it_to_prod")
    wav = os.path.join(out, f"dame_s{seed}.wav")
    if not os.path.exists(wav):
        os.makedirs(out, exist_ok=True)
        base = os.path.join(out, f"dame_s{seed}")
        json.dump(dict(DAME_REQUEST, seed=seed), open(base + ".json", "w"), indent=1)
        ace.run([os.path.join(ace.ACESTEP, "build", "ace-lm"), "--models", ace.MODELS, "--request", base + ".json",
                 "--device", "Vulkan0"], base + ".lm.log")
        ace.run([os.path.join(ace.ACESTEP, "build", "ace-synth"), "--models", ace.MODELS, "--request", base + "0.json",
                 "--device", "Vulkan0", "--vae-chunk", "512"], base + ".synth.log")
        os.replace(base + "00.wav", wav)
    return wav


DAME_AMP = float(os.environ.get("DAME_AMP", ".88"))      # -8 dB from the first try (2.2): "too prominent"
SOUL_FREE = os.environ.get("SOUL_FREE") or (None if os.environ.get("SOUL_PIPER") else "take")


def soul_free(bar, amp=None, seed=2):
    """ACE-Step's free take, uncut: it starts on the downbeat of `bar` and runs as long as it is (16 s, about 8 bars
    at 124 BPM), only lightly band-limited."""
    if not S.live(bar, 8):
        return
    x = ace_take(dame_take(seed) if SOUL_FREE == "take" else SOUL_FREE, 0)
    x = e.bandpass(x, 120, 8000)
    amp = DAME_AMP * (amp or 1.0)
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * .1                # no crackle: the take is clean (its pauses at -55 dB)
    put("vox", S.at(bar), x, .5, amp, wet=.2, echo=.06)


if os.environ.get("SOUL_STEM"):        # write the singer's dry line (bar 36) for ACE-Step to re-sing, and stop
    import wave
    _, b = dame_line(36)
    b = np.clip(b / (np.abs(b).max() + 1e-9) * .8, -1, 1)
    with wave.open(os.environ["SOUL_STEM"], "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.repeat(b[:, None], 2, 1) * 32767).astype("<i2").tobytes())
    raise SystemExit(f"wrote {os.environ['SOUL_STEM']}: {len(b) / SR:.1f} s")


MC_VOICE = os.environ.get("MC_VOICE", "en_US-ryan-high")


def mc(bar, text, bars=2, amp=1.0, voice=None):
    """The MC: plain speech at its own pace, clean (the dry, calm narrator of a deploy going wrong). Fitting it to
    the bars and a distorted layer made it husky and robotic."""
    if not S.live(bar, bars):
        return
    y = V._finish(V.tts(text, voice or MC_VOICE))
    y = y * (.14 / (np.sqrt(np.mean(y ** 2)) + 1e-9))
    put("vox", S.at(bar), y, .5, amp, wet=.1, echo=.12)


GANG = [("en_US-joe-medium", .2), ("en_US-john-medium", .8), ("en_GB-alan-medium", .35), ("en_US-bryce-medium", .65),
        ("en_US-norman-medium", .5)]


def gang(bar, beat, word, beats=1.0, amp=1.0):
    """A room of developers shouting a word together, a little apart in time and pitch."""
    if not S.live(bar):
        return
    for i, (v, pan) in enumerate(GANG):
        y = shout(word, beats * S.beat, voice=v, pitch=.95 + .05 * i)
        put("vox", S.at(bar, beat) + .007 * i - .014, y, pan, .45 * amp, wet=.15, echo=.05)


def pager(bar, beat=0.0):
    """A pager: three square beeps at 2.7 kHz, twice."""
    if not S.live(bar):
        return
    t = np.arange(int(.08 * SR)) / SR
    beep = np.sign(np.sin(2 * np.pi * 2700 * t)) * .25 * np.minimum(1, (len(t) - np.arange(len(t))) / 200)
    for k in range(6):
        put("fx", S.at(bar, beat) + k * .16 + (.25 if k >= 3 else 0), beep, .6, 1.0, wet=.1)


def rollback(bar, amp=1.0):
    """The hook backwards: a rollback."""
    if not S.live(bar):
        return
    y = shout("Push it to prod!", 1.5 * S.beat * 4 / 2)[::-1]
    put("vox", S.at(bar), y, .5, amp, wet=.15, echo=.2)


def roll(bar0, bars=4, amp=1.0):
    """A snare roll that climbs into the drop: eighths, sixteenths, then thirty-seconds."""
    for b in range(bars):
        if not S.live(bar0 + b):
            continue
        div = (2, 4, 4, 8)[b] if bars == 4 else 4
        for k in range(4 * div):
            u = (b * 4 * div + k) / (bars * 4 * div)
            put("drums", S.at(bar0 + b) + k * S.beat / div, SNARE, .5, (.25 + .6 * u) * amp, wet=.2)


# ---------------------------------------------------------------- the arrangement
RYAN, LESSAC = "en_US-ryan-high", "en_US-lessac-high"        # the two narrators, taking turns
MC_LINES = {48: ("Tests are green. Mostly.", RYAN), 50: ("The reviewer said L G T M.", LESSAC),
            52: ("It's four fifty-nine, on a Friday.", RYAN), 54: ("What could possibly go wrong?", LESSAC)}
for bar in range(BARS):
    intro, outro = bar < 16, bar >= 96
    if intro or outro:
        brk(bar, .9 if bar < 8 else 1.0)
        continue
    brk_on = not (64 <= bar < 72 or bar == 79)
    if brk_on:
        brk(bar, kick=not (72 <= bar < 76))
    if not 64 <= bar < 76:
        sub(bar, .8 if bar < 32 else 1.0)
    if 16 <= bar < 32:
        acid(bar, .8, cutoff=250 + 650 * (bar - 16) / 15)              # the filter opens over 16 bars
        if bar in (24, 28):
            chop(bar, 0)
            chop(bar, 1)
        if bar == 30:
            hook(bar)
    if 32 <= bar < 48:
        acid(bar, 1.0, cutoff=700 + 500 * np.sin(np.pi * (bar - 32) / 16))
        guitar(bar)
        if SOUL_FREE:
            if bar in (32, 34, 44, 46):
                hook(bar)                                              # the shout around her
            if bar == 36:
                soul_free(bar)                                         # her whole take, 36-43, uncut
            if bar == 43:
                chop(bar, 3)
        else:
            if bar % 2 == 0 and bar not in (36, 44):
                hook(bar)                                              # the sample, every two bars
            if bar in (36, 44):
                soul(bar)                                              # the singer has those two bars to herself
                chop(bar + 1, 3)
    if 48 <= bar < 64:                                                 # B: the MC tells how the deploy went
        acid(bar, .9, cutoff=600 + 40 * (bar - 48))
        if bar >= 56:
            guitar(bar, .8)
        if bar in MC_LINES:
            mc(bar, MC_LINES[bar][0], voice=MC_LINES[bar][1])
        if bar >= 56 and bar % 2 == 0:
            hook(bar)
    if 64 <= bar < 72:                                                 # the break: the pager
        acid(bar, .5, cutoff=300, reso=3.0)
        if bar in (64, 66):
            pager(bar)
        if bar == 68:
            mc(bar, "It's on fire.", 1, amp=1.2, voice=LESSAC)
        if bar == 70:
            mc(bar, "Roll it back?", 1, amp=1.1, voice=RYAN)
    if 72 <= bar < 80:                                                 # the build: the room wants a rollback
        acid(bar, .8, cutoff=400 + 180 * (bar - 72), reso=7.0)
        if bar in (72, 74):
            gang(bar, 0, "Roll", 1.5, .8)
            gang(bar, 2, "back", 1.5, .8)
        if bar in (76, 77):
            for b in (0, 2):
                gang(bar, b, "Rollback!", 1.0, .9)
        if bar == 78:
            for b in range(4):
                gang(bar, b, "Rollback!", .8, 1.0)
    if 80 <= bar < 96:                                                 # the drop: rollback, the hook backwards
        acid(bar, 1.0, cutoff=1500 + 400 * np.sin(np.pi * (bar - 80) / 8), reso=8.0)
        guitar(bar)
        if bar < 88:
            if bar % 2 == 0:
                gang(bar, 0, "Rollback!", 1.0, 1.1)
                gang(bar, 2, "Rollback!", 1.0, 1.1)
            else:
                rollback(bar)
        else:
            if bar == 88 and SOUL_FREE:
                soul_free(bar, amp=.82, seed=3)                        # she comes back over the drop: take 3
            if bar in (94,):
                hook(bar)
    if bar in (16, 32, 48, 80, 88):
        put("perc", S.at(bar), CRASH, .5, .8, wet=.3)

roll(76, 4)
S.put("fx", S.at(76), e.riser(S.bar * 4, .4), .5, wet=.3)
S.put("fx", S.at(64), e.downlifter(S.bar * 2, .3), .5, wet=.3)
S.put("fx", S.at(28), e.riser(S.bar * 4, .35), .5, wet=.3)
cut = [(0, 18000), (S.at(64), 18000), (S.at(64) + .05, 1800), (S.at(72), 1800), (S.at(80) - .02, 14000),
       (S.at(80), 18000), (S.n / e.SR, 18000)]   # the master filter: closed in the break, opening in the build
NAME = f"push-it-to-prod_{BPM}bpm_{KEY}"
S.mixdown(parts.out_path(NAME), {"drums": 1.0, "perc": .7, "bass": .85, "pads": .8, "keys": .7, "lead": 1.0,
                                 "vox": 1.3, "fx": .5},
          cut_keys=cut, room=.15, echo_mix=.35, lufs=LUFS, ir=room.impulse_response((7.0, 5.0, 3.0), rt60=1.0))
print(f"share.SONGS row: (\"{NAME}.wav\", \"{TITLE}\", \"{DAY}\", {BPM}, \"{KEY}\", {BARS}),")
