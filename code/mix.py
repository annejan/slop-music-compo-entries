#!/usr/bin/env python3
"""A day's songs mixed as the DJ would: one tempo for the set, each next song over the 16-bar drums-only outro of
the one before, the lows swapped 4 bars before the end. To hear whether the songs mix (beat grid, drums-only ends,
keys), and to listen to a set on the phone.

mix.py saturday [--order 1,3,2,4] [--tempo 121] [--use packet_loss=renders/produce/packet_loss/packet_loss.wav]

The tempo is the median of the day's tempos unless given; each song is played faster or slower to it (varispeed,
as on a turntable or a CDJ without key lock: the pitch moves too). Per transition the report gives the tempo change,
the pitch change, and whether the keys go together on the Camelot wheel (the same number, or one step around with
the same letter, or the same number with the other letter). --order auto: the order with the fewest clashes.
Writes renders/dj/<day> set.mp3.
"""
import argparse
import itertools
import os

import numpy as np
from scipy import signal

import dj
import engine as e
import master
import share

DJ_BARS = share.DJ_BARS
SWAP = 4                                    # the lows of the next song come in this many bars before the outro ends


def camelot_ok(a, b):
    """True when Camelot keys a and b (like "8A") go together."""
    na, la, nb, lb = int(a[:-1]), a[-1], int(b[:-1]), b[-1]
    step = min((na - nb) % 12, (nb - na) % 12)
    return (la == lb and step <= 1) or (step == 0)


def shifted(cam, semitones):
    """A Camelot key moved by a whole number of semitones (7 steps around the wheel per semitone)."""
    n, l = int(cam[:-1]), cam[-1]
    return f"{(n - 1 + 7 * semitones) % 12 + 1}{l}"


def varispeed(x, ratio):
    """x played `ratio` times as fast (shorter, higher)."""
    up, down = 1000, int(round(1000 * ratio))
    g = np.gcd(up, down)
    return signal.resample_poly(x, up // g, down // g, axis=0)


def best_order(songs, tempo):
    """The playing order with the fewest key clashes between the end of one song and the start of the next (the
    first listed song stays first: it opens the set)."""
    def keys(row):
        song, semis = dj.script_of(row[0]), round(12 * np.log2(tempo / row[3]))
        return shifted(dj.CAMELOT[row[4]], semis), shifted(dj.CAMELOT[dj.END_KEY.get(song, row[4])], semis)
    def clashes(order):
        return sum(not camelot_ok(keys(a[1])[1], keys(b[1])[0]) for a, b in zip(order, order[1:]))
    return min(([songs[0], *rest] for rest in itertools.permutations(songs[1:])), key=clashes)


def day_songs(day):
    return [(n, row) for n, row in enumerate(share.SONGS, 1) if row[2].lower().startswith(day.lower())]


def build(songs, tempo, use):
    """The mix and the report lines. songs: [(n, row)] in playing order."""
    bar = int(round(240 / tempo * e.SR))
    lows = lambda a: e.lowpass(a, 150, order=4)
    out, at, lines, prev = None, 0, [], None
    for n, (wav, title, day, bpm, key, bars) in songs:
        song = dj.script_of(wav)
        src = use.get(song, os.path.join(share.RENDERS, wav))
        x, sr = master.read(src)
        if sr != e.SR:
            raise ValueError(f"{src}: {sr} Hz, expected {e.SR}")
        x = varispeed(x, tempo / bpm)[:bars * bar]
        semis = 12 * np.log2(tempo / bpm)
        cam = dj.CAMELOT[key]
        end = dj.CAMELOT[dj.END_KEY.get(song, key)]
        heard_cam = shifted(cam, round(semis))
        if prev is None:
            out = np.zeros((sum(r[5] for _, r in songs) * bar, 2))
            out[:len(x)] = x
            at = 0
            lines.append(f"{title}: {bpm} BPM, {tempo / bpm - 1:+.1%} ({semis:+.2f} semitones), {key} {cam}")
        else:
            p_title, p_end, p_bars = prev
            at += (p_bars - DJ_BARS) * bar                          # the next song starts on the outro's first bar
            ov = DJ_BARS * bar
            sw = (DJ_BARS - SWAP) * bar
            prev_part = out[at:at + ov].copy()
            new = x[:ov].copy()
            # the lows: the old song's until the swap, then the new song's
            new[:sw] -= lows(new)[:sw]
            pl = lows(prev_part)
            prev_part[sw:] -= pl[sw:]
            # the old song fades over the last bars of the overlap, the new song is in from the start
            fade = np.ones(ov)
            fade[sw:] = np.cos(np.linspace(0, np.pi / 2, ov - sw))
            out[at:at + ov] = prev_part * fade[:, None] + new
            out[at + ov:at + len(x)] = x[ov:]
            fit = "fits" if camelot_ok(p_end, heard_cam) else "CLASH"
            lines.append(f"  -> {title}: {bpm} BPM, {tempo / bpm - 1:+.1%} ({semis:+.2f} semitones), "
                         f"{key} {cam} (heard as {heard_cam}); from {p_end}: {fit}")
        prev = (title, shifted(end, round(semis)), bars)
    total = at + len(x)
    return out[:total], lines


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("day", help="saturday, sunday or rehearsal")
    ap.add_argument("--order", help="the songs' numbers (from share.SONGS), comma separated, or auto: the fewest "
                                    "key clashes")
    ap.add_argument("--tempo", type=float, help="the set's tempo (default: the median of the songs)")
    ap.add_argument("--use", action="append", default=[], help="SONG=FILE: this file instead of our render")
    ap.add_argument("--tag", default="", help="added to the file name")
    a = ap.parse_args()
    songs = day_songs(a.day)
    tempo = a.tempo or float(np.median([r[3] for _, r in songs]))
    if a.order == "auto":
        songs = best_order(songs, tempo)
    elif a.order:
        by_n = dict(songs)
        songs = [(int(k), by_n[int(k)]) for k in a.order.split(",")]
    use = {k: os.path.abspath(v) for k, v in (u.split("=", 1) for u in a.use)}
    x, lines = build(songs, tempo, use)
    x = master.master(x, -10.0 if "house" in songs[0][1][2] else -9.0)
    day = songs[0][1][2].split(":")[0]
    out_dir = os.path.join(share.RENDERS, "dj")
    os.makedirs(out_dir, exist_ok=True)
    wav = os.path.join(out_dir, f"{day} set{a.tag}.wav")
    master.write(wav, x)
    mp3 = wav[:-4] + ".mp3"
    share.encode(wav, mp3, ["-metadata", f"title={day} set{a.tag} ({tempo:g} BPM)", "-metadata", "artist=sunA"],
                 [], None)
    m, s = divmod(len(x) / e.SR, 60)
    print(f"{day} set at {tempo:g} BPM, {int(m)}:{s:04.1f}")
    print("\n".join(lines))
    print("  (the joins are 16 bars of drums only: a key clash only shows when the drums carry a pitch)")
    for k, v in use.items():
        print(f"  ({k}: {os.path.relpath(v, share.RENDERS)})")
    print(mp3)
