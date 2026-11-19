"""Voices: a diva that sings our melody and a rapper that raps in time, both made by AI.

Piper (a neural text-to-speech model, run on the CPU) speaks every syllable. WORLD (pyworld) takes the speech
apart into pitch, spectral envelope and noise, and puts it back together on our notes: the vowel is stretched to
the note's length, the consonants keep their own length, and the pitch is tuned hard to the note (the eurodance
"robot diva" sound), with a vibrato on the long notes.

Needs the venv (see README): piper-tts, pyworld, and the voices in code/voices/.

A voice is a Piper voice name ("en_US-ryan-high"), or one of the classic engines, if installed:
"espeak:en-us+f3" (eSpeak NG), "flite:slt" (Flite, also a .flitevox path or URL), "festival:kal_diphone"
(Festival), "mimic3:en_US/vctk_low#p239" (Mimic 3).
"""
import hashlib
import os
import shutil
import subprocess
import tempfile
import warnings
import wave

import numpy as np
from scipy import signal

warnings.filterwarnings("ignore", category=UserWarning, module="pyworld")
import pyworld  # noqa: E402
from piper import PiperVoice, SynthesisConfig  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
VOICES = os.path.join(HERE, "voices")
CACHE = os.path.join(HERE, ".cache")
# the GPU lock of ace.gpu, for the voice engines that run on the iGPU (qwen:, maya:)
GPU_LOCK = os.environ.get("ACE_LOCK") or os.path.join(HERE, "renders", ".gpu.lock")
TTS_SR = 22050
OUT_SR = 44100
FRAME = 5.0          # WORLD frame period, ms
FS = FRAME / 1000

DIVA = os.environ.get("DIVA", "en_US-hfc_female-medium")
# 0: hard tuned, every syllable exactly on its note (the eurodance robot diva); 1: a singer's pitch and breath:
# scoops into the notes, a slow drift, a vibrato of its own, a swell on long notes, breath at their end (see sing)
HUMAN = float(os.environ.get("VOX_HUMAN", "0"))
RAPPER = os.environ.get("RAPPER", "en_US-ryan-high")

_loaded = {}


def _voice(name):
    if name not in _loaded:
        _loaded[name] = PiperVoice.load(os.path.join(VOICES, name + ".onnx"))
    return _loaded[name]


