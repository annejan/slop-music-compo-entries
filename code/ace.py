#!/usr/bin/env python3
"""One command for the ACE-Step route: our song script -> our render (and stems) -> ACE-Step -> mastered for the
DJ -> a radio edit and a DJ version as MP3.

ace.py SONG [--mode cover|vocals|lego|text] [--strength 0.85] [--model base|turbo] [--ref] [--ace 1.0] [--era 90s]
            [--seed 1] [--caption "..."] [--tag NAME] [--check]

  SONG      a song script without .py, e.g. rhythm_of_the_badge (it must be in share.SONGS)
  cover     ACE-Step re-plays the whole song from our render (cover-nofsq): its sound and voices on our structure,
            tempo, key and melody; our 16-bar DJ intro and outro are spliced back in (master.py --dj-from)
  vocals    ACE-Step re-sings only our vocal stem; its take is lined up, gated by our vocals and woven over our own,
            unchanged instrumental (weave.py), --ace of it in the vocals
  lego      ACE-Step sings a new vocal track over our instrumental stem (base model, with the LM): our music, its
            voices and its own melody on our words; our DJ intro and outro are spliced back in
  text      ACE-Step makes its own song from a caption and our lyrics, at our tempo and key (it sets the
            arrangement itself); mastered onto the beat grid
  --strength how many of ACE-Step's steps see our audio (cover modes): 1 follows us closely, 0.3 loosely
  --ref     also pass our audio as the timbre reference: closer to our sound (and to Piper's robot voices)
  --check   run the speech recognizer over the result (asr.py) and report the words it hears

The lyrics come from lyrics/NN-*.txt, respelled for ACE-Step (ACE_SPELL: it reads text itself, not through
eSpeak). Everything lands in renders/ace/<song>/<tag>.wav and renders/ace/<song>/<Title> (<tag>, radio edit).mp3;
the request and the logs stay next to it. ACE-Step is acestep.cpp in ~/Projects/acestep.cpp (ACESTEP to move it).
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time

import master
import share
import weave

HERE = os.path.dirname(os.path.abspath(__file__))
ACESTEP = os.environ.get("ACESTEP", os.path.expanduser("~/Projects/acestep.cpp"))
MODELS = os.path.join(ACESTEP, "models")
SYNTH = {"turbo": dict(synth_model="acestep-v15-turbo-Q8_0.gguf", inference_steps=8, guidance_scale=1.0, shift=3.0),
         "base": dict(synth_model="acestep-v15-base-Q8_0.gguf", inference_steps=50, guidance_scale=1.0, shift=1.0)}
LM = "acestep-5Hz-lm-4B-Q8_0.gguf"
KEYS = {"Am": "A minor", "Fm": "F minor", "Dm": "D minor", "Em": "E minor", "D": "D major", "C": "C major",
        "G": "G major", "Bm": "B minor"}

# ACE-Step reads the lyrics itself: these spellings come out right (found by ear: "Badgelink" gave badge-E-link,
# "Badglink" bad link)
ACE_SPELL = [
    (r"\bBadgelink\b|\bBadge link\b", "badge-link"),
    (r"\bUSB\b", "U S B"), (r"\bC6\b", "C six"), (r"\bP4\b", "P four"), (r"\bLED\b", "L E D"),
    (r"\bGPIO\b", "G P I O"), (r"\bPCB\b", "P C B"), (r"\bThreadSanitizer\b", "Thread Sanitizer"),
    (r"S-E-G-F-A-U-L-T!?", "S! E! G! F! A! U! L! T!"),
]

# the sound of each song, for the caption (from the style prompts in suno/, without the DJ intro and outro)
CAPTIONS = {
    "warm_boot": "90s deep house, mellow, warm Rhodes electric piano chords, Korg M1 organ stabs, round analog "
                 "bassline, shuffled 909 hi-hats, soft four on the floor kick, vinyl crackle, lush string pad, "
                 "soulful female vocal, breathy, sunrise, laid back",
    "packet_loss": "early 90s garage house, mellow, swung shuffle beat, deep organ bass, warm piano chords, soulful "
                   "male and female duet, call and response, smooth saxophone, rain on the window, late night",
    "low_battery": "instrumental 90s deep house, mellow, dreamy Rhodes chords, warm sub bass, shuffled 909 hats, "
                   "soft rimshots, airy pad, vinyl warmth, chopped female vocal sample, sunrise chill",
    "low_pass_love": "late 90s French house, filtered disco loop, slow low-pass filter sweeps, phaser, sidechain "
                     "pumping, funky bass guitar, Rhodes, talk box vocal hook, male disco vocal, warm and sunny",
    "segfault": "90s eurodance, powerful female diva vocal chorus, male rap verses, stabbing supersaw synth riff, "
                "Korg M1 piano, four on the floor kick, offbeat bass, open hi-hats, orchestra hits, euphoric, 1994, "
                "key change up for the last chorus",
    "blinky": "90s bubblegum eurodance, cute high female vocal, playful male shout-outs, bouncy synth riff, "
              "pizzicato strings, happy piano, four on the floor, offbeat bass, euphoric",
    "rhythm_of_the_badge": "mid 90s eurodance, dramatic female vocal, deep male rap, dark hoover synth, minor key "
                           "piano, big reverb snare, 909 kick, rolling offbeat bass, laser effects, dramatic, night "
                           "club, key change in the last chorus",
    "race_condition": "90s liquid drum and bass, chopped breakbeat, deep rolling sub bass, jazzy Rhodes chords, "
                      "soulful female vocal, male MC",
}
VOCALS_CAPTION = ("a cappella vocals only, no instruments: natural, warm, human voices, the same melody, words and "
                  "timing, 1994 studio recording, expressive, breathing, not robotic")


def song_info(script):
    """(n, wav, title, day, bpm, key, bars) from share.SONGS, matched by the render's name."""
    prefix = script.replace("_", "-") + "_"
    for n, row in enumerate(share.SONGS, 1):
        if row[0].startswith(prefix):
            return (n,) + row
    sys.exit(f"{script}: not in share.SONGS (add the song there first)")


