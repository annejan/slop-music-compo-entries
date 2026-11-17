# Sound design recipes and DJ delivery

Two goals: make `warm_boot.py` and `segfault.py` sound more like real 1990s
records, and hand the DJ files that mix without trouble. This file does not
repeat `mellow-house-90s.md` or `eurodance.md`.

**The all-AI rule.** No human edits audio. Code tracks change only by code that
Claude writes. A classic manual fix (DAW cut, hand mastering, manual
time-stretch) is marked "not for us" with a code-only alternative.

**Marks.** "(unverified)" means no primary source was found and the number is
an engineering starting point. "(measured)" means measured here.

## Measured state of our renders (measured, ffmpeg `ebur128=peak=true`)

| File | Integrated | True peak |
|---|---|---|
| `segfault_132bpm_Am.wav` | -9.5 LUFS | **+0.2 dBTP** (over full scale) |
| `warm-boot_120bpm_Am.wav` | -10.7 LUFS | -0.3 dBTP |

The limiter in `engine.mixdown` checks sample peaks only. Peaks between the
samples still go over 0 dBFS. An MP3 encode or a player's resampler can clip.

---

# A. Sound design

## Korg M1 "Organ 2" (house organ bass and stab)

- A sampled organ preset, not an analogue patch. It is the bass of Robin S
  "Show Me Love". "Organ 1" is less punchy.
