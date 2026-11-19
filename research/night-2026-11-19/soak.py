"""The VAE soak: the same ACE-Step synth (a 115 s turbo gag) again and again, VAE tiles of 512 and 1024 in turn,
while the CPU is busy (a song render in a loop, and a numpy load on 6 threads). Counts the runs that fail.

soak.py [RUNS] [until=07:00] [noload]
  RUNS        the number of runs (default: until the time, or forever)
  until=HH:MM no new run after this time
  noload      no load of our own (other work on the laptop is the load)
ACE_LOCK=FILE: take this GPU lock for each run, so other queues get their turns between runs.
"""
import json
import os
import shutil
import subprocess
import sys
import time

CODE = "/home/annejan/Projects/music/code"
ACE = "/home/annejan/Projects/acestep.cpp"
HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[1:]
RUNS = next((int(a) for a in ARGS if a.isdigit()), 10 ** 6)
UNTIL = next((a.split("=")[1] for a in ARGS if a.startswith("until=")), None)
LOAD = "noload" not in ARGS
LOCK = os.environ.get("ACE_LOCK")
D = os.path.join(HERE, "soak-long" if UNTIL else "soak")
os.makedirs(D, exist_ok=True)
REQ = os.path.join(D, "r.json")
shutil.copy(os.path.join(CODE, "renders/ace/gags/ad-s-grote-verdriet/request0.json"), REQ)
print(f"request: {json.load(open(REQ))['duration']} s, {json.load(open(REQ))['synth_model']}; load: {LOAD}; "
      f"until: {UNTIL}; lock: {LOCK}", flush=True)


def mem():
    m = dict(line.split(":") for line in open("/proc/meminfo"))
    return int(m["MemAvailable"].split()[0]) // 1024


def past(hhmm):
    """True once the clock is past HH:MM (a time after midnight, for a night run that starts before it)."""
    h, m = map(int, hhmm.split(":"))
    now = time.localtime()
    return now.tm_hour < 12 and (now.tm_hour, now.tm_min) >= (h, m)


loads = []
if LOAD:   # a song render in a loop, and numpy matrix products on 6 threads
    loads.append(subprocess.Popen(["bash", "-c", f"while :; do {CODE}/.venv/bin/python -W ignore "
                                  f"{CODE}/uptime_fever.py {D}/load.wav >/dev/null 2>&1; done"],
                                  start_new_session=True))
    loads.append(subprocess.Popen([f"{CODE}/.venv/bin/python", "-c",
                                   "import numpy as np\na=np.random.rand(1500,1500)\nwhile True: a=(a@a)/1500"],
                                  env=dict(os.environ, OMP_NUM_THREADS="6", OPENBLAS_NUM_THREADS="6"),
                                  start_new_session=True))
rows = []
try:
    if LOAD:
        time.sleep(20)                   # the load gets going
    for i in range(RUNS):
        if UNTIL and past(UNTIL):
            break
        # the first soak (30 runs, 02:42) crashed 1024 in 15 of 15 runs and 512 in none: the long soak runs only 512,
        # to see whether it holds over many runs (each crash resets the GPU, the desktop's too)
        chunk = 512 if (UNTIL or i % 2 == 0) else 1024
        log = os.path.join(D, f"run{i:03d}_{chunk}.log")
        cmd = [f"{ACE}/build/ace-synth", "--models", f"{ACE}/models", "--request", REQ, "--device", "Vulkan0",
               "--vae-chunk", str(chunk)]
        if LOCK:
            cmd = ["flock", LOCK, *cmd]
        t0, low = time.time(), mem()
        with open(log, "w") as fh:
            p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
            while p.poll() is None:
                low = min(low, mem())
                if time.time() - t0 > 900:        # with the lock, the wait for another queue's job counts too
                    p.kill()
                    break
                time.sleep(1)
        text = open(log, errors="replace").read()
        lost = "DeviceLost" in text
        ok = p.returncode == 0 and not lost
        rows.append((i, chunk, ok, lost, p.returncode, time.time() - t0, low))
        print(f"{time.strftime('%H:%M:%S')} run {i:3d}  tiles {chunk:4d}  {'ok' if ok else 'FAILED'}"
              f"{' (DeviceLost)' if lost else ''}  exit {p.returncode}  {time.time() - t0:5.1f} s  "
              f"RAM free at least {low} MB", flush=True)
        for f in os.listdir(D):
            if f.endswith(".wav") and f.startswith("r"):
                os.remove(os.path.join(D, f))
        if LOCK:
            time.sleep(3)                         # a gap for a job waiting on the lock
finally:
    for p in loads:
        try:
            os.killpg(p.pid, 15)
        except ProcessLookupError:
            pass
for chunk in (512, 1024):
    r = [x for x in rows if x[1] == chunk]
    if r:
        print(f"tiles {chunk}: {sum(x[2] for x in r)}/{len(r)} ok, {sum(x[3] for x in r)} DeviceLost, "
              f"{sum(x[5] for x in r) / len(r):.0f} s a run", flush=True)
