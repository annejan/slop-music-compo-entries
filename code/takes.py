#!/usr/bin/env python3
"""A cappella takes from ACE-Step for a song's lines, and a file to listen to: the song's own bars, then the same
bars with each take laid over them, with spoken labels. The technique of the practice rounds (Push It To Prod,
Uptime Fever): the 4B LM and the SFT DiT sing the lines a cappella, several seeds, the user picks one by ear, and
the take plays whole from a downbeat (no cutting, no time-fitting).

takes.py SONG --bar 48 --lines "Segfault in my heart|Tearing me apart" --caption "mid 1990s eurodance, a female diva"
         [--tag Chorus] [--bars 8] [--seeds 1,2,3,4] [--db -8]
takes.py --menu [--seeds 1,2,3]      the voice menu: kinds of voice that ACE-Step sings a cappella, one MP3

--caption: the genre and the voice ("a cappella vocals only, no instruments" is added). --lines: the words, one sung
line per "|" (respelled for ACE-Step: ace.ACE_SPELL). --bars: the length of the take (8 bars: 16 s at 120 BPM).
--db: the take's level against the mix in those bars (-8: a layer, as in Push It To Prod).

Writes renders/ace/takes/<song>/ (the takes, cached by their request) and "<title>, ACE takes at bar N.mp3" there;
the song's render is not changed. A take is about 20 s of work on the iGPU (the 4B LM and the SFT DiT load each
time, so nothing stays in memory between takes).
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from math import gcd

import numpy as np
from scipy import signal

import ace
import engine as e
import master
import room
import share
import voice as V

TAKES = os.path.join(ace.HERE, "renders", "ace", "takes")
MODEL = dict(lm_model=ace.LM, **ace.SYNTH["sft"])
A_CAPPELLA = "a cappella vocals only, no instruments"
LABEL_VOICE = "en_US-lessac-high"
WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen".split()


def slug(x):
    return re.sub(r"[^a-z0-9]+", "-", x.lower()).strip("-")[:40] or "take"


def ace_words(lines, tag="Chorus"):
    """The lines as ACE-Step's lyrics: one tag above them, respelled where ACE-Step reads a word wrong."""
    text = f"[{tag}]\n" + "\n".join(x.strip() for x in lines if x.strip()) + "\n"
    for pat, rep in ace.ACE_SPELL:
        text = re.sub(pat, rep, text)
    return text


LOCK = os.environ.get("ACE_LOCK")       # a lock file: with several queues, one ACE-Step job on the GPU at a time


def run(cmd, log, timeout):
    """One ACE-Step step; False when it fails or runs past `timeout` s (then it is killed). ACE_LOCK=FILE: wait for
    the GPU (flock) first."""
    if LOCK:
        cmd = ["flock", LOCK, *cmd]
        timeout += 600                      # the wait for the lock counts too
    with open(log, "w") as fh:
        try:
            r = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"killed after {timeout} s: {' '.join(cmd[:1])} (see {log})", file=sys.stderr)
            return False
    if r.returncode:
        print(f"failed (exit {r.returncode}): see {log}", file=sys.stderr)
    return r.returncode == 0


def take(caption, lyrics, bpm, key, bars, seed, out, name="take", lang="en"):
    """One take, `bars` long at `bpm`: the WAV's path, or None when ACE-Step failed. Cached by the request (the same
    request and seed give the same audio)."""
    req = {"caption": f"{caption}, {A_CAPPELLA}", "lyrics": lyrics, "bpm": int(round(bpm)), "keyscale": key,
           "timesignature": "4", "vocal_language": lang, "output_format": "wav16",
           "duration": round(bars * 240 / bpm, 2), "seed": seed, **MODEL}
    h = hashlib.sha1(json.dumps(req, sort_keys=True).encode()).hexdigest()[:8]
    base = os.path.join(out, f"{name}_s{seed}_{h}")
    wav = base + ".wav"
    if os.path.exists(wav):
        return wav
    os.makedirs(out, exist_ok=True)
    json.dump(req, open(base + ".json", "w"), indent=1, ensure_ascii=False)
    build = os.path.join(ace.ACESTEP, "build")
    if not run([os.path.join(build, "ace-lm"), "--models", ace.MODELS, "--request", base + ".json",
                "--device", "Vulkan0"], base + ".lm.log", 300):
        return None
    if not run([os.path.join(build, "ace-synth"), "--models", ace.MODELS, "--request", base + "0.json",
                "--device", "Vulkan0", "--vae-chunk", "512"], base + ".synth.log", 300):
        return None
    os.replace(base + "00.wav", wav)
    return wav