- MusicRadar's no-M1 recipe, as ratios over the bass note f0:
  - Osc 1: triangle/saw at the lowest footage (32'), ratio 1. Low rumble.
  - Osc 2: square at 4', three octaves up, ratio 8. The "flutey" top.
  - Osc 3: triangle at 8', ratio 4, for body. A variant tunes it a fifth up.
  - Filter envelope: instant attack, medium decay, sustain 0, medium release,
    amount 75 %. Amp envelope: instant attack, long decay, sustain 50 %.
  - Effects: hall reverb and some chorus. Overdrive for grit.
- In ms (unverified): amp attack 1-2 ms, decay to 50 % over 300-500 ms. Filter
  decay 150-250 ms from about 4 kHz to about 600 Hz, Q about 1. Key click: 3-5
  ms of noise band-passed at 2-8 kHz.
- Our `engine.organ()` is a good stab (partials 0.5-8, `exp(-t*7)`). It has no
  sustain, so it cannot play a held organ bass.

## DX7 "E.PIANO 1" (the 90s house Rhodes)

Parsed from the factory ROM1A sysex dump (voice 11). Real values, not a
reconstruction. Algorithm 5: three 2-operator stacks in parallel.

| Pair | Modulator | Carrier | Role |
|---|---|---|---|
| A | OP2 ratio **14.00**, level 58, velocity sens **7**, fast decay (R2 50) | OP1 ratio 1.00, detune +3 | the tine "bark" |
| B | OP4 ratio 1.00, level 89, vel sens 6 | OP3 ratio 1.00 | the body |
| C | OP6 ratio 1.00, detune +7, level 79, vel sens 6, **feedback 6** | OP5 ratio 1.00, detune -7 | warmth, beating |

- The tine pair is quiet unless the key is hit hard (sens 7 of 7). Hard notes
  bark, soft notes are round. The +7/-7 detunes beat slowly: a built-in chorus.
- Index conversion (unverified): about 0.75 dB per level step. Level 58 gives
  an index of about 0.3-1.0 with velocity. Levels 79-89 give about 1-3.
- Our `engine.rhodes()` uses a 1:1 "bark" and an additive sine at 7.1 x f. The
  real patch uses an FM modulator at 14 x f. That is the missing metallic
  attack.

## Juno-style string pad

- Juno-60: one DCO per voice (saw, pulse with PWM, sub), a 24 dB/oct resonant
  low-pass and a non-resonant high-pass. Chorus: bucket-brigade delays
  (MN3009). Mode I about 0.4 Hz, mode II about 0.6 Hz, both together stronger.
- Chorus delay range about 1.5-5.5 ms, L/R in opposite LFO phase, wet
  low-passed near 8-10 kHz (unverified).
- Recipe (unverified): 1 saw plus a 50 % pulse with PWM at 0.5-1 Hz per note.
  Cutoff 2-3 kHz with key tracking, low resonance, HPF about 150 Hz. Attack
  200-500 ms, release 0.8-1.5 s. Then chorus I.
- Our `engine.pad()` is a 5-voice supersaw: a late-90s trance pad. Its width
  comes from detune, not chorus, so it sounds thinner and more modern.

## Drums: 909, 808, swing

- **909 kick:** a saw shaped close to a sine. One envelope sweeps pitch down,
  one sets level. Low-passed noise plus a short pulse make the click (SOS). It
  takes distortion well. Start (unverified): sweep from 150-250 Hz to a 50-60
  Hz body in 30-50 ms, amp decay 200-500 ms, click 3-10 ms. Our `kick()` fits
  (`base 46-50`, `punch 90-130`, 36 ms sweep). Tune the body to A1 = 55 Hz.
- **808 kick:** a bridged-T resonator that rings by itself. Near-sine, small
  pitch drop, much longer ring than a 909. Good for deeper mellow house.
- **808 metal:** six squares at 205.3, 304.4, 369.6, 522.7, 540 and 800 Hz
  (forum sample analysis), then band-pass and high-pass. Our `METAL` is right.
  `hat()` multiplies it by 1.7, which drifts from the 808 colour.
- **909 hats and cymbals:** 6-bit samples (Wikipedia). Coarse quantisation is
  part of the sound.
- **Clap:** 3-4 noise bursts about 10 ms apart, then a 100-200 ms tail,
  band-pass centre about 1-1.5 kHz (unverified). Our `clap()` (bursts at
  0/9/19/27 ms, 59 ms tail) is close. Its 900-5500 Hz band is brighter.
- **Swing:** Roger Linn defines it as the ratio between the first and second
  16th in each 8th. 50 % is straight, 54 % loosens without sounding swung, 66 %
  is a triplet, the useful range is 50-70 %. The 909 has a global shuffle knob
  scaled per instrument. No measured 909 percentages were found. House sits at
  54-62 % (unverified). `warm_boot.py` uses `SWING = .16 * STEP` = 58 %: keep
  it. Eurodance stays straight, as in `segfault.py`.

## Eurodance stabs, bass and pump

- **Supersaw (JP-8000, Szabo's thesis):** 7 saws, non-linear detune. Relative
  offsets at full detune: -0.110, -0.063, -0.0195, 0, +0.0199, +0.062, +0.107
  (times a detune factor). The inner pair is about 18 % of the outer spread.
  Gains: centre `-0.55366*mix + 0.99785`, sides `-0.73764*mix**2 + 1.2841*mix
  + 0.044372`. Our `supersaw()` spaces voices evenly, so it lacks the dense
  core with wide edges.
- **Alpha Juno "hoover":** PWM on the saw cuts two "holes" and makes it sound
  octave-doubled. Add a copy an octave up, detune slightly, push the pitch
  envelope to full (scoop in, drop at release), and use the chorus
  (ReDominator author). Times (unverified): -12 st scoop over 80-200 ms, PWM
  LFO 4-6 Hz, portamento 50-100 ms.
- **M1 house piano ("Piano 8" or "Piano 16'", sources disagree):** strong,
  slightly clanky, over-bright top. Hollow mid, reduced around 800 Hz-2 kHz.
  Solid bass, mild chorus, low velocity sensitivity so the top stays constant,
  slightly short decay. Our `piano()` lacks the mid scoop, and `vel ** (.4 +
  .08*n)` still varies the top.
- **Orchestra hit:** a layered staccato orchestral chord. Fairlight ORCH5 is an
  **8-bit** sample of the opening chord of the "Infernal Dance" (Firebird),
  pitched down a minor sixth. Early hits ran under 1 s. The low-bit grit is
  part of the sound. Our `orch_hit()` is clean.
- **Offbeat bass:** one note per offbeat leaves room for the kick without
  ducking. Octave jumps add motion. A eurodance blog names the TX81Z "Lately
  Bass" (4-op FM, feedback operator for the snap) as the typical bass.
  `segfault.bass()` has the pattern but uses a saw, not FM.
- **Pump:** a kick sidechain ducks the music. Release 20-75 ms is subtle. A
  quarter-note release (500 ms at 120 BPM) pumps audibly. The obvious pump is
  late-90s French house. Early-90s eurodance used little (unverified). Our
  `mixdown` duck has a 0.18-beat time constant (82-90 ms). The segfault bass
  lands 227 ms after the kick, so its duck of 0.3 barely acts. That is right.

## What makes a mix sound 90s

- **Gear:** Akai S900/S950 12-bit samplers (7.5-40 kHz), Akai S1000, Mackie
  desks, Alesis Quadraverb, Lexicon reverbs. Compression was light (forum
  consensus, anecdotal).
- **Reverb (unverified):** short plate, 1.0-1.8 s, 10-30 ms pre-delay, on clap
  and snare. Hall, 2-3 s, 20-40 ms pre-delay, on pads and vocals. Damp highs
  above 6-8 kHz. Our room is one noise impulse response (RT60 about 2.5 s), no
  pre-delay, no early reflections, shared by every bus. It smears the drums and
  the robot's consonants.
- **Delay:** dotted-eighth or eighth, 2-4 repeats, band-limited. Our ping-pong
  (300-5500 Hz, 5 taps, x0.5) is era-correct.
- **Saturation:** desk and sampler grit, not heavy tape. Soft `tanh` on the
  drum bus, 12-bit quantisation on sampled-style instruments.
- **Loudness:** the average 1990s rock CD sat near -16.8 dBFS RMS. Oasis at -8
  dBFS RMS in 1995 was rare (Wikipedia). No measured 1994 dance dataset was
  found; expect quieter, more dynamic masters than today (unverified). Modern
  club masters sit at -6 to -9 LUFS, -1 dBTP (mastering blogs). Aim for about
  -9 LUFS so the DJ need not ride us up against louder Suno entries. Get there
  with arrangement and gentle glue, not a hard limiter. Keep the transients.

## Making the robot voice intelligible

Our `engine.robot()` is a **formant synth** (a saw through 3 band-passes per
vowel), not a channel vocoder. Both kinds of tip apply.

**Vowels:** Hillenbrand et al. 1995, men, mean Hz at steady state, plus F1/F2
at 80 % of the vowel (the drift):

| Code | Word | F1 | F2 | F3 | F1@80% | F2@80% |
|---|---|---|---|---|---|---|
| iy | heed | 342 | 2322 | 3000 | 342 | 2317 |
| ih | hid | 429 | 2033 | 2686 | 466 | 1841 |
| ei | haid | 476 | 2089 | 2691 | 399 | 2229 |
| eh | head | 587 | 1802 | 2604 | 560 | 1745 |
| ae | had | 591 | 1930 | 2595 | 632 | 1720 |
| ah | hod | 756 | 1308 | 2534 | 705 | 1460 |
| aw | hawed | 655 | 1023 | 2521 | 657 | 1265 |
| uh | hud | 621 | 1181 | 2547 | 573 | 1493 |
| oa | boat | 497 | 910 | 2459 | 434 | 897 |
| oo | hood | 469 | 1122 | 2434 | 483 | 1489 |
| uw | who'd | 379 | 992 | 2355 | 368 | 1027 |
| er | heard | 474 | 1379 | 1710 | 442 | 1483 |

- **Diphthongs:** hold the first target about 60 % of the time, then glide.
  /aɪ/ ("my", "night") = ah to ih. /aʊ/ = ah to oo. /ɔɪ/ = aw to ih. The
  engine's `"i"` is the "heed" vowel, too far for a diphthong end: add `"ih"`.
- **Consonants (textbook values, unverified here):**
  - w, r, l, m, n last only 40-80 ms. `robot()` spreads every target evenly
    over the syllable, so in "w-o-r-m" the w and r each get a quarter of the
    note. That blurs words.
  - Stops: put a 30-60 ms silence before the burst. p/t/k need 50-80 ms of
    aspiration noise through F2/F3 before voicing. b/d/g voice at release.
  - Glide F2 from a locus into the vowel over 30-50 ms: about 800 Hz for b/p,
    1800 Hz for d/t, about 2300 Hz for g/k before front vowels.
  - Nasals: 6-10 dB quieter, low-passed near 500 Hz.
- **Carrier:** a bright saw is right. Squares sound hollow. The carrier must
  cover the formants: no carrier treble means no output treble.
- **Unvoiced sounds:** a separate high-pass path for sibilants and plosives
  ("HF emphasis") restores consonants. Our noise bursts do this; keep them loud.
- **Real vocoder band count:** 4-8 bands already give high sentence
  intelligibility in research. MusicRadar says use the maximum, Apple says it
  matters little. Use 16-20 if we build one.
- **Mix:** reverb and echo smear consonants. `Song.sing()` defaults to
  `wet=.3, echo=.25`. Use about 0.1 each, with an echo throw only on the last
  word of a line.

---

# B. DJ-side delivery

## Keys (Camelot) and tempo

- A minor is **8A**. Safe moves: 8A, 7A (D minor), 9A (E minor), 8B (C major).
  B minor is **10A**. 8A to 10A is Mixed In Key's "+2 energy boost", exactly
  Segfault's key change.
- Warm Boot uses only A-minor diatonic chords, so a detector says 8A or 8B.
  Both are safe.
- **Genre anchors:** Robin S "Show Me Love" is 120 BPM, A minor, 8A: the same
  tempo and key as Warm Boot, so the DJ can layer them. Culture Beat "Mr. Vain"
  is about 133 BPM, A minor in most analyses. Corona "Rhythm of the Night" is
  128 BPM, C minor or F minor (sources disagree). Haddaway "What Is Love" is
  about 124 BPM, G minor (6A).
- Both tempos are good: 120 is deep-house range, 132 is the 1993-95 core.
- **Stretch limits:** about 6 % equals 1 semitone. 120 to 132 is +10 %, +1.65
  semitones without key lock, which lands between keys. With key lock (Master
  Tempo) artefacts start above about 4-5 %. CDJ ranges are ±6/10/16/100 %. The
  days are separate sets, so our two tracks never mix with each other.
- **Our advantage:** code renders at any BPM and key. If the DJ names a set
  tempo, render at it. Manual time-stretching is not for us anyway.

## File format, USB, names, tags

- WAV or AIFF at 44.1 kHz/16-bit plays on every Pioneer player since
  CDJ-900/2000. Older players stop at 48 kHz/24-bit, so no 96 kHz.
  `engine.mixdown` writes plain PCM WAV (format tag 1) through Python `wave`.
  That avoids the `WAVE_FORMAT_EXTENSIBLE` header some CDJs refuse.
- WAV has no common tag standard; CDJs often show only the file name. AIFF and
  MP3 carry ID3 tags (v1 to v2.4) that CDJs read.
- **Deliver per track:** (1) AIFF 44.1/16 with ID3 title, artist, BPM (TBPM),
  key (TKEY) and a comment like "8A, drums-only intro 16 bars"; (2) the same
  audio as WAV; (3) MP3 320 kbps as a fallback. Make all three with one ffmpeg
  call in the render script: format wrapping, not editing.
- **USB:** FAT32 is the only file system every Pioneer CDJ reads. exFAT works
  only on newer units (CDJ-3000, XDJ-RX3 and others). Bring a second stick.
- **Names:** ASCII only, none of `\ / : * ? " < > |`. Put BPM and key in the
  name in case tags do not show: `Claude - Warm Boot (Club Mix) 120bpm 8A.aiff`.

## Loudness for club play

- Target about **-9 LUFS integrated** (±1), ceiling **-1 dBTP**. Club practice
  is -6 to -9 LUFS, and -1 dBTP survives MP3 encoding. Warm Boot can sit 1 dB
  lower: a mellow track does not need to win.
- Fix Segfault's +0.2 dBTP in code (change 1 below). Hand mastering is not for
  us. Downloads are not normalised: the DJ gets our level and only trims it.

## Structure the DJ expects

- Everything comes in 8-bar blocks, grouped as 16 or 32. Big changes land on
  bars 1, 9, 17, 25 ... Intros and outros run 16-32 bars, drums first.
- Both arrangements change only on multiples of 8, with 16 drums-only bars at
  each end. The grid starts at sample 0 and the tempo is exact. Keep all that.
- **House:** DJs blend for 16-32 bars, with a bass swap on a phrase boundary.
  Warm Boot's bars 16-31 (bass plus muffled Rhodes) are a second mix zone.
- **Eurodance:** shorter mixes of 8-16 bars, or a cut after a chorus
  (unverified). At 132 BPM, 16 bars is only 29 s.
- **Edits:** give one club mix per day. A radio edit is not needed for a
  DJ-mixed compo. If a length limit appears, render a shorter arrangement from
  code. A DAW cut is not for us.

---

# Concrete changes for our code tracks

Ranked by benefit for the effort.

1. **`engine.Song.mixdown`: true-peak limiter, LUFS target, dither.** Detect
   peaks on a 4x oversampled copy (`scipy.signal.resample_poly(x, 4, 1)`), set
   the ceiling to -1 dBTP (0.891), and drop the hard `np.clip(..., .97)`.
   Replace `rms_db` with `lufs=-9.0`, measured with BS.1770 K-weighting
   (pyloudnorm or two biquads). Add TPDF dither before `astype("<i2")`; the
   cast now truncates. Then use `lufs=-9.0` in `segfault.py` and `lufs=-10.0`
   in `warm_boot.py`. This fixes the measured +0.2 dBTP.
2. **`--bpm` and `--key` arguments in both tracks.** Pass them to
   `e.Song(bpm=...)`. Add a key offset to every `chord_of`, `root_note`,
   `voicing` and `S.notes(..., key)` call, and `+ KEY` to fixed MIDI numbers in
   `warm_boot_baby`, `spell` and the others. Write BPM and Camelot code into the
   file name. We then match the DJ's tempo and key with no stretching.
3. **`engine.robot` intelligibility.** Hold `w r l m n` targets 50 ms and give
   the vowel nucleus the rest. Update `VOWELS` to the Hillenbrand table and add
   `ih`, `oo`, `uh`, `ae`, `er`. Insert 40 ms silence before stop bursts and 60
   ms of aspiration through F2/F3 after p/t/k. Lower `Song.sing` defaults to
   `wet=.12, echo=.08`.
4. **New `engine.chorus(x, rate=.4, lo_ms=1.5, hi_ms=5.5, mix=.5)` and a Juno
   `engine.pad()`.** Use 1 saw plus 1 PWM pulse per note instead of
   `supersaw(... voices=5)`, HPF at 150 Hz, then chorus with L/R in opposite
   phase. Also chorus `rhodes` and `piano` at 0.3 mix.
5. **`engine.rhodes` as DX7 E.PIANO 1.** Replace `high = .12*vel*sin(2π·7.1f·t)`
   with an FM tine `sin(2πft + I_t·sin(2π·14f·t))`, `I_t ≈ 1.2*vel**2*exp(-t*25)`
   (unverified scale). Add a third 1:1 pair detuned ±3 cents.
6. **`engine.supersaw` offsets and gains from Szabo.** Use `det = spread * [-1,
   -.572, -.177, 0, .181, .565, .977]` and the centre/side gain formulas with a
   `mix` argument. Affects `segfault.riff()`; apply the same to `lead()`.
7. **New `engine.organ_bass(m, d)`** from the Organ 2 recipe: ratios 1
   (tri/saw), 4 (triangle), 8 (square); amp decays to 50 % over 400 ms; filter
   envelope from 4 kHz to 600 Hz over 200 ms; key click. In `warm_boot.py`, use
   it instead of `deep_bass` in bars 48-63 and 72-87 with a new syncopated line.
   Do not copy the "Show Me Love" riff.
8. **Two reverbs in `mixdown`.** A plate (1.2 s, 15 ms pre-delay) for `drums`,
   `perc` and `vox`. A darker hall (2.5 s, 35 ms pre-delay) for `pads`, `keys`
   and `lead`. `put(..., wet=)` then picks the reverb per bus.
9. **New `engine.crush(x, bits, rate)`.** `orch_hit` at 8 bits and about 22
   kHz, `hat()` at 6 bits, `piano`/`organ` at 12 bits. Add a -3 dB scoop at
   800 Hz-2 kHz to `piano()` and flatten its velocity tilt.
10. **Kick tuning.** In both `drums()` functions, change `base=50` (segfault)
    and `base=46` (warm_boot) to `base=55` (A1), so the kick sits in the key.
11. **New `engine.hoover(m, d)`** for a segfault build or a surprise theme: PWM
    saw plus an octave-up copy, slight detune, -12 st scoop over 120 ms,
    chorus II.
12. **Tag comment for Segfault.** The last chorus is in 10A, but the outro is
    drums-only, so mixing out is key-free. Say so in the tag. No audio change.

---

## Sources

- M1 organ bass: https://www.musicradar.com/tuition/tech/how-to-create-a-korg-m1-style-organ-bass-sound-642650
- Organ 2 history: https://gijs.substack.com/p/the-legendary-korg-m1-organ-2-preset
- DX7 ROM1A sysex (parsed locally): https://github.com/mmontag/dx7-synth-js/tree/master/roms
- Juno-60: https://en.wikipedia.org/wiki/Roland_Juno-60
- TR-909: https://en.wikipedia.org/wiki/Roland_TR-909 ; manual: https://www.rolandcloud.com/getmedia/a88fc05f-0b9f-4ba2-8266-b2272ba31572/TR-909-Manual-E.pdf?ext=.pdf
- SOS Synth Secrets: https://www.soundonsound.com/techniques/practical-bass-drum-synthesis ; https://www.soundonsound.com/techniques/practical-snare-drum-synthesis
- 808 metal frequencies: https://www.kvraudio.com/forum/viewtopic.php?p=7494787 ; https://www.elektronauts.com/t/hh-lab-tips/207960
- Roger Linn on swing: https://www.attackmagazine.com/features/interview/roger-linn-swing-groove-magic-mpc-timing/
- Szabo supersaw: https://gist.github.com/audionerd/fe50790b7601cba65ddd855caffb05ad ; https://web.archive.org/web/20191104212834/https://www.nada.kth.se/utbildning/grukth/exjobb/rapportlistor/2010/rapporter10/szabo_adam_10131.pdf
- Hoover: https://www.musicradar.com/how-to/how-to-design-a-dominator-style-hoover-sound-with-audiorealisms-redominator
- House piano: https://planetbotch.blogspot.com/2014/10/the-house-piano-sound-explained.html ; https://www.musicradar.com/tuition/tech/get-the-sound-of-blackboxs-ride-on-time-554275
- Orchestra hit: https://en.wikipedia.org/wiki/Orchestra_hit
- Offbeat bass: https://theproducerschool.com/blogs/featured-blogs/5-essential-bass-patterns-that-define-hard-house-and-trance-music ; https://www.edmprod.com/bass-lines-tips/ ; https://eurodancetutorial.blogspot.com/2012
- Sidechain: https://www.sonarworks.com/blog/learn/sidechain-compression ; https://www.soundonsound.com/node/4908058
- 90s gear (anecdotal): https://libreddit.winscloud.net/r/edmproduction/comments/1exrc5c/what_makes_90s_percussion_signature_sound
- Loudness: https://en.wikipedia.org/wiki/Loudness_war ; https://www.masteringthemix.com/blogs/learn/song-mastering-for-cd-club-play-and-streaming ; https://www.mixgraph.io/tools/lufs-meter
- Hillenbrand 1995 data: https://github.com/santiagobarreda/hillenbrand_et_al_1995
- Vocoders: https://www.musicradar.com/how-to/how-to-get-the-most-out-of-vocoders-a-complete-guide ; https://help.apple.com/mainstage/mac/2.2/en/mainstage/logicproinstruments/chapter_10_section_9.html ; https://pmc.ncbi.nlm.nih.gov/articles/PMC2730710
- Camelot: https://mixedinkey.com/workflows/how-to-use-the-camelot-wheel/
- Key lock and tempo: https://wearecrossfader.co.uk/blog/key-lock/ ; https://www.mixgraph.io/tools/pitch-tempo
- Pioneer formats: https://github.com/joeselway/Pioneer-DJ-File-Formats ; https://www.pioneerdj.com/en-us/product/player/cdj-3000/white/specifications/ ; https://manualslib.com/manual/1196325/Pioneer-Cdj-2000nxs2.html?page=7
- WAV metadata: https://support.disco.ac/home/q-why-is-there-no-metadata-appearing-in-my-wav-files
- Phrasing: https://www.djkit.com/blogs/news/djing-rule-of-32 ; https://cursa.app/en/page/dj-mixing-foundations-bars-phrasing-and-starting-on-the-one
- Track keys: https://www.mixgraph.io/tracks/robin-s-show-me-love ; https://songbpm.com/@corona/the-rhythm-of-the-night ; https://www.karaoke-version.com/mp3-backingtrack/haddaway/what-is-love.html ; https://songs.klang.io/en/s/Culture%20Beat/Mr.%20Vain%20-%20Original%20Radio%20Edit/VAmq5-wcLHE
