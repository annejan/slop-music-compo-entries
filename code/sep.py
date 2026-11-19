#!/usr/bin/env python3
"""The singer alone: an ACE-Step take split into its voice and the band that ACE-Step put under it.

ACE-Step often ignores "a cappella vocals only, no instruments": of 122 takes on disk on 19 November, about half
carry drums, bass or pads under the voice. In a song that band plays in its own key and chords under ours. The
rehearsal song Pull-Up Resistor ("sucks ... mostly the high pitched singing, but also some of the rest") played such
a take: 29 % of its energy below 150 Hz (a clean take: 0 %), and fit.py measured the bass instead of the voice.
Mel-Band RoFormer (audio.cpp v0.9.5 prebuilt, Vulkan, behind the GPU lock) splits a take in about 0.8 times its
length; the voice it gives back has no energy below 150 Hz.

sep.py TAKE.wav [TAKE.wav ...]      <take>_vox.wav next to each take, and the band's level

band_db: the band's level against the whole take (20 log10 of the RMS ratio). A clean take measures below CLEAN_DB;
voice() then keeps the take itself, so a clean take is never touched.
Needs ~/Projects/audiocpp/v095/audiocpp_cli and ~/Projects/audiocpp-models/Mel-Band-RoFormer-GGUF (the source
build in ~/Projects/audiocpp-src has no RoFormer). The model: audio.cpp's model_manager_v2.py install
mel_band_roformer_q8_0 --models-root ~/Projects/audiocpp-models (250 MB).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

import ace
import master

CLI = os.path.expanduser("~/Projects/audiocpp/v095/audiocpp_cli")
MODEL = os.path.expanduser("~/Projects/audiocpp-models/Mel-Band-RoFormer-GGUF/mel-band-roformer-q8_0.gguf")
CLEAN_DB = -25.0      # Overclocked Heart's approved take -45 dB, the menu's house diva (a faint bed) -28, the rehearsal
#                       keeper -3


def _rms(x):
    return float(np.sqrt(np.mean(np.square(x)) + 1e-12))


def split(wav):
    """(voice WAV, band_db) of a take, cached next to it as <take>_vox.wav and <take>_vox.json; (None, None) when the
    separation failed (its log stays as <take>_vox.log)."""
    vox, meta, log = wav[:-4] + "_vox.wav", wav[:-4] + "_vox.json", wav[:-4] + "_vox.log"
    if os.path.exists(vox) and os.path.exists(meta):
        return vox, json.load(open(meta))["band_db"]
    with tempfile.TemporaryDirectory(dir=os.path.dirname(os.path.abspath(wav))) as d:
        src = os.path.join(d, "in.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-ar", "44100", "-ac", "2", src], check=True)
        if not ace.gpu([CLI, "--task", "sep", "--family", "mel_band_roformer", "--model", MODEL, "--backend",
                        "vulkan", "--audio", src, "--out-dir", d], log, 600):
            return None, None
        band_db = 20 * np.log10(_rms(master.read(os.path.join(d, "instrumental.wav"))[0])
                                / _rms(master.read(src)[0]))
        shutil.move(os.path.join(d, "vocals.wav"), vox)
    json.dump({"band_db": round(float(band_db), 1), "model": os.path.basename(MODEL)}, open(meta, "w"))
    os.remove(log)
    return vox, round(float(band_db), 1)


def voice(wav, clean_db=CLEAN_DB):
    """The take to use and its band level: the take itself when it was clean (band below `clean_db`), else its
    voice alone. The take itself too when the separation failed (band_db None)."""
    vox, band_db = split(wav)
    if vox is None or band_db < clean_db:
        return wav, band_db
    return vox, band_db


def describe(band_db):
    if band_db is None:
        return "band not measured"
    return "clean" if band_db < CLEAN_DB else f"a band under the voice at {band_db:.0f} dB: separated"


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sys.exit(__doc__)
    for wav in sys.argv[1:]:
        vox, band_db = split(wav)
        print(f"{os.path.basename(wav)}: {describe(band_db)}" + (f" -> {vox}" if vox else ""))


if __name__ == "__main__":
    main()