def ace_lyrics(n, t0=None, t1=None):
    """The lyric sheet as ACE-Step lyrics: [Section] tags, the sung words without the roles, respelled. With t0 and
    t1 (seconds): only the sections that start inside that stretch, or sing into it."""
    sheets = glob.glob(os.path.join(share.LYRICS, f"{n:02d}-*.txt"))
    if not sheets:
        return "[Instrumental]"
    lines = open(sheets[0], encoding="utf-8").read().splitlines()
    if t0 is not None:
        keep, times = [], []
        for line in lines:
            m = re.match(r"\[(\d+):(\d\d)\]", line.strip())
            times.append(int(m.group(1)) * 60 + int(m.group(2)) if m else None)
        starts = [t for t in times if t is not None]
        cur = None
        for line, t in zip(lines, times):
            if t is not None:
                nxt = next((s for s in starts if s > t), 10 ** 6)
                cur = t < t1 and nxt > t0
            if cur:
                keep.append(line)
        lines = keep
    out, started = [], False
    for line in lines:
        line = line.strip()
        m = re.match(r"\[\d+:\d\d\]\s*(.*)", line)
        started = started or bool(m)              # the header (title, voices) ends at the first time stamp
        if not started:
            continue
        if m:
            section = re.sub(r"\s*\(.*?\)", "", m.group(1)).strip()
            out += ["", f"[{section}]"]
            if ":" in section:     # "[1:58] MC: Warning..." : a timed line, the words after the role
                role, words = section.split(":", 1)
                out[-1] = f"[{role.strip()}]"
                out.append(words.strip())
        elif ":" in line and not line.startswith("("):
            out.append(line.split(":", 1)[1].strip())
    text = "\n".join(out).strip()
    text = re.sub(r"[ \t]*\([^)]*\)", "", text)          # stage directions in the sheet: "(in the echo)"
    for pat, rep in ACE_SPELL:
        text = re.sub(pat, rep, text)
    return re.sub(r"\n{3,}", "\n\n", text)


def run(cmd, log):
    with open(log, "w") as fh:
        r = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT)
    if r.returncode:
        sys.exit(f"failed: {' '.join(cmd)} (see {log})")