def mono(path):
    """A take as mono at our rate."""
    x, sr = master.read(path)
    x = x.mean(1)
    if sr != e.SR:
        g = gcd(e.SR, sr)
        x = signal.resample_poly(x, e.SR // g, sr // g)
    return x


def rms(x):
    return float(np.sqrt(np.mean(np.square(x)) + 1e-12))


_IR = []


def roomy(y, wet=.22):
    """A mono line in a room, stereo (room.py, the room of the disco rounds)."""
    if not _IR:
        _IR.append(room.impulse_response((9.0, 6.0, 3.5), rt60=1.4))
    ir = _IR[0]
    out = np.repeat(y[:, None], 2, axis=1)
    for c in range(2):
        out[:, c] += wet * signal.fftconvolve(y, ir[:, c])[:len(y)]
    return out


def lay(song, take_wav, bpm, bar, bars, db=-8.0, lead=2):
    """Bars `bar - lead` up to `bar + bars + 1` of the song's render, with the take laid over it from the downbeat of
    `bar`, at `db` against the mix there, then limited back to the excerpt's own loudness."""
    b = 240 / bpm
    i0, i1 = int(round((bar - lead) * b * e.SR)), int(round((bar + bars + 1) * b * e.SR))
    part = song[max(i0, 0):i1].copy()
    if take_wav:
        y = e.bandpass(mono(take_wav), 110, 9000)
        k = int(round(lead * b * e.SR))
        y = y[:len(part) - k]
        y = y * (rms(part[k:k + len(y)]) * 10 ** (db / 20) / rms(y))
        part[k:k + len(y)] += roomy(y)
        part = master.master(part, e.integrated_lufs(song[max(i0, 0):i1]))
    f = int(.4 * e.SR)
    part[-f:] *= np.linspace(1, 0, f)[:, None]
    return part


def label(text, level=.08):
    """A spoken label (Lessac), stereo, with a little silence after it."""
    y = V._finish(V.tts(text, LABEL_VOICE))
    y = y * (level / rms(y))
    return np.concatenate([np.repeat(y[:, None], 2, axis=1), np.zeros((int(.35 * e.SR), 2))])


def gap(seconds=.6):
    return np.zeros((int(seconds * e.SR), 2))


def listen(parts, mp3, title):
    """The parts back to back, written as WAV and MP3 (title tag, artist sunA)."""
    x = np.clip(np.concatenate(parts), -1, 1)
    wav = mp3[:-4] + ".wav"
    master.write(wav, x)
    share.encode(wav, mp3, ["-metadata", f"title={title}", "-metadata", "artist=sunA"], [])
    os.remove(wav)
    return mp3


def song_takes(name, bar, lines, caption, tag="Chorus", bars=8, seeds=(1, 2, 3, 4), db=-8.0):
    """The takes for one song's lines and the listen file: ours, then each seed laid over ours."""
    song = ace.script_name(name)
    n, wav, title, day, bpm, key, nbars = ace.song_info(song)
    out = os.path.join(TAKES, song)
    lyrics = ace_words(lines, tag)
    got = [(s, take(caption, lyrics, bpm, ace.keyscale(key), bars, s, out, f"{tag.lower()}{bar}")) for s in seeds]
    x, _ = master.read(os.path.join(share.RENDERS, wav))
    parts = [label("Ours."), lay(x, None, bpm, bar, bars), gap()]
    for s, w in got:
        if w:
            parts += [label(f"Seed {WORDS[s]}."), lay(x, w, bpm, bar, bars, db), gap()]
        else:
            print(f"seed {s}: no take", file=sys.stderr)
    mp3 = os.path.join(out, f"{title}, ACE takes at bar {bar} ({tag.lower()}).mp3")
    return listen(parts, mp3, f"{title}: ACE takes at bar {bar}")


# ---------------------------------------------------------------- the voice menu: what ACE-Step sings a cappella
SING = ["We light up the night", "Hold on to me tight", "We light up the night", "And everything's alright"]
RAP = ["Step to the front and let the speakers shake", "Every single beat is a move we make",
       "Hands in the air from the floor to the sky", "This is the sound and we never say goodbye"]
SHOUT = ["Hey! Hey! Turn it up!", "Hey! Hey! Never stop!", "Hey! Hey! Turn it up!", "Hey! Hey! Never stop!"]
DUTCH = ["Hossen door de nacht", "Iedereen doet mee", "Hossen door de nacht", "Nog een keer, olé"]
MENU = [  # (the kind, for the label; the caption; the words; the tag; the language)
    ("house diva", "early 1990s deep house, a powerful soulful female diva, gospel runs", SING, "Chorus", "en"),
    ("soul man", "1970s soul, a warm soulful male singer, smooth gospel runs", SING, "Chorus", "en"),
    ("falsetto", "late 1990s French house, a smooth male falsetto singer, disco soul", SING, "Chorus", "en"),
    ("whisper", "early 1990s deep house, a breathy intimate female spoken word voice, close to the microphone",
     SING, "Verse", "en"),
    ("eurodance diva", "mid 1990s eurodance, a bright powerful female dance diva, soaring", SING, "Chorus", "en"),
    ("bubblegum", "late 1990s bubblegum pop, a bright playful high female pop singer", SING, "Chorus", "en"),
    ("male rapper", "mid 1990s eurodance, a male rapper, confident rhythmic flow, clear words", RAP, "Rap", "en"),
    ("female rapper", "1990s hip hop, a female rapper, sharp confident flow, clear words", RAP, "Rap", "en"),
    ("gang chant", "a crowd of men and women shouting together, a terrace chant", SHOUT, "Chorus", "en"),
    ("gospel choir", "a gospel choir, men and women, rich harmonies, call and response", SING, "Chorus", "en"),
    ("punk shout", "1980s punk, a raw shouting male punk singer, hoarse and angry", SHOUT, "Chorus", "en"),
    ("crooner", "1950s lounge, a smooth male crooner, deep baritone, slow vibrato", SING, "Chorus", "en"),
    ("carnival", "Dutch carnival schlager, a cheerful male sing-along singer, beer hall", DUTCH, "Chorus", "nl"),
    ("reggae", "1970s roots reggae, a laid-back warm male reggae singer", SING, "Chorus", "en"),
    ("country", "1990s country, a female country singer with a twang", SING, "Chorus", "en"),
    ("opera", "classical opera, a dramatic operatic soprano", SING, "Chorus", "en"),
    ("kids choir", "a children's choir, bright and innocent", SING, "Chorus", "en"),
    ("robot", "late 1990s French house, robotic vocoder vocals, a talk box", SING, "Chorus", "en"),
]


def menu(seeds=(1, 2, 3), bpm=120, key="A minor", bars=8):
    """Each kind of voice, a few seeds, a cappella, one MP3 with the number and kind spoken before each."""
    out = os.path.join(TAKES, "menu")
    parts, sheet = [], []
    for i, (kind, caption, lines, tag, lang) in enumerate(MENU, 1):
        sheet.append(f"{i:2d}. {kind}: {caption}")
        parts.append(label(f"{WORDS[i] if i < len(WORDS) else i}. {kind}."))
        for s in seeds:
            w = take(caption, ace_words(lines, tag), bpm, key, bars, s, out, slug(kind), lang)
            if not w:
                print(f"{kind}, seed {s}: no take", file=sys.stderr)
                continue
            y = roomy(e.bandpass(mono(w), 80, 12000), .15)
            parts += [label(WORDS[s], .06), master.master(y, -16.0), gap(.5)]
        parts.append(gap(.4))
    open(os.path.join(out, "menu.txt"), "w").write("\n".join(sheet) + "\n")
    return listen(parts, os.path.join(out, "ACE voice menu.mp3"), "ACE voice menu")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song", nargs="?")
    ap.add_argument("--menu", action="store_true", help="the voice menu instead of a song")
    ap.add_argument("--bar", type=int, help="the downbeat where the take starts")
    ap.add_argument("--lines", help='the words, one sung line per "|"')
    ap.add_argument("--caption", help="the genre and the voice")
    ap.add_argument("--tag", default="Chorus", help="the lyrics tag: Chorus, Verse, Rap, ...")
    ap.add_argument("--bars", type=int, default=8)
    ap.add_argument("--seeds", default=None, help="for example 1,2,3,4 (default: 1-4, the menu 1-3)")
    ap.add_argument("--db", type=float, default=-8.0, help="the take against the mix there (default -8 dB)")
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")] if a.seeds else None
    if a.menu:
        print(menu(seeds or (1, 2, 3)))
        return
    if not (a.song and a.bar is not None and a.lines and a.caption):
        ap.error("a song needs --bar, --lines and --caption (or use --menu)")
    print(song_takes(a.song, a.bar, a.lines.split("|"), a.caption, a.tag, a.bars, seeds or (1, 2, 3, 4), a.db))


if __name__ == "__main__":
    main()
