"""Voices: a diva that sings our melody and a rapper that raps in time, both made by AI.

Piper (a neural text-to-speech model, run on the CPU) speaks every syllable. WORLD (pyworld) takes the speech
apart into pitch, spectral envelope and noise, and puts it back together on our notes: the vowel is stretched to
the note's length, the consonants keep their own length, and the pitch is tuned hard to the note (the eurodance
"robot diva" sound), with a vibrato on the long notes.

Needs the venv (see README): piper-tts, pyworld, and the voices in code/voices/.
"""
import hashlib
import os
import warnings

import numpy as np
from scipy import signal

warnings.filterwarnings("ignore", category=UserWarning, module="pyworld")
import pyworld  # noqa: E402
from piper import PiperVoice, SynthesisConfig  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
VOICES = os.path.join(HERE, "voices")
CACHE = os.path.join(HERE, ".cache")
TTS_SR = 22050
OUT_SR = 44100
FRAME = 5.0          # WORLD frame period, ms
FS = FRAME / 1000

DIVA = "en_US-hfc_female-medium"
RAPPER = "en_US-ryan-high"

_loaded = {}


def _voice(name):
    if name not in _loaded:
        _loaded[name] = PiperVoice.load(os.path.join(VOICES, name + ".onnx"))
    return _loaded[name]


def tts(text, voice, length_scale=1.0):
    """Speech for a text, 22.05 kHz, the silence at both ends trimmed; cached on disk."""
    key = hashlib.sha1(f"{voice}|{length_scale}|{text}".encode()).hexdigest()[:16]
    path = os.path.join(CACHE, key + ".npy")
    if os.path.exists(path):
        return np.load(path)
    cfg = SynthesisConfig(length_scale=length_scale, noise_scale=.5, noise_w_scale=.6)
    x = np.concatenate([c.audio_float_array for c in _voice(voice).synthesize(text, cfg)]).astype(np.float64)
    env = np.convolve(np.abs(x), np.ones(110) / 110, "same")
    on = np.nonzero(env > .02 * env.max())[0]
    x = x[max(on[0] - 60, 0):on[-1] + 200] if len(on) else x
    os.makedirs(CACHE, exist_ok=True)
    np.save(path, x)
    return x


def analyse(x):
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


def sing(text, notes, voice=DIVA, glide=.03, vibrato=.35, formant=1.0, level=.12):
    """One syllable sung over one or more notes [(midi, seconds), ...], one after the other.

    Returns (lead_in seconds, mono 44.1 kHz audio): put the audio lead_in seconds before the first note's time,
    so the consonants come just before the beat and the vowel lands on it.
    """
    x = tts(text, voice)
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
    sm = signal.lfilter([alpha], [1, alpha - 1], tgt - tgt[0], zi=[0.0])[0] + tgt[0]
    tau = np.maximum((np.arange(m) - pre) * FS, 0)
    starts = np.concatenate([[0], ends[:-1]])
    since = tau - starts[np.clip(np.searchsorted(ends, tau, side="right"), 0, len(notes) - 1)]
    vib = vibrato * np.sin(2 * np.pi * 5.6 * tau) * np.clip((since - .22) / .25, 0, 1)
    f0_new = np.where(vo, _hz(sm + vib), 0.0)
    if formant != 1.0:   # move the formants up (brighter) or down (darker)
        bins = sp2.shape[1]
        src_bins = np.clip(np.arange(bins) / formant, 0, bins - 1)
        sp2 = np.stack([np.interp(src_bins, np.arange(bins), row) for row in sp2])
    y = pyworld.synthesize(f0_new, np.ascontiguousarray(sp2), np.ascontiguousarray(ap2), TTS_SR, FRAME)
    y = _finish(y)
    body = y[int(pre * FS * OUT_SR):] if pre else y
    rms = np.sqrt(np.mean(body[:max(len(body), 1)] ** 2)) + 1e-9
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
