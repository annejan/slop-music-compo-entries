"""The night queue (19 November): one job at a time, the memory watched.

Before each job: wait until at least 6 GB of RAM is free (up to 20 min, else skip the job). During a job: if free
RAM falls under 1.5 GB, or the job runs past its time, kill its whole process group and go on. Every 10 s the free
RAM, free swap and GPU memory go to mem.csv. Each ACE-Step step is its own process, so the models leave memory
after every take.
"""
import os
import signal
import subprocess
import sys
import threading
import time

CODE = "/home/annejan/Projects/music/code"
HERE = os.path.dirname(os.path.abspath(__file__))
PY = [f"{CODE}/.venv/bin/python", "-W", "ignore"]
GTT = [f"/sys/class/drm/{c}/device/mem_info_gtt_used" for c in os.listdir("/sys/class/drm")
       if os.path.exists(f"/sys/class/drm/{c}/device/mem_info_gtt_used")][0]
VRAM = GTT.replace("gtt", "vram")
NEED_MB, FLOOR_MB = 6000, 1500


def meminfo():
    m = dict(line.split(":") for line in open("/proc/meminfo"))
    return int(m["MemAvailable"].split()[0]) // 1024, int(m["SwapFree"].split()[0]) // 1024


def gpu():
    return int(open(GTT).read()) >> 20, int(open(VRAM).read()) >> 20


def sampler(stop):
    with open(os.path.join(HERE, "mem.csv"), "a") as fh:
        fh.write("time,ram_free_mb,swap_free_mb,gtt_used_mb,vram_used_mb,job\n")
        while not stop.is_set():
            a, s = meminfo()
            g, v = gpu()
            fh.write(f"{time.strftime('%H:%M:%S')},{a},{s},{g},{v},{CURRENT[0]}\n")
            fh.flush()
            stop.wait(10)


CURRENT = ["-"]
S = "mid 1990s eurodance, a male rapper, confident rhythmic flow, clear words"
HOUSE = "early 1990s deep house, a powerful soulful female house diva, warm and smooth, gospel runs"
EURO = "mid 1990s eurodance, a bright powerful female dance diva, soaring chorus vocals"


def singer(song, bar, lines, caption, tag="Chorus"):
    return (f"singer {song} bar {bar}", PY + [f"{CODE}/takes.py", song, "--bar", str(bar), "--lines", "|".join(lines),
                                              "--caption", caption, "--tag", tag], 15 * 60)


JOBS = [
    singer("warm_boot", 48, ["Warm boot, baby", "All night long"] * 2, HOUSE),
    singer("packet_loss", 40, ["Packet loss of love", "Say it once again", "Packet loss of love", "Say it once again",
                               "Ping me when you're ready", "I'll be waiting up", "Packet loss of love"],
           "early 1990s deep house, a soulful female and male vocal duet, warm and smooth"),
    singer("low_battery", 48, ["Low battery, low, low", "Ten percent", "Ch-ch-ch-charging", "Sleep mode"] * 2,
           "early 1990s deep house, a breathy dreamy soulful female singer, sleepy"),
    singer("low_pass_love", 32, ["Low pass love", "Open up the filter", "Low pass love", "Let the highs come through"],
           "late 1990s French house, a smooth male disco soul singer with falsetto"),
    singer("segfault", 48, ["Segfault in my heart", "Tearing me apart", "Segfault in my heart",
                            "Reboot from the start"] * 2, EURO),
    singer("blinky", 32, ["Blink, blink, blinky", "On and off all night", "Blink, blink, blinky",
                          "Red and green and white", "Toggle me, baby", "GPIO high", "Blink, blink, blinky",
                          "Light up the sky"], "late 1990s bubblegum eurodance, a bright playful high female pop singer"),
    singer("rhythm_of_the_badge", 32, ["Feel the rhythm of the badge", "Feel the rhythm of the badge",
                                       "Flash me, flash me, one more time", "Feel the rhythm of the badge"], EURO),
    singer("segfault", 32, ["S-E-G-F-A-U-L-T!", "You overflowed the buffer that you gave to me.",
                            "Null pointer, no answer, the stack is on fire.",
                            "I free the same love twice, I'm a double free liar.",
                            "Check the bounds, check the bounds, but you never do.",
                            "Valgrind in the morning, it was always you.", "Get up, get down, get the backtrace now!",
                            "Segfault, segfault, let me show you how!"], S, "Rap"),
    singer("blinky", 48, ["Hello world!", "Hello world!", "Put your hands up, everybody, set the pin to out!",
                          "Delay one second, now everybody shout!", "Hey! Hey!", "Hey! Hey! Hey! Hey!"], S, "Rap"),
    singer("rhythm_of_the_badge", 48, ["Plug it in, USB,", "let the firmware flow!", "From the C6 to the P4,",
                                       "here we go!", "Badgelink, app store,", "upload complete.",
                                       "Now the whole tent is moving", "to the beat!"], S, "Rap"),
    ("voice menu", PY + [f"{CODE}/takes.py", "--menu"], 45 * 60),
]
RENDERS = {"warm_boot": "warm-boot_120bpm_Am.wav", "packet_loss": "packet-loss_122bpm_Fm.wav",
           "low_battery": "low-battery_120bpm_Dm.wav", "low_pass_love": "low-pass-love_122bpm_Am.wav",
           "segfault": "segfault_132bpm_Am.wav", "blinky": "blinky_132bpm_D.wav",
           "rhythm_of_the_badge": "rhythm-of-the-badge_134bpm_Em.wav"}
