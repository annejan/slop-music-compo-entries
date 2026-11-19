"""The second GPU queue (19 November, after night.py): ACE-Step re-singing our vocal stems at cover strength 0.95
and 1.0 (the user, 01:58: a free ACE take over our voices "improvises like an idiot"; can its voice keep our
melody?), the voices per genre, then the VAE soak until 07:00. Waits for night.py (its PID) first. Every ACE-Step
job takes the GPU lock (ACE_LOCK; ace.py as a whole), so the dry-run rounds' takes get turns. The same memory guard
as night.py (it is night.py's runner)."""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
LOCK = os.path.join(HERE, "gpu.lock")
os.environ["ACE_LOCK"] = LOCK
import night  # noqa: E402

first = int(sys.argv[1])
sys.argv = sys.argv[:1]          # night.main() reads its arguments as a job filter
while os.path.exists(f"/proc/{first}"):
    time.sleep(20)
jobs = []
for song in ("packet_loss", "low_battery", "low_pass_love", "segfault", "blinky", "rhythm_of_the_badge"):
    for strength in ("0.95", "1.0"):
        jobs.append((f"vocals sft {strength} {song}", ["flock", LOCK] + night.PY + [
            f"{night.CODE}/ace.py", song, "--mode", "vocals", "--model", "sft", "--strength", strength], 20 * 60))
jobs += [("vocals A-B", night.PY + [f"{HERE}/vocals_ab.py"], 10 * 60),
         ("genre voices", night.PY + [f"{HERE}/genre_voices.py"], 60 * 60),
         ("VAE soak until 07:00", night.PY + [f"{HERE}/soak.py", "until=07:00", "noload"], 6 * 3600)]
night.JOBS = jobs
os.makedirs(os.path.join(HERE, "jobs"), exist_ok=True)
night.main()
