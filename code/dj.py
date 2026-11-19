#!/usr/bin/env python3
"""The files for the DJ: every song as a 16-bit 44.1 kHz WAV with its tempo and key (Camelot) in the name, checked,
and a track list. Copy renders/dj/ to the USB stick (FAT32: the names avoid : ? * " < > | and stay short).

dj.py [--only warm_boot,segfault] [--use rhythm_of_the_badge=renders/ace/rhythm_of_the_badge/x.wav]

--only copies and checks only those songs; the others keep their file and their line in the track list. An older
file of a song (another name: a new key, title or tempo) is removed, so the stick never holds a song twice.

Checks per song: the true peak (at most -1.0 dBTP), the loudness, the beat grid at sample 0 (the kick on the
grid), the 16 bars at each end drums only (little of the 300-3000 Hz band, where keys, pads and voices are, or no
pitch in it: distorted drums fill that band too), and
the length (the bars plus the reverb's tail: a preview or a cut file is flagged).
"""
import argparse
import os
import re
import shutil

import numpy as np
from scipy import signal

import engine as e
import master
import share

OUT = os.path.join(share.RENDERS, "dj")
CAMELOT = {   # all 24 keys, with the enharmonic spellings
    "Abm": "1A", "G#m": "1A", "Ebm": "2A", "D#m": "2A", "Bbm": "3A", "A#m": "3A", "Fm": "4A", "Cm": "5A", "Gm": "6A",
    "Dm": "7A", "Am": "8A", "Em": "9A", "Bm": "10A", "F#m": "11A", "Gbm": "11A", "C#m": "12A", "Dbm": "12A",
    "B": "1B", "Cb": "1B", "F#": "2B", "Gb": "2B", "Db": "3B", "C#": "3B", "Ab": "4B", "G#": "4B", "Eb": "5B",
    "D#": "5B", "Bb": "6B", "A#": "6B", "F": "7B", "C": "8B", "G": "9B", "D": "10B", "A": "11B", "E": "12B"}
# songs that end in another key (a key change for the last chorus); a song not listed here ends in its key moved by
# its script's KEY_CHANGE (the template's knob), see end_key
END_KEY = {"segfault": "Bm", "blinky": "E", "rhythm_of_the_badge": "F#m"}
NOTES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]
PITCH = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
         "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "Cb": 11}


def script_of(wav):
    return wav.split("_")[0].replace("-", "_")


def end_key(song, key):
    """The key of the song's last chorus: END_KEY, else the key moved by `KEY_CHANGE = n` in code/<song>.py."""
    if song in END_KEY:
        return END_KEY[song]
    here = os.path.dirname(os.path.abspath(__file__))
    paths = [os.path.join(here, n + ".py") for n in (song, song.replace("_", "-"))]
    src = next((open(f, encoding="utf-8").read() for f in paths if os.path.exists(f)), None)
    if src is None:
        return key
    m = re.search(r"^KEY_CHANGE\s*=\s*(-?\d+)", src, re.M)
    if not m or int(m.group(1)) == 0:
        return key
    minor = key.endswith("m")
    return NOTES[(PITCH[key[:-1] if minor else key] + int(m.group(1))) % 12] + ("m" if minor else "")


def pitch_share(x, sr):
    """How much of the 300-3000 Hz peaks fall on the 3 strongest pitch classes: about .33-.39 for drums (noise has no
    key), .48-.66 for the sung bodies of our songs (18 November). An end above .44 carries pitch: keys, pads, voices."""
    f, _, z = signal.stft(x, sr, nperseg=8192, noverlap=6144)
    band = (f >= 300) & (f <= 3000)
    f, p = f[band], np.abs(z[band]) ** 2
    peak = (p > np.roll(p, 1, 0)) & (p > np.roll(p, -1, 0))
    pc = np.round(12 * np.log2(f / 440)).astype(int) % 12
    c = np.array([(p * peak)[pc == k].sum() for k in range(12)])
    return float(np.sort(c / c.sum())[-3:].sum())


