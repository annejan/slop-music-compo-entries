"""One MP3: for each weekend song, 16 bars from its first chorus: ours, the turbo polish, the SFT polish."""
import os
import sys

sys.path.insert(0, "/home/annejan/Projects/music/code")
import ace  # noqa: E402
import master  # noqa: E402
import share  # noqa: E402
import takes as T  # noqa: E402
import engine as e  # noqa: E402

SONGS = [("warm_boot", 48), ("packet_loss", 40), ("low_battery", 48), ("low_pass_love", 32), ("segfault", 48),
         ("blinky", 32), ("rhythm_of_the_badge", 32)]
parts = []
for song, bar in SONGS:
    n, wav, title, day, bpm, key, bars = ace.song_info(song)
    d = os.path.join(share.RENDERS, "produce", song)
    versions = [("Ours.", os.path.join(share.RENDERS, wav)), ("Turbo.", os.path.join(d, f"{song}-nm-p65.wav")),
                ("S F T.", os.path.join(d, f"{song}-nm-sft65.wav"))]
    parts.append(T.label(title + ".", .09))
    for name, path in versions:
        if not os.path.exists(path):
            print(f"{song}: no {path}", file=sys.stderr)
            continue
        x, _ = master.read(path)
        parts += [T.label(name, .06), T.lay(x, None, bpm, bar, 16, lead=0), T.gap(.5)]
    parts.append(T.gap(.5))
out = os.path.join(T.TAKES, "polish A-B (ours, turbo, SFT).mp3")
os.makedirs(T.TAKES, exist_ok=True)
print(T.listen(parts, out, "Polish A/B: ours, turbo, SFT"))
