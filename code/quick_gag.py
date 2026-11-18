#!/usr/bin/env python3
"""A gag from one line: Qwen 3.5 9B (on the NPU, through FastFlowLM) writes the song (title, words, style, tempo,
key, language), ACE-Step 1.5 sings and plays it (the 1.7B LM and the turbo DiT: fast), master.py and an MP3.
For a laugh in the group chat, not for the DJ.

quick_gag.py "Nederlands carnavalsliedje over dat alle updates gedraaid zijn"
quick_gag.py "Dubstep, English, time to take the bus" [--seed 2] [--best] [--keep]

--best: the 4B LM and the SFT DiT (about 2.5 minutes for 2 minutes of music, by ear the best; default: about 70 s).
--keep: leave the Qwen server running for the next gag (the first start takes about 8 s). It holds about 6 GB of
memory shared with the NPU: with another flm server and the browser, the laptop went to swap and mastering took 30 to
50 s instead of 5, so the default is to stop it after each gag.
The words and Qwen's whole answer go next to the MP3 in renders/ace/gags/<title>/ (renders/ is not in git).

The Qwen server is our own (`flm serve qwen3.5:9b` on port 52626), next to any other flm server, which keeps
running: FastFlowLM shares the NPU between them request by request.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

import gag

MODEL, PORT = "qwen3.5:9b", 52626
URL = f"http://127.0.0.1:{PORT}/v1"
LANGS = ("ar az bg bn ca cs da de el en es fa fi fr he hi hr ht hu id is it ja ko la lt ms ne nl no pa pl pt ro ru "
         "sa sk sr sv sw ta te th tl tr uk ur vi yue zh").split()        # ACE-Step's vocal languages

SYSTEM = """You write short, funny songs for the group chat of a crowd of hardware hackers and nerds (badges,
soldering, firmware, servers, updates). Given a request (a genre, a language, a topic, in any mix), write one song.
Answer in exactly this form, nothing before or after it:

TITLE: the song's title, in the song's language
LANG: the ISO 639-1 code of the language of the words (nl, en, de, zh, ...)
STYLE: in English, for a music generator: the genre and era, the instruments, the kind of voice, the mood (at most
40 words, no artist or band names)
BPM: an integer tempo typical of the genre
KEY: a key like G major or A minor
SECONDS: the length, 60 to 120
LYRICS:
the words in that language, with [Verse], [Chorus], [Bridge] and [Outro] tags each on their own line; one short line
per line (at most 8 words, never two sentences on one line), easy to sing; a catchy chorus that comes back at least twice; specific, funny details from the request; about 16
to 24 lines in all

Write the words yourself; do not quote existing songs."""


def up():
    try:
        urllib.request.urlopen(URL + "/models", timeout=2).read()
        return True
    except OSError:
        return False


def start_server():
    """Our own Qwen server, unless one already answers on the port. Returns the process we started, or None."""
    if up():
        return None
    p = subprocess.Popen(["flm", "serve", MODEL, "--port", str(PORT), "--quiet"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(90):
        if up():
            return p
        if p.poll() is not None:
            sys.exit(f"flm serve {MODEL} stopped (exit {p.returncode}); try: flm validate")
        time.sleep(1)
    p.terminate()
    sys.exit(f"flm serve {MODEL} did not answer on port {PORT} in 90 s")


def ask(request, seed):
    body = {"model": MODEL, "temperature": .8, "seed": seed, "max_tokens": 1500,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": request}]}
    req = urllib.request.Request(URL + "/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    text = json.load(urllib.request.urlopen(req, timeout=300))["choices"][0]["message"]["content"]
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)          # a reasoning model's thoughts, if any
    text = text.replace("**", "")
    song = {}
    for k in ("title", "lang", "style", "bpm", "key", "seconds"):
        m = re.search(rf"^\s*{k}\s*:\s*(.+?)\s*$", text, re.M | re.I)
        if m:
            song[k] = m.group(1).strip().strip('"')
    m = re.search(r"^\s*lyrics\s*:\s*(.*)", text, re.M | re.I | re.S)
    song["lyrics"] = m.group(1).strip() if m else ""
    for k in ("title", "lang", "style", "bpm", "key", "lyrics"):
        if not song.get(k):
            raise ValueError(f"the answer has no {k.upper()}: {text[:300]}")
    song["bpm"] = re.sub(r"[^0-9]", "", song["bpm"]) or "120"
    song["lang"] = song["lang"].lower() if song["lang"].lower() in LANGS else "en"
    song["bpm"] = int(min(max(int(song["bpm"]), 60), 300))
    song["seconds"] = int(min(max(int(song.get("seconds", 90)), 45), 150))
    if not re.match(r"^[A-G][#b]? (major|minor)$", song["key"]):
        song["key"] = "A minor"
    return song


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("request", help="one line: the genre, the language and the topic")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--best", action="store_true", help="the 4B LM and the SFT DiT: slower, by ear better")
    ap.add_argument("--keep", action="store_true", help="leave the Qwen server running")
    a = ap.parse_args()

    t0 = time.time()
    server = start_server()
    try:
        for attempt in range(3):
            try:
                song = ask(a.request, a.seed + attempt)
                break
            except ValueError as err:
                print(f"Qwen, try {attempt + 1}: {err}", file=sys.stderr)
        else:
            sys.exit("Qwen gave no usable song in three tries")
    finally:
        if server and not a.keep:
            server.terminate()
    t1 = time.time()
    print(f"{song['title']} ({song['lang']}, {song['bpm']} BPM, {song['key']}, {song['seconds']} s)\n{song['style']}\n")
    print(song["lyrics"])

    name = re.sub(r"[^a-z0-9]+", "-", song["title"].lower()).strip("-") or re.sub(r"[^a-z0-9]+", "-",
                                                                                 a.request.lower())[:40].strip("-")
    out = os.path.join(gag.GAGS, name)
    os.makedirs(out, exist_ok=True)
    json.dump(dict(song, request=a.request), open(os.path.join(out, "qwen.json"), "w"), indent=1, ensure_ascii=False)
    open(os.path.join(out, "lyrics.txt"), "w", encoding="utf-8").write(song["lyrics"] + "\n")
    mp3, t = gag.make(song["title"], song["lyrics"], song["style"], song["bpm"], song["key"], song["lang"],
                      song["seconds"], a.seed, fast=not a.best, out=out)
    print(f"\nQwen {t1 - t0:.0f} s, ACE-Step LM {t['lm']:.0f} s, audio {t['audio']:.0f} s, MP3 {t['master']:.0f} s: "
          f"{time.time() - t0:.0f} s in all")
    print(mp3)


if __name__ == "__main__":
    main()
