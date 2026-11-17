#!/usr/bin/env python3
"""Encode the renders for sharing in a chat app such as Signal: MP3 at 320 kbit/s with title tags, about 9 MB per
song (Signal's limit is 100 MB), plays on every phone. The lyric sheets from lyrics/ go in the tags and next to them.

share.py            writes renders/share/NN Title (BPM, key).mp3 for every song that is rendered,
                    and renders/share/NN Title - lyrics.txt
"""
import glob
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(HERE, "renders")
LYRICS = os.path.join(os.path.dirname(HERE), "lyrics")
OUT = os.path.join(RENDERS, "share")

# file, title, day, BPM, key
SONGS = [
    ("warm-boot_120bpm_Am.wav", "Warm Boot", "Saturday: 90's mellow house", 120, "Am"),
    ("packet-loss_122bpm_Fm.wav", "Packet Loss (Of Love)", "Saturday: 90's mellow house", 122, "Fm"),
    ("low-battery_120bpm_Dm.wav", "Low Battery Lullaby", "Saturday: 90's mellow house", 120, "Dm"),
    ("low-pass-love_122bpm_Am.wav", "Low Pass Love", "Saturday: 90's mellow house", 122, "Am"),
    ("segfault_132bpm_Am.wav", "Segfault (In My Heart)", "Sunday: eurodance", 132, "Am"),
    ("blinky_132bpm_D.wav", "Blinky (The LED Song)", "Sunday: eurodance", 132, "D"),
    ("rhythm-of-the-badge_134bpm_Em.wav", "The Rhythm Of The Badge", "Sunday: eurodance", 134, "Em"),
]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for n, (wav, title, day, bpm, key) in enumerate(SONGS, 1):
        src = os.path.join(RENDERS, wav)
        if not os.path.exists(src):
            print(f"skip {wav}: not rendered")
            continue
        dst = os.path.join(OUT, f"{n:02d} {title} ({bpm} BPM, {key}).mp3")
        sheets = glob.glob(os.path.join(LYRICS, f"{n:02d}-*.txt"))
        words = ["-metadata", "lyrics=" + open(sheets[0], encoding="utf-8").read()] if sheets else []
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-c:a", "libmp3lame", "-b:a", "320k",
                        "-metadata", f"title={title}", "-metadata", "artist=Claude (AI slop music compo)",
                        "-metadata", f"album=slop-music-compo-entries", "-metadata", f"comment={day}",
                        "-metadata", f"genre={day.split(': ')[1]}", "-metadata", f"track={n}/{len(SONGS)}",
                        "-metadata", f"TBPM={bpm}", "-metadata", f"TKEY={key}", *words, "-id3v2_version", "3", dst],
                       check=True)
        print(f"{os.path.basename(dst)}: {os.path.getsize(dst) / 1e6:.1f} MB")
        for txt in sheets:
            shutil.copyfile(txt, os.path.join(OUT, f"{n:02d} {title} - lyrics.txt"))
