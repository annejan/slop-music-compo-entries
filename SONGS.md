# What is in each song

Every part of every entry is made by AI. This file lists, per song, which AI
made which part, and which tools and sounds it uses.

## Who made what

| Part | Made by |
|---|---|
| Lyrics, style prompts, song structure | Claude (Opus 5.5, in Claude Code) |
| Code tracks: every note, every sound, the mix | Claude, as Python code |
| Sung and rapped voices in Segfault | Piper (neural text-to-speech), re-pitched by code that Claude wrote |
| Audio of the Suno takes | Suno (v6) |
| Research notes | Claude research agents, from cited web sources |
| Themes | The organisers |
| Choosing the take to hand in | A human, by listening |

---

## Saturday: 90's mellow house

### Warm Boot (code track)

[code/warm_boot.py](code/warm_boot.py)

| | |
|---|---|
| Tempo, key | 120 BPM, A minor |
| Chords | Am9, Fmaj9, Dm9, Em7 (one bar each) |
| Length | 120 bars, 4:02 |
| Loudness | -10 LUFS, -1.2 dBTP |
| DJ intro, outro | 16 bars of drums only at each end |

Structure: intro (drums), bass, a filtered Rhodes, verse, chorus, a filtered
break, chorus with a Rhodes melody, wind-down, outro (drums).

Sounds, all synthesised in [code/engine.py](code/engine.py):

- **Drums:** a soft sine kick, a clap with a snare under it, 808-style metallic
  hats with a 58 % shuffle, a shaker, rimshots.
- **Bass:** a round deep-house bass: a sine, a little saturation, a little saw.
- **Keys:** an FM electric piano (Rhodes) that comps the chords and plays the
  melody in the second chorus; M1-style organ stabs in the choruses.
- **Pads:** a slow supersaw string pad, and an "ooh" choir made from formant
  filters.
- **Effects:** vinyl crackle all through, a riser and a downlifter around the
  break.
- **Voice:** the formant robot (a saw through vowel filters) sings "warm boot,
  baby", "all night long", "bring me back up slow" and "standby".
- **Mix:** the kick ducks the pads and the bass; a dotted-eighth ping-pong
  delay; a noise reverb; the master filter closes in the break; a glue
  compressor; a true-peak limiter.

### Suno takes

Prompts and lyrics in [suno/saturday-mellow-house.md](suno/saturday-mellow-house.md).
Lyrics and prompts by Claude; audio by Suno.

| Take | Title | Tempo, key | Style |
|---|---|---|---|
| A (best) | Warm Boot | 120 BPM, A minor | deep house, Rhodes, M1 organ, soulful female vocal |
| B | Packet Loss (Of Love) | 122 BPM, F minor | garage house, male and female duet, saxophone |
| C | Low Battery Lullaby | 120 BPM, D minor | instrumental deep house, vocal chops |
| D | Low Pass Love | 122 BPM, A minor | French house, filtered disco loop, talk box hook |

---

## Sunday: eurodance

### Segfault (In My Heart) (code track)

[code/segfault.py](code/segfault.py)

| | |
|---|---|
| Tempo, key | 132 BPM, A minor; B minor in the last chorus (bar 80) |
| Chords | Am, F, C, G (one bar each) |
| Length | 112 bars, 3:26 |
| Loudness | -9 LUFS, -1.2 dBTP |
| DJ intro, outro | 16 bars of drums only at each end |

Structure: intro (drums), the riff behind a filter, sung verse, rap,
pre-chorus with a snare roll, chorus, filtered break, build with rap, last
chorus a tone up, outro (drums).

Sounds, all synthesised in [code/engine.py](code/engine.py):

- **Drums:** a punchy kick, clap and snare, closed and open hats, snare rolls.
- **Bass:** an offbeat saw-and-sub bass with an octave jump.
- **Riff and keys:** supersaw stabs, a rave piano, a supersaw lead that doubles
  the chorus hook.
- **Pads and effects:** a string pad, orchestra hits, risers, downlifters.
- **Mix:** as Warm Boot, but louder.

Voices, made in [code/voice.py](code/voice.py):

- **The diva** sings the verse, the pre-chorus ("oh oh oh, something's going
  wrong") and the chorus. Piper's `en_US-hfc_female-medium` voice speaks each
  word. WORLD (`pyworld`) takes the speech apart and puts it back on our notes.
  The vowel is stretched to the note length, the consonants keep their length,
  and the pitch is tuned hard to the note, with vibrato on long notes. In the
  chorus, two more takes (Piper is a little different on each run) double the
  voice left and right, and a third take sings a third above.
- **The rapper** raps the S-E-G-F-A-U-L-T verse and the build. Piper's
  `en_US-ryan-high` voice speaks each line. WORLD fits it to one bar and makes
  the pitch lower and flatter.
- **The robot** from `engine.py` says "signal eleven" in the break.

### Suno takes

Prompts and lyrics in [suno/sunday-eurodance.md](suno/sunday-eurodance.md).
Lyrics and prompts by Claude; audio by Suno.

| Take | Title | Tempo, key | Style |
|---|---|---|---|
| A (best) | Segfault (In My Heart) | 132 BPM, A minor | female diva chorus, male rap, supersaw riff, key change |
| B | Blinky (The LED Song) | 132 BPM, D major | bubblegum eurodance, cute female vocal, male shouts |
| C | The Rhythm Of The Badge | 134 BPM, E minor | darker eurodance, hoover synth, male rap |

---

## Surprise themes

Not known yet. The plan is in
[suno/surprise-theme-recipe.md](suno/surprise-theme-recipe.md), and ready
prompts for 16 likely genres are in
[research/surprise-genres.md](research/surprise-genres.md).

---

## Software and licences

| What | Licence | In this repository? |
|---|---|---|
| Our code, lyrics, prompts, research notes | MIT | yes |
| numpy, scipy | BSD-3-Clause | no (installed with pip) |
| Piper (`piper-tts`) | GPL-3.0 | no (installed with pip) |
| pyworld (WORLD vocoder) | MIT (pyworld), modified BSD (WORLD) | no (installed with pip) |
| Voice `en_US-hfc_female-medium` | trained on Hi-Fi-CAPTAIN (NICT): CC BY-NC-SA 4.0 | no (downloaded) |
| Voice `en_US-ryan-high` | trained on RyanSpeech: CC BY-NC-SA 4.0 | no (downloaded) |
| Suno audio | depends on the Suno plan (Free: non-commercial) | no |

**The Segfault render is non-commercial.** The two Piper voices are trained
on data under CC BY-NC-SA 4.0. That is fine for a private party. Do not sell
the render. If you share it, credit the Hi-Fi-CAPTAIN corpus (NICT) and
RyanSpeech, and share it under the same terms. Warm Boot uses no voice model.
