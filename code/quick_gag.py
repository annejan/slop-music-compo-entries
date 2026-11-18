#!/usr/bin/env python3
"""A gag from one line: Qwen 3.5 9B (on the NPU, through FastFlowLM) writes the song (title, words, style, tempo,
key, language), ACE-Step 1.5 sings and plays it (the 1.7B LM and the turbo DiT: fast), master.py and an MP3.
For a laugh in the group chat, not for the DJ.

quick_gag.py "Nederlands carnavalsliedje over dat alle updates gedraaid zijn"
quick_gag.py "Dubstep, English, time to take the bus" [--nerd] [--seed 2] [--best] [--keep]
quick_gag.py 'Rockabilly about a bug, the hook "BuggyWuggy, boogie woogie"' --nerd   (quoted words go in as written)

The song is about the request and nothing else; --nerd bends it towards the hardware-hacker crowd (badges,
soldering, firmware, servers, updates), as the first version always did ("Bus Stop Drop" got a badge, a server rack
and a CPU core).

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

SYSTEM = """You write short, funny songs for a group chat. Given a request (a genre, a language, a topic, in any mix),
write one song about exactly that topic: its jokes and details come from the topic itself.
{nerd}
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
per line (at most 8 words, never two sentences on one line), easy to sing; a catchy chorus that comes back at least twice; specific, funny details about the topic; about 16
to 24 lines in all

Words in quotes in the request go into the lyrics exactly as written, as the hook of the chorus.
Write the other words yourself; do not quote existing songs.

An example of the form (a different song; yours is longer):

TITLE: Monday Morning Coffee
LANG: en
STYLE: 1970s funk, slap bass, horn section, wah guitar, a cheerful male singer, sunny mood
BPM: 104
KEY: E minor
SECONDS: 90
LYRICS:
[Verse]
The alarm goes off at seven
I hit snooze and dream of heaven
[Chorus]
Coffee, coffee, save my day
Pour it in and I'm okay
[Outro]
Pour it in and I'm okay"""

REFORMAT = """Put these song lyrics in lines, as a lyric sheet: each [Tag] on its own line; one short sung line per line,
at most 8 words; split long lines where a sentence or phrase ends. Do not change, add or drop any words. Answer with
only the lyrics."""


def messy(lyrics):
    """True when the words are not in sung lines: a tag inside a line, or a line of more than 12 words."""
    for line in lyrics.splitlines():
        line = line.strip()
        if re.search(r".\[[A-Za-z]", line) or len(line.split()) > 12:
            return True
    return False


def chat(system, user, seed, max_tokens=1500):
    body = {"model": MODEL, "temperature": .8, "seed": seed, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    req = urllib.request.Request(URL + "/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    text = json.load(urllib.request.urlopen(req, timeout=300))["choices"][0]["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S)          # a reasoning model's thoughts, if any


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


NERD = ("The chat is a crowd of hardware hackers and nerds: bend the topic towards their world (badges, soldering, "
        "firmware, servers, updates) where it is funny.")


def quoted(request):
    """The phrases in quotes ("...", '...', or curly quotes) that must appear in the words as written."""
    return [m.strip() for m in re.findall(r'["\u201c\u201e]([^"\u201c\u201d\u201e]+)["\u201d]|\'([^\']+)\'', request)
            for m in m if m.strip()]


def plain(x):
    return re.sub(r"[^a-z0-9]+", " ", x.lower()).strip()


def ask(request, seed, nerd=False):
    system = SYSTEM.replace("{nerd}", NERD if nerd else "Do not add other subjects (no computers or technology unless "
                                                          "the request is about them).")
    text = chat(system, request, seed)
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
    if messy(song["lyrics"]):                  # Qwen puts its own words in lines (once), the regex only as a last resort
        print("Qwen: the words are not in lines; asking it to set them as a lyric sheet", file=sys.stderr)
        again = chat(REFORMAT, song["lyrics"], seed).strip()
        if len(again.split()) >= .8 * len(song["lyrics"].split()):
            song["lyrics"] = again
    song["lyrics"] = tidy(song["lyrics"])
    missing = [q for q in quoted(request) if plain(q) not in plain(song["lyrics"])]
    if missing:
        raise ValueError(f"the words leave out {missing}")
    song["lang"] = song["lang"].lower() if song["lang"].lower() in LANGS else "en"
    song["bpm"] = int(min(max(int(song["bpm"]), 60), 300))
    song["seconds"] = int(min(max(int(song.get("seconds", 90)), 45), 150))
    if not re.match(r"^[A-G][#b]? (major|minor)$", song["key"]):
        song["key"] = "A minor"
    return song


def tidy(lyrics, width=8):
    """The words as ACE-Step wants them: each [Tag] on its own line with a blank line before it, and no line longer
    than about `width` words (Qwen sometimes writes a whole song on one line). Splits at punctuation when it can."""
    text = re.sub(r"\s*(\[[A-Za-z][A-Za-z0-9 \-]*\])\s*", r"\n\n\1\n", lyrics).strip()
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("[") or len(line.split()) <= width + 2:
            out.append(line)
            continue
        # sentences: after punctuation, or where a capital follows a lower-case word ("old cheese My lunchbox")
        parts = [x.strip() for x in re.split(r"(?<=[.!?,;])\s+|(?<=[a-z])\s+(?=[A-Z])", line) if x.strip()]
        cur = []
        for part in parts:                         # short parts back together, up to width + 1 words a line;
            words = part.split()                   # a capital starts a new line once the line has 4 words
            if cur and (len(cur) + len(words) > width + 1 or (words[0][:1].isupper() and len(cur) >= 4)):
                out.append(" ".join(cur))
                cur = []
            cur += words
            while len(cur) > width + 2:            # still too long: cut at about `width` words
                out.append(" ".join(cur[:width]))
                cur = cur[width:]
        if cur:
            out.append(" ".join(cur))
    lines = "\n".join(out).strip().splitlines()    # blank lines only before a [Tag] (Qwen sometimes leaves one after
    keep = [x for i, x in enumerate(lines)            # every line, which ACE-Step reads as a pause)
            if x.strip() or (i + 1 < len(lines) and lines[i + 1].startswith("["))]
    return "\n".join(keep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("request", help="one line: the genre, the language and the topic")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--best", action="store_true", help="the 4B LM and the SFT DiT: slower, by ear better")
    ap.add_argument("--keep", action="store_true", help="leave the Qwen server running")
    ap.add_argument("--nerd", action="store_true", help="bend the song towards the hardware-hacker crowd (badges, "
                                                        "soldering, firmware, servers)")
    a = ap.parse_args()

    t0 = time.time()
    server = start_server()
    try:
        for attempt in range(3):
            try:
                song = ask(a.request, a.seed + attempt, a.nerd)
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
