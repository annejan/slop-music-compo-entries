# slop-music-compo-entries

Entries for an AI slop music compo. Every day of the party has two themes. The
first theme of each day is known in advance. The second theme comes two hours
before the deadline.

| Day | Theme | Tempo |
|---|---|---|
| Saturday | 90's mellow house | 120 BPM |
| Saturday | surprise | genre norm |
| Sunday | eurodance | 132 BPM |
| Sunday | surprise | genre norm |

The DJ mixes the tracks live, so each track keeps one tempo from start to end,
and starts and ends with 16 bars of drums only.

There are two kinds of entry. Both are fully made by AI.

## 1. Suno prompts: `suno/`

Style prompts and lyrics to paste into [Suno](https://suno.com) (Custom mode).

- [suno/README.md](suno/README.md): how to use the prompts, and tips for the DJ.
- [suno/saturday-mellow-house.md](suno/saturday-mellow-house.md): "Warm Boot",
  "Packet Loss (Of Love)", "Low Battery Lullaby".
- [suno/sunday-eurodance.md](suno/sunday-eurodance.md): "Segfault (In My Heart)",
  "Blinky (The LED Song)", "The Rhythm Of The Badge".
- [suno/surprise-theme-recipe.md](suno/surprise-theme-recipe.md): a two-hour
  plan and a tempo table for the surprise themes.

## 2. Code tracks: `code/`

The same two songs ("Warm Boot" and "Segfault (In My Heart)"), but written by
Claude as Python code. Every note and every sound is in the source: there are no
samples and no loops. The synthesis is numpy and scipy. The voice is a vocoder
robot made from formant filters.

| Script | Theme | Tempo, key | Length |
|---|---|---|---|
| [code/warm_boot.py](code/warm_boot.py) | 90's mellow house | 120 BPM, A minor | 4:02 |
| [code/segfault.py](code/segfault.py) | eurodance | 132 BPM, A minor, then B minor | 3:26 |

[code/engine.py](code/engine.py) holds the shared parts: oscillators,
instruments, drums, the robot voice, and the mixdown (sidechain, delay, reverb,
glue compressor, true-peak limiter). It comes from the soundtrack of the QtPass 2.0 film.

### Render

You need Python 3 with numpy and scipy.

```sh
cd code
python3 warm_boot.py      # writes renders/warm-boot_120bpm_Am.wav
python3 segfault.py       # writes renders/segfault_132bpm_Am.wav
```

Each track renders in about 20 seconds. The output is a 44.1 kHz, 16-bit stereo
WAV. The beat grid starts at sample 0 and the tempo is exact, so a DJ can sync it
without beat analysis.

The renders are not in the repository. Run the scripts to make them.

## Research: `research/`

Notes on the genres, reference tracks with their tempos, and Suno tips.

## License

MIT. See [LICENSE](LICENSE).