def _read_wav(path):
    with wave.open(path) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), "<i2").astype(np.float64) / 32768
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    if sr != TTS_SR:
        g = np.gcd(sr, TTS_SR)
        x = signal.resample_poly(x, TTS_SR // g, sr // g)
    return x


def _classic(engine, name, text, length_scale):
    """Speech from a command-line engine, as 22.05 kHz floats."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "out.wav")
        if engine == "espeak":
            cmd = ["espeak-ng", "-v", name, "-s", str(int(165 / length_scale)), "-w", out, text]
        elif engine == "flite":
            if name.endswith(".flitevox") and "://" not in name and not os.path.exists(name):
                raise FileNotFoundError(name)   # flite would quietly fall back to its default voice
            cmd = ["flite", "-voice", name, "--setf", f"duration_stretch={length_scale}", "-t", text, "-o", out]
        elif engine == "festival":
            txt = os.path.join(tmp, "in.txt")
            with open(txt, "w") as fh:
                fh.write(text)
            local = os.path.join(VOICES, "festival", "festival", "lib", "voices", "us", name)
            reg = [f'(voice-location "{name}" "{local}/" "local")'] if os.path.isdir(local) else []
            cmd = ["text2wave", *[a for r in reg for a in ("-eval", r)], "-eval", f"(voice_{name})", "-eval",
                   f"(Parameter.set 'Duration_Stretch {length_scale})", txt, "-o", out]
        elif engine == "kokoro":
            # "kokoro:af_bella" or "kokoro:am_fenrir@1.2" (a speed): Kokoro-82M presets on the CPU, in its own venv
            # (~/Projects/kokoro; the TTS A/B of 19 November: "way better than other options so far")
            v, _, speed = name.partition("@")
            k = os.path.expanduser("~/Projects/kokoro")
            cmd = [f"{k}/.venv/bin/python", f"{k}/scripts/kokoro_say.py", "--voice", v,
                   "--speed", speed or f"{1 / length_scale:g}", "--out", out, text]
        elif engine == "qwen":
            # "qwen:<a voice described in words>" or "...#seed" (default 42; a seed keeps one voice): Qwen3-TTS
            # 1.7B VoiceDesign through qwentts.cpp on the GPU, behind the ACE-Step GPU lock (~/Projects/qwentts.cpp)
            desc, seed = (name.rsplit("#", 1) + ["42"])[:2] if "#" in name else (name, "42")
            q = os.path.expanduser("~/Projects/qwentts.cpp")
            subprocess.run(["flock", GPU_LOCK, f"{q}/build/qwen-tts", "--model",
                            f"{q}/models/qwen-talker-1.7b-voicedesign-Q8_0.gguf", "--codec",
                            f"{q}/models/qwen-tokenizer-12hz-Q8_0.gguf", "--device", "Vulkan0", "--lang", "English",
                            "--seed", seed, "--max-new", "500", "--instruct", desc.strip(), "-o", out],
                           input=text.encode(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return _read_wav(out)
        elif engine == "maya":
            # "maya:<a voice described in words>" or "...#seed"; emotion tags go in the text ("<excited> Hands up!",
            # <whisper>, <angry>, <laugh>, ...): Maya1 through llama.cpp on the GPU (behind the lock) and the SNAC
            # decoder; slow (a 4 s line takes about 17 s), so every line is cached (~/Projects/maya1)
            desc, seed = (name.rsplit("#", 1) + ["-1"])[:2] if "#" in name else (name, "-1")
            m = os.path.expanduser("~/Projects/maya1")
            cmd = ["flock", GPU_LOCK, f"{m}/.venv/bin/python", f"{m}/maya1_tts.py", "--seed", seed, "--wav", out,
                   "--description", desc.strip(), "--text", text]
        elif engine == "mimic3":
            exe = shutil.which("mimic3") or os.path.join(HERE, ".venv-mimic3", "bin", "mimic3")
            with open(out, "wb") as fh:
                subprocess.run([exe, "--voices-dir", os.path.join(VOICES, "mimic3"), "--voice", name,
                                "--length-scale", str(length_scale), text], stdout=fh,
                               stderr=subprocess.DEVNULL, check=True)
            return _read_wav(out)
        else:
            raise ValueError(f"unknown voice engine {engine!r}")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return _read_wav(out)


def tts(text, voice, length_scale=1.0, take=0):
    """Speech for a text, 22.05 kHz, the silence at both ends trimmed; cached on disk. Piper's noise is random, so
    every take is a little different (with the same timing): a double-tracked voice."""
    key = hashlib.sha1(f"{voice}|{length_scale}|{text}|{take}".encode()).hexdigest()[:16]
    path = os.path.join(CACHE, key + ".npy")
    if os.path.exists(path):
        return np.load(path)
    if ":" in voice:
        engine, name = voice.split(":", 1)
        x = _classic(engine, name, text, length_scale)
    else:
        # "voice#speaker": a speaker of a many-speaker model, by name or number (en_GB-semaine-medium#spike, the
        # angry one; en_US-libritts_r-medium#12 of its 904; en_GB-vctk-medium#40 of its 109)
        name, _, spk = voice.partition("#")
        sid = None
        if spk:
            sid = int(spk) if spk.isdigit() else _voice(name).config.speaker_id_map[spk]
        cfg = SynthesisConfig(speaker_id=sid, length_scale=length_scale, noise_scale=.5, noise_w_scale=.6)
        x = np.concatenate([c.audio_float_array for c in _voice(name).synthesize(text, cfg)]).astype(np.float64)
    env = np.convolve(np.abs(x), np.ones(110) / 110, "same")
    on = np.nonzero(env > .02 * env.max())[0]
    x = x[max(on[0] - 60, 0):on[-1] + 200] if len(on) else x
    os.makedirs(CACHE, exist_ok=True)
    np.save(path, x)
    return x


def analyse(x):
    """WORLD's pitch, spectral envelope and aperiodicity of a piece of speech, and its energy per frame; cached."""
    path = os.path.join(CACHE, "w" + hashlib.sha1(x.tobytes()).hexdigest()[:16] + ".npz")
    if os.path.exists(path):
        z = np.load(path)
        return z["f0"], z["sp"], z["ap"], z["energy"]
    f0, sp, ap, energy = _analyse(x)
    os.makedirs(CACHE, exist_ok=True)
    np.savez(path, f0=f0, sp=sp, ap=ap, energy=energy)
    return f0, sp, ap, energy


def _analyse(x):
    f0, t = pyworld.harvest(x, TTS_SR, frame_period=FRAME, f0_floor=70, f0_ceil=600)
    sp = pyworld.cheaptrick(x, f0, t, TTS_SR)
    ap = pyworld.d4c(x, f0, t, TTS_SR)
    n = len(f0)
    hop = int(TTS_SR * FS)
    energy = np.array([np.sqrt(np.mean(x[i * hop:i * hop + hop] ** 2) + 1e-12) for i in range(n)])
    return f0, sp, ap, energy


def _interp_frames(arr, idx):
    """Rows of arr at fractional frame indices, linearly between frames."""
    i0 = np.clip(np.floor(idx).astype(int), 0, len(arr) - 1)
    i1 = np.clip(i0 + 1, 0, len(arr) - 1)
    w = (idx - i0)[:, None]
    return arr[i0] * (1 - w) + arr[i1] * w


def _hz(m):
    return 440.0 * 2 ** ((np.asarray(m, dtype=float) - 69) / 12)


def _finish(y, gain_db=0.0):
    y = signal.resample_poly(y, OUT_SR // TTS_SR, 1)
    k = int(.004 * OUT_SR)
    if len(y) > 2 * k:
        y[:k] *= np.linspace(0, 1, k)
        y[-k:] *= np.linspace(1, 0, k)
    return y * 10 ** (gain_db / 20)


_VOWEL_LP = signal.butter(4, 6000, fs=OUT_SR, output="sos")   # the backing vowels: no air on top


def _humanise(text, voice, take, notes, tgt, sm, vib, sp, ap, tau, starts, since, pre, room, glide, vibrato, cents,
              h):
    """A singer instead of a tuner, by h (0..1). The pitch scoops up into each note from below (less after a step
    down) and glides more slowly between notes; it drifts a little (about 12 cents); the vibrato has its own rate
    (5.0 to 6.2 Hz) and breathes in depth. The long notes swell a little in the middle, and their ends turn breathy
    (more aperiodicity, a little quieter). Every syllable gets its own, repeatable variation (seeded by the word,
    the voice and the take), so a choir of voices does not move as one."""
    m = len(tgt)
    rng = np.random.default_rng(int(hashlib.sha1(f"{text}|{voice}|{take}|{notes}".encode()).hexdigest()[:8], 16))
    g = glide * (1 + 1.5 * h)
    alpha = 1 - np.exp(-FS / g)
    sm = signal.lfilter([alpha], [1, alpha - 1], tgt - tgt[0], zi=[0.0])[0] + tgt[0] + cents / 100
    idx = np.arange(m)
    for j, s0 in enumerate(starts):
        down = j > 0 and notes[j][0] < notes[j - 1][0]
        depth = h * (.5 + .3 * rng.random()) * (.4 if down else 1.0)
        dt = tau - s0
        on = (dt >= 0) & (idx >= pre if j else True)
        sm = sm - np.where(on, depth * np.exp(-np.maximum(dt, 0) / .07), 0.0)
    if m > 40:
        b, a = signal.butter(2, 3.0, fs=1 / FS)
        d = signal.filtfilt(b, a, rng.standard_normal(m))
        sm = sm + d / (np.std(d) + 1e-9) * .12 * h
    rate = 5.6 + h * (rng.random() * 1.2 - .6)
    breathe = 1 + .3 * h * np.sin(2 * np.pi * .7 * tau + rng.random() * 6.28)
    vib = vibrato * breathe * np.sin(2 * np.pi * rate * tau) * np.clip((since - .22 + .05 * h) / .25, 0, 1)
    u = np.clip((idx - pre) / max(room, 1), 0, 1)
    tail = np.clip((u - .7) / .3, 0, 1) * (idx >= pre)
    gain = 1 + h * (.18 * np.sin(np.pi * u) - .12 * tail)
    sp = sp * (gain ** 2)[:, None]
    ap = ap + (1 - ap) * (h * .35 * tail)[:, None]
    return sm, vib, sp, ap


def sing(text, notes, voice=DIVA, glide=.03, vibrato=.35, formant=1.0, level=.12, take=0, cents=0.0,
         vowel_only=False):
    """One syllable sung over one or more notes [(midi, seconds), ...], one after the other.

    Returns (lead_in seconds, mono 44.1 kHz audio): put the audio lead_in seconds before the first note's time,
    so the consonants come just before the beat and the vowel lands on it.

    vowel_only: keep only the vowel, faded in and out (lead_in 0), for a choir behind a lead: every voice has
    its own consonant lengths, so their consonants land up to 80 ms apart and smear the words; the lead
    sings those. The vowel is low-passed at 6 kHz: some voices (ljspeech) are breathy, and the air of five
    voices on top of each other hisses.
    """
    x = tts(text, voice, take=take)
    f0, sp, ap, energy = analyse(x)
    n = len(f0)
    voiced = f0 > 0
    if voiced.any():
        loud = voiced & (energy > .4 * energy[voiced].max())
        idx = np.nonzero(loud)[0]
        a, b = idx[0], idx[-1] + 1
    else:
        a, b = n // 3, 2 * n // 3
    total = sum(d for _, d in notes)
    pre, post, nuc = a, n - b, b - a
    want = int(round(total / FS))
    room = want - post
    if room < max(nuc, 1) * .5:   # a short note: squeeze the consonants too
        k = want / max(n, 1)
        pre, post = int(pre * k), int(post * k)
        room = max(want - post, 1)
    src = np.concatenate([np.linspace(0, a, pre, endpoint=False),
                          np.linspace(a, b, max(room, 1), endpoint=False),
                          np.linspace(b, n - 1, max(post, 1))])
    sp2, ap2 = _interp_frames(sp, src), _interp_frames(ap, src)
    vo = _interp_frames(voiced[:, None].astype(float), src)[:, 0] > .5
    # the pitch: our notes, from the vowel on; the consonants before it take the first note
    m = len(src)
    tgt = np.empty(m)
    ends = np.cumsum([d for _, d in notes])
    for i in range(m):
        tau = (i - pre) * FS
        j = int(np.searchsorted(ends, max(tau, 0), side="right"))
        tgt[i] = notes[min(j, len(notes) - 1)][0]
    # a quick glide between notes (hard tuned), then a vibrato that grows on the long notes
    alpha = 1 - np.exp(-FS / glide)
    sm = signal.lfilter([alpha], [1, alpha - 1], tgt - tgt[0], zi=[0.0])[0] + tgt[0] + cents / 100
    tau = np.maximum((np.arange(m) - pre) * FS, 0)
    starts = np.concatenate([[0], ends[:-1]])
    since = tau - starts[np.clip(np.searchsorted(ends, tau, side="right"), 0, len(notes) - 1)]
    vib = vibrato * np.sin(2 * np.pi * 5.6 * tau) * np.clip((since - .22) / .25, 0, 1)
    if HUMAN > 0:
        sm, vib, sp2, ap2 = _humanise(text, voice, take, notes, tgt, sm, vib, sp2, ap2, tau, starts, since, pre, room,
                                      glide, vibrato, cents, HUMAN)
    f0_new = np.where(vo, _hz(sm + vib), 0.0)
    if formant != 1.0:   # move the formants up (brighter) or down (darker)
        bins = sp2.shape[1]
        src_bins = np.clip(np.arange(bins) / formant, 0, bins - 1)
        sp2 = np.stack([np.interp(src_bins, np.arange(bins), row) for row in sp2])
    y = pyworld.synthesize(f0_new, np.ascontiguousarray(sp2), np.ascontiguousarray(ap2), TTS_SR, FRAME)
    y = _finish(y)
    body = y[int(pre * FS * OUT_SR):] if pre else y
    rms = np.sqrt(np.mean(body[:max(len(body), 1)] ** 2)) + 1e-9
    if vowel_only:
        v = body[:max(int(max(room, 1) * FS * OUT_SR), 1)].copy()
        fi, fo = min(int(.012 * OUT_SR), len(v) // 4), min(int(.04 * OUT_SR), len(v) // 3)
        v[:fi] *= np.linspace(0, 1, fi)
        v[len(v) - fo:] *= np.linspace(1, 0, fo)
        v = signal.sosfilt(_VOWEL_LP, v)
        return 0.0, v * (level / rms)
    return pre * FS, y * (level / rms)


def rap(text, seconds, voice=RAPPER, pitch=.92, level=.14):
    """A spoken line fitted to a length: Piper's own pace first, then WORLD for the exact fit, the pitch a little
    lower and flatter (more attitude)."""
    x = tts(text, voice)
    natural = len(x) / TTS_SR
    ls = float(np.clip(seconds / natural, .55, 1.6))
    x = tts(text, voice, round(ls, 2))
    f0, sp, ap, _ = analyse(x)
    n = len(f0)
    want = max(int(round(seconds / FS)), 1)
    src = np.linspace(0, n - 1, want)
    sp2, ap2 = _interp_frames(sp, src), _interp_frames(ap, src)
    f = np.interp(src, np.arange(n), f0)
    vo = _interp_frames((f0 > 0)[:, None].astype(float), src)[:, 0] > .5
    mean = np.exp(np.mean(np.log(f[vo]))) if vo.any() else 100.0
    f = np.where(vo, mean * pitch * (f / mean) ** .6, 0.0)   # flatter: 60 % of the speech's own melody
    y = pyworld.synthesize(f, np.ascontiguousarray(sp2), np.ascontiguousarray(ap2), TTS_SR, FRAME)
    y = _finish(y)
    return y * (level / (np.sqrt(np.mean(y ** 2)) + 1e-9))
