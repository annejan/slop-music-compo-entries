#!/usr/bin/env python3
"""Ears for the vocals: a speech recognizer (faster-whisper, MIT, on the CPU) writes down what it hears, and the
words are compared with the lyrics, so a mangled word ("badge-E-link", "bad link") shows up before a human hears it.

asr.py SONG.wav [LYRICS.txt | SONG]   (SONG: a script name such as segfault; its lyric sheet is used)

Works on a full mix (our Badge: 74 % of the words heard) and better on a vocal stem
(MUTE=drums,perc,bass,pads,keys,lead,fx: 99 %). Whisper's voice-activity filter is off (WHISPER_VAD=1 turns it on):
it takes singing over music for "not speech" and drops all of it.
The first run downloads the model (WHISPER_MODEL, default base.en, about 150 MB) to ~/.cache/huggingface.
"""
import difflib
import glob
import os
import re
import sys

MODEL = os.environ.get("WHISPER_MODEL", "base.en")
VAD = os.environ.get("WHISPER_VAD", "0") == "1"     # the voice-activity filter drops singing over music
_model = None


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen " \
       "seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def number_words(n):
    """64 -> "sixty four" (0..99; bigger numbers stay digits)."""
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    return str(n)


def words(text):
    text = text.lower().replace("-", " ").replace("%", " percent")
    text = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", text)        # "c6" -> "c 6"
    text = re.sub(r"\d+", lambda m: number_words(int(m.group())), text)
    return re.findall(r"[a-z']+|\d+", text)


def hear(path, t0=None, t1=None):
    """[(start, end, text)] of what the recognizer hears (from t0 to t1 seconds only, if given; times stay song
    times). No context carried from one stretch to the next: one misheard line must not drag the next along."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    import numpy as np
    from scipy import signal
    import master
    x, sr = master.read(path)                       # our own reader: mono, 16 kHz, as float32 (no PyAV)
    g = np.gcd(sr, 16000)
    x = signal.resample_poly(x.mean(1), 16000 // g, sr // g).astype(np.float32)
    off = 0.0
    if t0 is not None:
        off = max(t0, 0.0)
        x = x[int(off * 16000):int(t1 * 16000) if t1 else None]
    segments, _ = _model.transcribe(x, language="en", vad_filter=VAD, beam_size=5,
                                    condition_on_previous_text=False, temperature=0.0)
    return [(s.start + off, s.end + off, s.text.strip()) for s in segments]


def sheet_text(sheet):
    """The sung words of a lyric sheet (lyrics/NN-*.txt): the text after "ROLE:", no stage directions."""
    out, started = [], False
    for line in open(sheet, encoding="utf-8").read().splitlines():
        started = started or bool(re.match(r"\[\d+:\d\d\]", line.strip()))     # the header ends at the first time
        if not started:
            continue
        line = re.sub(r"^\[\d+:\d\d\]\s*", "", line.strip())
        line = re.sub(r"\(.*?\)", "", line)
        if ":" in line:
            out.append(line.split(":", 1)[1])
    return " ".join(out)


def report(path, lyrics):
    """Plain text: how many of the lyric's words were heard, the missed ones, and what was heard instead."""
    heard = hear(path)
    got = words(" ".join(t for _, _, t in heard))
    want = words(lyrics)
    sm = difflib.SequenceMatcher(a=want, b=got, autojunk=False)
    hit = sum(b.size for b in sm.get_matching_blocks())
    lines = [f"{os.path.basename(path)}: {hit}/{len(want)} lyric words heard ({hit / max(len(want), 1):.0%})"]
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op in ("replace", "delete") and a1 - a0 <= 6:
            lines.append(f"  sung \"{' '.join(want[a0:a1])}\" -> heard \"{' '.join(got[b0:b1])}\"")
    return "\n".join(lines[:40])


if __name__ == "__main__":
    wav = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    if arg and os.path.exists(arg):
        text = sheet_text(arg) if arg.endswith(".txt") else open(arg).read()
        if not text.strip():          # a plain words file named .txt (no [m:ss] lines): its words as they are
            text = open(arg).read()
    elif arg:
        import share
        n = next(i for i, row in enumerate(share.SONGS, 1) if row[0].startswith(arg.replace("_", "-") + "_"))
        text = sheet_text(glob.glob(os.path.join(share.LYRICS, f"{n:02d}-*.txt"))[0])
    else:
        for s, e_, t in hear(wav):
            print(f"[{s:6.1f}-{e_:6.1f}] {t}")
        sys.exit()
    print(report(wav, text))
