#!/usr/bin/env python3
"""Produce a song section by section: our code track as the sketch, ACE-Step as the producer, and every section
tuned on its own. A project file (projects/<song>.toml) holds the knobs; a change re-runs only what it touches
(every ACE-Step result is cached by its request).

produce.py SONG [--project FILE]      writes renders/produce/<song>/<song>.wav, the MP3s and an ear report
produce.py SONG --map                 the song's sections from its lyric sheet, with their bars: to write a project

projects/rhythm_of_the_badge.toml:

    take = "cover"           # the whole song first: "cover" (ACE-Step re-plays our render) or "ours"
    strength = 0.85          # cover: how closely ACE-Step follows our render (1 = closely)
    model = "base"           # base (50 steps) or turbo (8)
    seed = 1

    [[section]]              # then section by section, in order
    name = "rap"
    bars = [48, 56]          # from bar 48 up to bar 56
    use = "ours"             # ours: our own render here (the machine flow), crossfaded in
                             # repaint: ACE-Step makes this part again on the take so far, with each seed in
                             #          `seeds`; the ear picks the take with the most lyric words
                             # take: keep the take (the default)
    seeds = [2, 3, 4]

The DJ intro and outro (16 bars of drums at each end) are always ours. The result is mastered like ours (-9 LUFS
for eurodance and drum and bass, -10 for house, -1.2 dBTP), and asr.py reports per section how many words come
through.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib

import numpy as np
from scipy import signal

import ace
import asr
import engine as e
import master
import share

HERE = os.path.dirname(os.path.abspath(__file__))


def section_words(sheet, bpm):
    """[(t0, t1, words)] from a lyric sheet: each [m:ss] section with the words sung in it."""
    out, cur = [], None
    for line in open(sheet, encoding="utf-8").read().splitlines():
        m = re.match(r"\[(\d+):(\d\d)\]\s*(.*)", line.strip())
        if m:
            cur = [int(m.group(1)) * 60 + int(m.group(2)), None, []]
            out.append(cur)
            rest = m.group(3)
            if ":" in rest:
                cur[2] += asr.words(re.sub(r"\(.*?\)", "", rest.split(":", 1)[1]))
        elif cur and ":" in line:
            cur[2] += asr.words(re.sub(r"\(.*?\)", "", line.split(":", 1)[1]))
    for a, b in zip(out, out[1:]):
        a[1] = b[0]
    if out:
        out[-1][1] = 10 ** 6
    return out


def heard_in(heard, t0, t1):
    return asr.words(" ".join(t for s, e_, t in heard if s < t1 and e_ > t0))


def score(heard, want):
    if not want:
        return 1.0
    import difflib
    got = sum(b.size for b in difflib.SequenceMatcher(a=want, b=heard, autojunk=False).get_matching_blocks())
    return got / len(want)


class Producer:
    def __init__(self, song, project, tag=None):
        self.song = song
        self.tag = tag
        self.p = project
        self.n, self.wav, self.title, self.day, self.bpm, self.key, self.bars = ace.song_info(song)
        self.bar = 240 / self.bpm
        self.dir = os.path.join(share.RENDERS, "produce", song)
        self.cache = os.path.join(self.dir, "cache")
        os.makedirs(self.cache, exist_ok=True)
        self.ours_path = ace.render(song, self.wav)
        self.ours, _ = master.read(self.ours_path)
        self.lyrics = ace.ace_lyrics(self.n)
        sheets = [f for f in os.listdir(share.LYRICS) if f.startswith(f"{self.n:02d}-")]
        self.sheet = os.path.join(share.LYRICS, sheets[0]) if sheets else None

    def synth(self, req, src):
        """An ACE-Step result for this request and source file, cached; returned at 44.1 kHz, lined up with ours."""
        src_hash = hashlib.sha1(open(src, "rb").read()).hexdigest()[:12]
        key = hashlib.sha1((json.dumps(req, sort_keys=True) + src_hash).encode()).hexdigest()[:16]
        out = os.path.join(self.cache, key + ".wav")
        if not os.path.exists(out):
            path = os.path.join(self.cache, key + ".json")
            json.dump(req, open(path, "w"), indent=1)
            log = os.path.join(self.cache, key + ".log")
            with open(log, "w") as fh:
                r = subprocess.run([os.path.join(ace.ACESTEP, "build", "ace-synth"), "--models", ace.MODELS,
                                    "--request", path, "--src-audio", src, "--device", "Vulkan0"],
                                   stdout=fh, stderr=subprocess.STDOUT)
            if r.returncode:
                sys.exit(f"ACE-Step failed, see {log}")
            os.replace(os.path.join(self.cache, key + "0.wav"), out)
        x, sr = master.read(out)
        lag = master.lag_to(x, sr, self.ours, start=16 * self.bar)
        if sr != e.SR:
            g = np.gcd(sr, e.SR)
            x = signal.resample_poly(x, e.SR // g, sr // g, axis=0)
        i = int(round(lag * e.SR))
        x = x[i:] if i >= 0 else np.concatenate([np.zeros((-i, 2)), x])
        n = len(self.ours)
        return np.concatenate([x, np.zeros((max(n - len(x), 0), 2))])[:n]

    def request(self, **kw):
        return {"caption": self.p.get("caption", ace.CAPTIONS.get(self.song, self.day.split(": ")[1])),
                "lyrics": self.lyrics, "bpm": self.bpm, "keyscale": ace.KEYS.get(self.key, self.key),
                "timesignature": "4", "vocal_language": "en", "seed": self.p.get("seed", 1), "output_format": "wav16",
                **ace.SYNTH[self.p.get("model", "base")], **kw}

    def splice(self, x, y, b0, b1):
        """y in place of x from bar b0 up to bar b1, level matched, a one-beat equal-power crossfade at each end."""
        i0, i1 = int(round(b0 * self.bar * e.SR)), int(round(b1 * self.bar * e.SR))
        f = int(round(self.bar / 4 * e.SR))
        rms = lambda a: np.sqrt(np.mean(a[i0:i1] ** 2) + 1e-12)
        y = y * (rms(x) / rms(y))
        out = x.copy()
        u = np.linspace(0, 1, f)[:, None]
        fin, fout = np.sin(u * np.pi / 2), np.cos(u * np.pi / 2)
        out[i0:i0 + f] = x[i0:i0 + f] * fout + y[i0:i0 + f] * fin
        out[i0 + f:i1 - f] = y[i0 + f:i1 - f]
        out[i1 - f:i1] = y[i1 - f:i1] * fout + x[i1 - f:i1] * fin
        return out

    def write_tmp(self, x, name):
        path = os.path.join(self.cache, name)
        master.write(path, np.clip(x, -1, 1))
        return path

    def run(self):
        take = self.p.get("take", "cover")
        if take == "cover":
            x = self.synth(self.request(task_type="cover-nofsq", audio_cover_strength=self.p.get("strength", .85)),
                           self.ours_path)
            print(f"take: ACE-Step cover, strength {self.p.get('strength', .85)}", flush=True)
        else:
            x = self.ours.copy()
            print("take: ours", flush=True)
        for sec in self.p.get("section", []):
            b0, b1 = sec["bars"]
            use = sec.get("use", "take")
            if use == "ours":
                x = self.splice(x, self.ours, b0, b1)
            elif use == "repaint":
                src = self.write_tmp(x, "current.wav")
                best = (self.section_score(x, b0, b1), None)       # what is there now: a repaint must beat it
                print(f"  {sec.get('name', '')} bars {b0}-{b1}, now: ear {best[0]:.0%}", flush=True)
                for seed in sec.get("seeds", [2, 3]):
                    y = self.synth(self.request(task_type="repaint", repainting_start=b0 * self.bar,
                                                repainting_end=b1 * self.bar, seed=seed), src)
                    s = self.section_score(y, b0, b1)
                    print(f"  {sec.get('name', '')} bars {b0}-{b1}, seed {seed}: ear {s:.0%}", flush=True)
                    if s > best[0]:
                        best = (s, y)
                if best[1] is None:
                    use = "repaint (no seed beat it: kept)"
                else:
                    x = self.splice(x, best[1], b0, b1)
            print(f"section {sec.get('name', '')} (bars {b0}-{b1}): {use}", flush=True)
        x = master.splice_dj(x, self.ours, self.bpm, self.bars)
        lufs = -10.0 if "house" in self.day else -9.0
        x = master.master(x, lufs)
        name = self.song + (f"-{self.tag}" if self.tag else "")
        out = os.path.join(self.dir, f"{name}.wav")
        master.write(out, x)
        label = "produced" + (f", {self.tag}" if self.tag else "")
        share.encode(out, os.path.join(self.dir, f"{self.title} ({label}, radio edit).mp3"),
                     ["-metadata", f"title={self.title}", "-metadata", "artist=sunA"], [],
                     share.radio_window(self.bpm, self.bars))
        print(self.report(out))
        return out

    def section_score(self, y, b0, b1):
        """The share of the lyric words heard in bars b0..b1 of y."""
        if not self.sheet:
            return 0.0
        path = self.write_tmp(y, "score.wav")
        heard = asr.hear(path)
        t0, t1 = b0 * self.bar, b1 * self.bar
        want = [w for s0, s1, ws in section_words(self.sheet, self.bpm) if s0 < t1 - 1 and s1 > t0 + 1 for w in ws]
        return score(heard_in(heard, t0 - .5, t1 + .5), want)

    def report(self, path):
        if not self.sheet:
            return "no lyric sheet: no ear report"
        heard = asr.hear(path)
        lines = [f"ear per section ({os.path.basename(path)}):"]
        for t0, t1, want in section_words(self.sheet, self.bpm):
            if want:
                s = score(heard_in(heard, t0, min(t1, t0 + 60)), want)
                lines.append(f"  bar {t0 / self.bar:5.1f}: {s:4.0%}  {' '.join(want[:8])}...")
        return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song")
    ap.add_argument("--project", help="default projects/<song>.toml (or just a cover take)")
    ap.add_argument("--map", action="store_true", help="print the sections and their bars, then stop")
    ap.add_argument("--tag", help="a name for this variant: renders/produce/<song>/<song>-<tag>.wav")
    a = ap.parse_args()
    if a.map:
        n, wav, title, day, bpm, key, bars = ace.song_info(a.song)
        sheets = [f for f in os.listdir(share.LYRICS) if f.startswith(f"{n:02d}-")]
        bar = 240 / bpm
        print(f"{title}: {bpm} BPM, {bars} bars ({bar:.3f} s a bar)")
        for line in open(os.path.join(share.LYRICS, sheets[0]), encoding="utf-8").read().splitlines():
            m = re.match(r"\[(\d+):(\d\d)\]\s*(.*)", line.strip())
            if m:
                t = int(m.group(1)) * 60 + int(m.group(2))
                print(f"  bar {round(t / bar):3d}  [{m.group(1)}:{m.group(2)}]  {m.group(3)[:70]}")
        return
    path = a.project or os.path.join(HERE, "projects", a.song + ".toml")
    project = tomllib.load(open(path, "rb")) if os.path.exists(path) else {}
    Producer(a.song, project, a.tag).run()


if __name__ == "__main__":
    main()
