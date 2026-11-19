# Pull-Up Resistor: why the rehearsal song sucked (19 November)

The dress rehearsal: an agent alone made a happy hardcore song from WEEKEND.md, picking takes with fit.py and
Whisper, without ears. The user: "the Pull-up resistor song sucks . . ass . . . mostly the high pitched singing ..
but also . . some of the rest". This note is what was measured afterwards and what changed.

## The diva: three faults, all in our chain

1. **A band under the voice.** ACE-Step ignored "a cappella vocals only, no instruments": the pinned keeper
   carried a drone of bass and pads (no drums) at -3 dB against the voice. In the mix it played its own chords
   under the kit (on the kit's triad only 58 % of the time; bar 56: G-ish with C# and D# over F). Of about 120
   ACE-Step takes on disk, about half carry such a band (clean by low-band share: 1 of 34 turbo drafts, 58 of 172
   SFT takes; Chorus tags 24 %, Rap 67 %).
2. **Too high.** The voice alone sat at A4 (median of the steady notes), top 10 % A5; the lift's +3 made it C5 and
   C6. Overclocked Heart's diva, which the user likes: F#4, top B4 (lifted 3: A4, top G5).
3. **Two bars off.** fit.py tracked ACE-Step's bass, not the voice (the "register" of the full take read A2), so it
   chose "one bar later". On the voice alone the take fits best one bar earlier (68 % against 36 % one bar
   later): it played two bars from its best place, every line starting on an odd bar, off the crash and the fills.

## The lab: what keeps the band out (8 rounds of 4, every take split and measured)

| Setting | Band (dB, mean of 4) | Register |
|---|---|---|
| the rehearsal's caption, turbo | -3 | A4, top C#5 (high after +3) |
| + negative prompt against instruments | -3 | same |
| + lm_cfg_scale 3.5 | -2 | same |
| a voice-first caption | -5 | D4-E4: about 6 semitones lower |
| + "shrill, chipmunk" in the negative prompt | -5 | D4-F#4 |
| a caption without genre words, turbo | -7 | D4-E4 |
| the same LM codes, SFT DiT | -23 (one take -39, clean) | D4-E4 |
| Overclocked Heart with these settings | -25 (baseline -2) | two high, one low: "soaring", "powerful" pull it up |

The turbo DiT adds the drone: the same codes are much cleaner with SFT. The LM side (no genre words, the negative
prompt) is needed too: SFT re-renders of banded codes kept their band. About 1 take in 4 still has a band, so
every draft is split.

## What changed

- `sep.py` (new): Mel-Band RoFormer through the audio.cpp v0.9.5 prebuilt, about 0.8x real time; the voice alone
  and the band's level (Overclocked Heart's approved take -45 dB, the rehearsal's -3 dB; clean below -25 dB).
- `takes.py`: drafts with the SFT DiT and `LM_NEGATIVE`; the round splits every draft and ranks, finishes and
  plays the voice alone; `--keep` gives the voice alone; `drafts(extra=...)` for more request fields.
- `fit.py`: the register (median and top 10 % of the steady notes) after the shift, HIGH above A#4 / G5 and 4 points
  of rank per semitone; the shift chosen among the shifts nearly as much on the scale by chord fit and register;
  offsets in 2-bar steps.
- `kit_template.py`: the first chorus's take cut before the break (bar 64: the rehearsal's take ran a bar into the
  break as the loudest moment of the song, -6.5 LUFS, then dropped 8.9 dB into a hole); `DIVA_GAIN` a test switch
  starting lower; `say()` warns when a line runs into the next.
- WEEKEND.md: the caption pattern (the voice only, no genre words), the new table, the 2-bar offsets.

## The rest (a critic agent against Overclocked Heart; numbers, not ears)

Not yet changed, waiting for the user's ears:
- No build into either chorus: the riser sits at bar 28, and the build keeps the kick, so the last chorus's drop is
  0.9 dB quieter than the build (Overclocked Heart takes the kick out in 78-79).
- The genre's hook plays in 5 of 112 bars: the template mutes the whole lead bus under the diva.
- The narrators are slow storytellers over 170 BPM (0.9 syllables a beat against Overclocked Heart's 2.4); one line
  ran 0.7 s into the next.
- Near mono: side/mid -19 to -20 dB against Overclocked Heart's -12 to -13.
- The kick is a sub boom with little 60-200 Hz body (sub share 66 % in the drums section, Overclocked Heart 23 %).
- The MC's first shout is masked by the snare roll and riser starting in the same bar.
- Loudness, harshness, mud and pumping are like Overclocked Heart's.

The fixed chorus as an A/B for the phone: `renders/scratch/Pull-Up Resistor, the chorus fixed (phone).mp3`
(A the rehearsal; B its take without the band, on the phrase grid, still +3; C another draft's voice, -4;
D a lab take clean from the start, +3, around F4; E the same at -2).