def check(path, bpm, bars):
    x, sr = master.read(path)
    tp = 20 * np.log10(e.true_peak(x).max())
    lufs = e.integrated_lufs(x)
    phase = master.beat_phase(x, sr, bpm) * 1000
    beat = 60000 / bpm
    grid = min(phase, beat - phase)                        # ms off the grid (either side of the beat)
    bar = 240 / bpm
    mid = signal.sosfilt(signal.butter(4, [300, 3000], btype="band", fs=sr, output="sos"), x.mean(1))
    def share_mid(t0, t1):
        a = slice(int(t0 * sr), int(t1 * sr))
        return np.mean(mid[a] ** 2) / (np.mean(x[a].mean(1) ** 2) + 1e-12)
    music = share_mid(32 * bar, (bars - 32) * bar)
    intro = share_mid(0, 15.5 * bar) / music
    outro = share_mid((bars - 15.5) * bar, bars * bar) / music
    problems = []
    length = len(x) / sr
    if not bars * bar - .5 < length < bars * bar + 4:      # the bars plus the reverb's tail (2 s): not a preview
        problems.append(f"{length:.1f} s long, {bars} bars are {bars * bar:.1f} s")
    if tp > -1.0:
        problems.append(f"true peak {tp:+.1f} dBTP")
    if grid > 10:
        problems.append(f"{grid:.0f} ms off the grid")
    # drums only: little of the mid band, or (distorted drums are mid-heavy) no pitch in it
    end = lambda t0, t1: x[int(t0 * sr):int(t1 * sr)].mean(1)
    if intro > .5 and pitch_share(end(0, 15.5 * bar), sr) > .44:
        problems.append("the intro is not drums only")
    if outro > .5 and pitch_share(end((bars - 15.5) * bar, bars * bar), sr) > .44:
        problems.append("the outro is not drums only")
    return dict(tp=tp, lufs=lufs, grid=grid, length=len(x) / sr, problems=problems)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="song scripts, comma separated")
    ap.add_argument("--use", action="append", default=[], help="SONG=FILE: this file instead of our render")
    a = ap.parse_args()
    use = dict(u.split("=", 1) for u in a.use)
    only = set(a.only.split(",")) if a.only else None
    known = {script_of(row[0]) for row in share.SONGS}
    wrong = ((only or set()) | set(use)) - known       # a name not in share.SONGS wrote nothing, without a word
    if wrong:
        raise SystemExit(f"not in share.SONGS: {', '.join(sorted(wrong))} (the names: {', '.join(sorted(known))})")
    os.makedirs(OUT, exist_ok=True)
    written = []
    tracklist = os.path.join(OUT, "tracklist.txt")
    kept = {}      # --only: the other songs keep their line (and their file)
    if only and os.path.exists(tracklist):
        kept = {l[:2]: l for l in open(tracklist, encoding="utf-8").read().splitlines() if l[:2].isdigit()}
    lines = ["Track list for the DJ: 16-bit 44.1 kHz WAV, the beat grid at sample 0, 16 bars of drums at each end.",
             ""]
    for n, (wav, title, day, bpm, key, bars) in enumerate(share.SONGS, 1):
        song = script_of(wav)
        if only and song not in only:
            if f"{n:02d}" in kept and any(f.startswith(f"{n:02d} ") for f in os.listdir(OUT)):
                lines.append(kept[f"{n:02d}"])
            continue
        src = use.get(song, os.path.join(share.RENDERS, wav))
        if not os.path.exists(src):
            print(f"skip {title}: {src} not rendered")
            if f"{n:02d}" in kept and any(f.startswith(f"{n:02d} ") for f in os.listdir(OUT)):
                lines.append(kept[f"{n:02d}"])                  # --only: its old file stays, so its line does too
            continue
        cam = CAMELOT.get(key, key)
        keys = f"{cam} {key}"
        end = end_key(song, key)
        if end != key:
            keys += f" to {CAMELOT[end]} {end}"
        safe = "".join(c for c in title if c not in ':?*"<>|/\\')
        name = f"{n:02d} {safe} - {bpm} BPM - {keys.replace(' to ', ' to ')}.wav"
        dst = os.path.join(OUT, name)
        shutil.copyfile(src, dst)
        written.append(name)
        c = check(dst, bpm, bars)
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), song + ".py")
        if song not in use and os.path.exists(script) and os.path.getmtime(script) > os.path.getmtime(src):
            c["problems"].append("the render is older than its script (render it again, or touch the WAV)")
        m, s = divmod(c["length"], 60)
        flag = "OK" if not c["problems"] else "CHECK: " + "; ".join(c["problems"])
        lines.append(f"{n:02d}  {title:28s} {bpm} BPM  {keys:14s} {int(m)}:{s:04.1f}  {c['lufs']:5.1f} LUFS  "
                     f"{c['tp']:+.1f} dBTP  {day.split(': ')[1]}  [{flag}]"
                     + (f"  (source: {os.path.relpath(src, share.RENDERS)})" if song in use else ""))
        print(lines[-1], flush=True)
    # an older file of a song written now (another name: a new key, title or tempo) would be a second copy on the
    # stick; without --only, every WAV not written now goes
    for old in os.listdir(OUT):
        if old.endswith(".wav") and old not in written and (not only or any(old[:3] == w[:3] for w in written)):
            os.remove(os.path.join(OUT, old))
            print(f"removed the old {old}")
    with open(tracklist, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\n{OUT}: {sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)) / 1e6:.0f} MB")
