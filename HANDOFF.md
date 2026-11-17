# Handoff notes

Notes from one Claude session to the next, for work that is not finished. The
newest note is first. Remove a note when its work is done.

## 2026-11-17: the choir behind the diva

**Asked:** "The end of The Rhythm Of The Badge, with the diva and the choir:
the choir is a mess." After the change below the answer was "sounds better,
for now". It was a short interlude in a QtPass session, so only the Badge was
changed.

### What was wrong

Measured on the vox bus of bars 80-95 (the last chorus, `big=True`), before
the mixdown, so before loudness normalisation:

- **Balance.** The five choir voices together were only 0.9 dB under the diva,
  so she did not lead any more. The man an octave down (`en_US-norman-medium`)
  was the loudest choir voice, 3.7 dB under her.
- **Consonants.** Every choir voice is another Piper speaker with its own
  consonant lengths. `diva()` lined up only the vowel onsets (`t - li`), so
  the consonants of the choir landed up to 50-80 ms from the diva's (p10-p90
  per voice; a tight double needs about 15 ms). The choir had 3.5 % of its
  energy at 5-10 kHz, the diva 0.4 %: smeared "f", "th", "sh" on every word.
- All choir voices also had the diva's vibrato (5.6 Hz, same phase), which
  beats between voices.

### What changed

- `voice.sing(..., vowel_only=True)` keeps only the vowel (the stretched
  nucleus), with a 12 ms fade in and a 40 ms fade out, and returns a lead-in
  of 0. The diva sings the words; the choir only follows the vowels. This is
  what a producer does with real backing vocals (tighten or cut their
  consonants).
- `rhythm_of_the_badge.py`, `diva()`: the choir sings `vowel_only=True` with
  `vibrato=.15`. `chorus_lines()` uses `choir=.45` (was .55). The man an
  octave down has gain .6 (was .7).
- Result in bars 80-95: the choir is 5.2 dB under the diva, the doubles 10.4,
  the third above 12.6, the man 12.6, the sixth down 15.3. The choir's 5-10 kHz
  share fell to 1.3 %. The tags (bars 96-103) have the choir 7.4 dB under her.
  The earlier choruses (bars 32 and 56) use the same `diva()`, so they changed
  too.

### Still to do

The other songs still build their choirs the old way: whole words from every
voice, put at `t - li`. They will smear in the same way. Each has its own copy
of the choir code:

- `parts.py` line ~207 (the template's diva with a choir: fix this first, the
  surprise songs start from it)
- `segfault.py` lines ~214-226
- `blinky.py` line ~319
- `packet_loss.py` line ~355
- `race_condition.py`, through `parts.Band` (fixed with `parts.py`)

For each: pass `vowel_only=True` and a lower `vibrato`, put the audio at
`t + late` (no lead-in), then measure the balance again. Aim for the whole
choir about 6 dB under the lead, and the voice an octave down about 12 dB
under.

Not tried yet: a different choir voice set that blends better, a de-esser on
the vox bus, or a vowel ("ooh"/"aah") pad on the chord tones in place of the
words.

### How it was measured

Copy the song script to a scratch folder. In the copy, add a `PART` switch in
`diva()`: `diva` puts only the diva, `choir` only the choir, `c0`-`c4` one
choir voice (index into `parts`). In place of `S.mixdown(...)`, save the raw
bus, for example
`np.save(out, S.bus["vox"][int(S.at(78) * SR):int(S.at(104) * SR)])`. Run it
from `code/` with `PYTHONPATH=.`; with the speech cache it takes about 15
seconds per part. Then compare RMS in dB per section, the 5-10 kHz energy
share, and the lag of the 3-10 kHz envelope of each voice against the diva
(cross-correlation per bar, limited to +-80 ms).

`PREVIEW=78-104 SOLO=vox` gives a quick listen to the vocals alone, but the
mixdown normalises its loudness, so do not compare levels with it.
