#!/usr/bin/env python3
"""Voice trials: render Segfault with other voices and cut the vocal part (bars 24-58: verse, rap, pre-chorus,
chorus) into clips to compare by ear.

trials.py [--solo] [DIVA,RAPPER ...]     (default: every pair in PAIRS)

Writes renders/voices/NN_<diva>__<rapper>.wav, or with --solo the voices alone (a cappella, so the voices are
easy to tell apart) to renders/voices-solo/. Three renders run at once.
"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, ".venv", "bin", "python")
OUT = os.path.join(HERE, "renders", "voices")
FULL = os.path.join(HERE, ".cache", "trials")
BAR = 60 / 132 * 4
FIRST, LAST = 24, 58

SOLO = "--solo" in sys.argv
if SOLO:
    OUT = os.path.join(HERE, "renders", "voices-solo")

PAIRS = [
    ("en_US-hfc_female-medium", "en_US-ryan-high"),
    ("en_US-ljspeech-high", "en_US-joe-medium"),
    ("en_US-kristin-medium", "en_US-norman-medium"),
    ("en_US-lessac-high", "en_US-bryce-medium"),
    ("en_US-amy-medium", "en_US-john-medium"),
    ("en_GB-cori-high", "en_GB-alan-medium"),
    ("en_GB-jenny_dioco-medium", "en_US-hfc_male-medium"),
    ("mimic3:en_US/cmu-arctic_low#slt", "mimic3:en_US/cmu-arctic_low#bdl"),
    ("mimic3:en_US/vctk_low#p239", "mimic3:en_US/vctk_low#p226"),
    ("mimic3:en_US/cmu-arctic_low#clb", "mimic3:en_US/cmu-arctic_low#rms"),
    ("mimic3:en_US/hifi-tts_low#92", "mimic3:en_US/cmu-arctic_low#awb"),
]


def short(v):
    return v.replace(":", "-").replace("/", "-").replace("#", "-").replace("en_US-", "").replace("en_GB-", "gb-")


def one(job):
    k, (diva, rapper) = job
    name = f"{k:02d}_{short(diva)}__{short(rapper)}"
    full = os.path.join(FULL, name + ".wav")
    env = dict(os.environ, DIVA=diva, RAPPER=rapper, **({"SOLO": "vox"} if SOLO else {}))
    r = subprocess.run([PY, "-W", "ignore", os.path.join(HERE, "segfault.py"), full], env=env,
                       capture_output=True, text=True)
    if r.returncode:
        return f"{name}: FAILED\n{r.stderr[-800:]}"
    clip = os.path.join(OUT, name + ".wav")
    d = (LAST - FIRST) * BAR
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{FIRST * BAR:.4f}", "-t", f"{d:.4f}", "-i", full, "-af",
                    f"afade=t=in:d=0.3,afade=t=out:st={d - 1:.3f}:d=1", clip], check=True)
    os.remove(full)
    return f"{name}: ok"


if __name__ == "__main__":
    pairs = [tuple(a.split(",")) for a in sys.argv[1:] if a != "--solo"] or PAIRS
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(FULL, exist_ok=True)
    with ThreadPoolExecutor(3) as pool:
        start = len([f for f in os.listdir(OUT) if f.endswith(".wav")]) + 1
        for line in pool.map(one, enumerate(pairs, start)):
            print(line, flush=True)