def render(script, wav, env=None):
    """Our render: the song script, again only when the script is newer than the render."""
    out = os.path.join(share.RENDERS, wav) if not os.path.isabs(wav) else wav
    src = os.path.join(HERE, script + ".py")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        print(f"render {os.path.basename(out)}", flush=True)
        subprocess.run([sys.executable, "-W", "ignore", src, out], env=dict(os.environ, **(env or {})), check=True,
                       stdout=subprocess.DEVNULL)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song")
    ap.add_argument("--mode", choices=["cover", "vocals", "lego", "text"], default="cover")
    ap.add_argument("--strength", type=float, default=.85)
    ap.add_argument("--model", choices=["base", "turbo"], default="base")
    ap.add_argument("--ref", action="store_true", help="our audio as the timbre reference too")
    ap.add_argument("--ace", type=float, default=1.0, help="vocals mode: ACE-Step's share of the vocals")
    ap.add_argument("--era", choices=["90s"])
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--caption", help="replace the song's caption")
    ap.add_argument("--lyrics", help="a text file with the lyrics (ACE-Step format, [Section] tags) instead of the sheet")
    ap.add_argument("--tag", help="the output's name (default: mode, model, strength, seed)")
    ap.add_argument("--check", action="store_true", help="the speech recognizer over the result")
    a = ap.parse_args()

    n, wav, title, day, bpm, key, bars = song_info(a.song)
    tag = a.tag or (f"{a.mode}-{a.model}-{a.strength:g}-s{a.seed}" if a.mode in ("cover", "vocals")
                    else f"{a.mode}-s{a.seed}")
    if a.era:
        tag += f"-{a.era}"
    out = os.path.join(share.RENDERS, "ace", a.song)
    os.makedirs(out, exist_ok=True)
    t0 = time.time()

    full = render(a.song, wav)
    src = full
    if a.mode in ("vocals", "lego"):
        inst = render(a.song, os.path.join(out, "stem_inst.wav"), {"MUTE": "vox"})
        vox = render(a.song, os.path.join(out, "stem_vox.wav"), {"MUTE": "drums,perc,bass,pads,keys,lead,fx"})
        src = vox if a.mode == "vocals" else inst
    if a.mode == "lego" and a.model != "base":
        sys.exit("lego needs the base model (--model base)")

    caption = a.caption or (VOCALS_CAPTION if a.mode == "vocals" else CAPTIONS.get(a.song, day.split(": ")[1]))
    lyrics = open(a.lyrics, encoding="utf-8").read() if a.lyrics else ace_lyrics(n)
    req = {"caption": caption, "lyrics": lyrics, "bpm": bpm, "keyscale": KEYS.get(key, key),
           "timesignature": "4", "vocal_language": "en", "seed": a.seed, "output_format": "wav16", **SYNTH[a.model]}
    base = os.path.join(out, tag)
    if a.mode in ("text", "lego"):
        req.update(duration=round(bars * 240 / bpm + 2), lm_model=LM)
        if a.mode == "lego":
            req.update(task_type="lego", track="vocals")
        json.dump(req, open(base + ".json", "w"), indent=1)
        run([os.path.join(ACESTEP, "build", "ace-lm"), "--models", MODELS, "--request", base + ".json",
             "--device", "Vulkan0"], base + ".lm.log")
        synth_req = base + "0.json"
        cmd = ["--src-audio", src] if a.mode == "lego" else []
    else:
        req.update(task_type="cover-nofsq", audio_cover_strength=a.strength)
        json.dump(req, open(base + ".json", "w"), indent=1)
        synth_req = base + ".json"
        cmd = ["--src-audio", src] + (["--ref-audio", src] if a.ref else [])
    run([os.path.join(ACESTEP, "build", "ace-synth"), "--models", MODELS, "--request", synth_req, *cmd,
         "--device", "Vulkan0"], base + ".synth.log")
    raw = synth_req[:-5] + "0.wav"
    print(f"ACE-Step: {time.time() - t0:.0f} s", flush=True)

    final = base + ".wav"
    if a.mode in ("cover", "lego"):
        print(master.process(raw, final, bpm, era=a.era, dj_from=full, bars=bars))
    elif a.mode == "vocals":
        print(weave.process(inst, vox, raw, full, final, bpm, ace=a.ace))
    else:
        print(master.process(raw, final, bpm, era=a.era))

    tags = ["-metadata", f"title={title} ({tag})", "-metadata", "artist=sunA"]
    share.encode(final, os.path.join(out, f"{title} ({tag}, radio edit).mp3"), tags, [], share.radio_window(bpm, bars))
    if a.check:
        import asr
        sheet = glob.glob(os.path.join(share.LYRICS, f"{n:02d}-*.txt"))
        print(asr.report(final, asr.sheet_text(sheet[0])) if sheet else "no lyric sheet to check against")
    print(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
