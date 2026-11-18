#!/usr/bin/env python3
"""The files for the DJ: every song as a 16-bit 44.1 kHz WAV with its tempo and key (Camelot) in the name, checked,
and a track list. Copy renders/dj/ to the USB stick (FAT32: the names avoid : ? * " < > | and stay short).

dj.py [--only warm_boot,segfault] [--use rhythm_of_the_badge=renders/ace/rhythm_of_the_badge/x.wav]

Checks per song: the true peak (at most -1.0 dBTP), the loudness, the beat grid at sample 0 (the kick on the
grid), and the 16 bars at each end drums only (little of the 300-3000 Hz band, where keys, pads and voices are).
"""
import argparse
import os
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
# songs that end in another key (a key change for the last chorus)
END_KEY = {"segfault": "Bm", "blinky": "E", "rhythm_of_the_badge": "F#m"}


def script_of(wav):
    return wav.split("_")[0].replace("-", "_")


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
    if tp > -1.0:
        problems.append(f"true peak {tp:+.1f} dBTP")
    if grid > 10:
        problems.append(f"{grid:.0f} ms off the grid")
    if intro > .5:
        problems.append("the intro is not drums only")
    if outro > .5:
        problems.append("the outro is not drums only")
    return dict(tp=tp, lufs=lufs, grid=grid, length=len(x) / sr, problems=problems)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="song scripts, comma separated")
    ap.add_argument("--use", action="append", default=[], help="SONG=FILE: this file instead of our render")
    a = ap.parse_args()
    use = dict(u.split("=", 1) for u in a.use)
    only = set(a.only.split(",")) if a.only else None
    os.makedirs(OUT, exist_ok=True)
    lines = ["Track list for the DJ: 16-bit 44.1 kHz WAV, the beat grid at sample 0, 16 bars of drums at each end.",
             ""]
    for n, (wav, title, day, bpm, key, bars) in enumerate(share.SONGS, 1):
        song = script_of(wav)
        if only and song not in only:
            continue
        src = use.get(song, os.path.join(share.RENDERS, wav))
        if not os.path.exists(src):
            print(f"skip {title}: {src} not rendered")
            continue
        cam = CAMELOT.get(key, key)
        keys = f"{cam} {key}"
        if song in END_KEY:
            keys += f" to {CAMELOT[END_KEY[song]]} {END_KEY[song]}"
        safe = "".join(c for c in title if c not in ':?*"<>|/\\')
        name = f"{n:02d} {safe} - {bpm} BPM - {keys.replace(' to ', ' to ')}.wav"
        dst = os.path.join(OUT, name)
        shutil.copyfile(src, dst)
        c = check(dst, bpm, bars)
        m, s = divmod(c["length"], 60)
        flag = "OK" if not c["problems"] else "CHECK: " + "; ".join(c["problems"])
        lines.append(f"{n:02d}  {title:28s} {bpm} BPM  {keys:14s} {int(m)}:{s:04.1f}  {c['lufs']:5.1f} LUFS  "
                     f"{c['tp']:+.1f} dBTP  {day.split(': ')[1]}  [{flag}]"
                     + (f"  (source: {os.path.relpath(src, share.RENDERS)})" if song in use else ""))
        print(lines[-1], flush=True)
    with open(os.path.join(OUT, "tracklist.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\n{OUT}: {sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)) / 1e6:.0f} MB")
