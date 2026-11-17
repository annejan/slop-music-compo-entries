# How fast everything renders

Measured on 18 November 2026 on this laptop: AMD Ryzen AI 7 PRO 350 (8 cores,
16 threads), 27 GB RAM, Radeon 860M (Vulkan, RADV). The machine did nothing
else during the runs. Times are wall-clock time. With a game or other renders
running at the same time, the times double or triple.

"Warm" means the speech and the room simulation are already in `code/.cache/`.
That is the normal case after the first render of a song.

## The code tracks

| Song | Length | Render (warm) | Peak memory |
|---|---|---|---|
| Warm Boot | 4:02 | 18 s | 3.0 GB |
| Packet Loss (Of Love) | 3:58 | 21 s | 3.2 GB |
| Low Battery Lullaby | 4:02 | 19 s | 3.0 GB |
| Low Pass Love | 4:14 | 24 s | 3.2 GB |
| Segfault (In My Heart) | 3:26 | 27 s | 2.5 GB |
| Blinky (The LED Song) | 3:26 | 34 s | 2.5 GB |
| The Rhythm Of The Badge | 3:37 | 21 s | 2.7 GB |
| Race Condition | 3:21 | 22 s | 2.4 GB |
| template.py | 3:32 | 30 s | 2.5 GB |

| Other jobs | Time |
|---|---|
| `PREVIEW=48-64` (16 bars), Warm Boot / Segfault | 9 s / 18 s |
| Segfault with an empty speech cache (Piper speaks every word, WORLD analyses it) | 55 s |
| The room simulation (`room.py`, 7 x 5 x 3 m, 1.8 s), once per room | 7 s |
| `share.py`: 16 MP3s (radio edits and DJ versions) | 24 s |

Most of a warm render is the mixdown: the reverb convolution, the true-peak
limiter (4 times oversampled) and the loudness measurement. The notes and the
sounds take a few seconds.

## DiffSinger (Hanami, through warble, on the CPU)

| Job | Time |
|---|---|
| Segfault's chorus alone (9 s of singing) | 9 s |
| The Rhythm Of The Badge with `DIVA=ds:hanami`, no caches (all of the diva's part) | 75 s |
| The same, the part cached in `code/.cache/` | 21 s (as without DiffSinger) |

warble uses all 16 threads (12 minutes of CPU time for the 75 s render). It
also caches each phrase in `~/.cache/warble/`: when only a few lines change,
only those phrases render again.

## ACE-Step 1.5 (acestep.cpp, Vulkan on the Radeon 860M)

Turbo DiT (Q8_0, 8 steps) and the 1.7B LM (Q8_0).

| Song length | LM (lyrics to audio codes) | DiT | VAE decode | Total |
|---|---|---|---|---|
| 1:29 | 15 s | about 12 s | 17 s | 45 s |
| 3:30 | about 31 s (34 tokens/s) | 25 s | 40 s | 102 to 139 s |

Peak memory: 2 GB. `master.py` (beat grid to sample 0, 44.1 kHz, -10 LUFS,
-1.2 dBTP) takes 6 s for a 3:30 song.

The research guess was 3 to 8 minutes for a 3-minute song; it is about 2
minutes. The 4B LM and the base DiT (for adding vocals over our own tracks) are
not measured yet.

## What this means for a surprise theme (2 hours)

- A new code track from `template.py`: a 16-bar preview in under 20 s, the
  whole song in under a minute (the first render, with new words for Piper,
  about a minute more).
- An ACE-Step take: about 2 minutes, so 10 to 20 takes fit easily. Every take
  needs `master.py` before it goes to the DJ.
