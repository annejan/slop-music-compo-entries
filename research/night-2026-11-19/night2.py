"""The second GPU queue (19 November, after night.py): the voice bank per genre, then the VAE soak until 07:00.
Waits for night.py (its PID) first. Every ACE-Step job takes the GPU lock (ACE_LOCK), so the dry-run rounds'
takes get turns between the soak's runs. The same memory guard as night.py (it is night.py's runner)."""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ["ACE_LOCK"] = os.path.join(HERE, "gpu.lock")
import night  # noqa: E402

first = int(sys.argv[1])
sys.argv = sys.argv[:1]          # night.main() reads its arguments as a job filter
while os.path.exists(f"/proc/{first}"):
    time.sleep(20)
night.JOBS = [("genre voices", night.PY + [f"{HERE}/genre_voices.py"], 60 * 60),
              ("VAE soak until 07:00", night.PY + [f"{HERE}/soak.py", "until=07:00", "noload"], 6 * 3600)]
os.makedirs(os.path.join(HERE, "jobs"), exist_ok=True)
night.main()