JOBS.append(("polish turbo warm_boot", PY + [f"{CODE}/produce.py", "warm_boot", "--project",
                                             f"{CODE}/projects/_polish.toml", "--tag", "nm-p65", "--ours",
                                             f"{CODE}/renders/warm-boot_120bpm_Am.wav"], 25 * 60))
for song, wav in RENDERS.items():
    JOBS.append((f"polish sft {song}", PY + [f"{CODE}/produce.py", song, "--project",
                                             f"{CODE}/projects/_polish_sft.toml", "--tag", "nm-sft65", "--ours",
                                             f"{CODE}/renders/{wav}"], 25 * 60))
JOBS += [("polish A-B", PY + [f"{HERE}/polish_ab.py"], 10 * 60),
         ("VAE soak", PY + [f"{HERE}/soak.py", "30"], 60 * 60)]


def wait_for_memory(name):
    t0 = time.time()
    while meminfo()[0] < NEED_MB:
        if time.time() - t0 > 20 * 60:
            return False
        time.sleep(15)
    return True


def kill(p):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(p.pid, sig)
        except ProcessLookupError:
            return
        for _ in range(10):
            if p.poll() is not None:
                return
            time.sleep(1)


def main():
    only = sys.argv[1:]
    stop = threading.Event()
    threading.Thread(target=sampler, args=(stop,), daemon=True).start()
    log = open(os.path.join(HERE, "night.log"), "a", buffering=1)
    log.write(f"=== {time.strftime('%F %T')}: {len(JOBS)} jobs\n")
    for name, cmd, limit in JOBS:
        if only and not any(o in name for o in only):
            continue
        CURRENT[0] = name
        if not wait_for_memory(name):
            log.write(f"{time.strftime('%T')} SKIPPED {name}: under {NEED_MB} MB free for 20 min\n")
            continue
        a0, s0 = meminfo()
        t0, low, top, why = time.time(), a0, 0, ""
        out = open(os.path.join(HERE, "jobs", name.replace(" ", "_") + ".log"), "w")
        p = subprocess.Popen(cmd, cwd=CODE, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
        while p.poll() is None:
            a, _ = meminfo()
            low, top = min(low, a), max(top, gpu()[0])
            if a < FLOOR_MB:
                why = f"KILLED: only {a} MB free"
                kill(p)
            elif time.time() - t0 > limit:
                why = f"KILLED: past {limit // 60} min"
                kill(p)
            time.sleep(2)
        log.write(f"{time.strftime('%T')} {name}: exit {p.returncode} {why} in {time.time() - t0:.0f} s; RAM free "
                  f"{a0} MB at the start, {low} MB at the least; GTT up to {top} MB; swap free {meminfo()[1]} MB\n")
    CURRENT[0] = "-"
    log.write(f"=== {time.strftime('%F %T')}: done\n")
    stop.set()


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "jobs"), exist_ok=True)
    main()
