"""One MP3: for each weekend song, 16 bars from its first chorus: ours, then ACE-Step re-singing our vocal stem
(ace.py --mode vocals, SFT: our melody and timing, its voice) at cover strength 0.85, 0.95 and 1.0."""
import os
import sys

sys.path.insert(0, "/home/annejan/Projects/music/code")
import ace  # noqa: E402
import master  # noqa: E402
import share  # noqa: E402
import takes as T  # noqa: E402

SONGS = [("packet_loss", 40), ("low_battery", 48), ("low_pass_love", 32), ("segfault", 48), ("blinky", 32),
         ("rhythm_of_the_badge", 32)]
parts = []
for song, bar in SONGS:
    n, wav, title, day, bpm, key, bars = ace.song_info(song)
    d = os.path.join(share.RENDERS, "ace", song)
    versions = [("Ours.", os.path.join(share.RENDERS, wav)), ("Point eight five.", os.path.join(d, "vocals-sft.wav")),
                ("Point nine five.", os.path.join(d, "vocals-sft-0.95-s1.wav")),
                ("One.", os.path.join(d, "vocals-sft-1-s1.wav"))]
    parts.append(T.label(title + ".", .09))
    for name, path in versions:
        if not os.path.exists(path):
            print(f"{song}: no {path}", file=sys.stderr)
            continue
        x, _ = master.read(path)
        parts += [T.label(name, .06), T.lay(x, None, bpm, bar, 16, lead=0), T.gap(.5)]
    parts.append(T.gap(.5))
print(T.listen(parts, os.path.join(T.TAKES, "ACE re-sings our melody (0.85, 0.95, 1.0).mp3"),
               "ACE re-sings our melody: 0.85, 0.95, 1.0"))
