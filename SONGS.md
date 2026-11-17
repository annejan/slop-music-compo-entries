# What is in each song

Every part of every entry is made by AI. This file lists, per song, which AI
made which part, and which tools and sounds it uses.

## Who made what

| Part | Made by |
|---|---|
| Lyrics, style prompts, song structure | Claude (Opus 5.5, in Claude Code) |
| Code tracks: every note, every sound, the mix | Claude, as Python code |
| Sung and rapped voices in Segfault | Piper (neural text-to-speech), re-pitched by code that Claude wrote |
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
- **Keys:** an electric piano that comps the chords and plays the melody in
  the second chorus. It is the E.Piano patch of a DX7-style FM synthesizer
  ([code/dx7.py](code/dx7.py)): six sine operators in algorithm 5, a feedback
  operator, a ratio-14 operator for the bell-like attack, and keyboard
  scaling that makes the high notes softer and darker. M1-style organ
  stabs in the choruses.
- **Pads:** a slow supersaw string pad, and an "ooh" choir made from formant
  filters.
- **Effects:** vinyl crackle all through, a riser and a downlifter around the
  break.
- **Voice:** the formant robot (a saw through vowel filters) sings "warm boot,
  baby", "all night long", "bring me back up slow" and "standby".
- **Mix:** the kick ducks the pads and the bass; a dotted-eighth ping-pong
  delay; the reverb of a simulated 7 x 5 x 3 m room (a 3-D wave simulation in
  [code/room.py](code/room.py), RT60 1.8 s, nothing above 4 kHz); the master
  filter closes in the break; a glue compressor; a true-peak limiter.

The DX7 synthesizer and the room simulation are numpy ports of the NPU demos
in `~/Projects/npu` (MIT), which run on the Ryzen AI NPU there.

### Packet Loss (Of Love) (code track)

[code/packet_loss.py](code/packet_loss.py). Garage house, 122 BPM, F minor,
120 bars, 3:58, -10 LUFS. A late-night duet over a bad network connection.

- **Structure:** intro (drums), organ bass and the DX7 piano behind a filter,
  verse 1 (him, she answers "ACK" and "NACK"), verse 2 (her), chorus with a
  choir that answers "say it once again", sax solo, a break with thunder and
  a terminal voice ("64 bytes from your heart ... packet loss: fifty
  percent"), chorus 2 in which the lead vocals really lose 30 ms packets,
  wind-down to "Request timed out", outro (drums).
- **Sounds:** swung garage drums with congas and rimshots, an M1-style organ
  bass, the DX7 electric piano, a gospel piano, a pad, a tenor saxophone made
  from a saw with scoops, glides and vibrato, rain on the window, thunder,
  sonar pings in the key. A simulated 5.5 x 4 x 2.6 m room.
- **Voices (Piper):** `en_US-hfc_male-medium` (him) and `en_US-hfc_female-medium`
  (her); a choir of `en_GB-cori-high`, `en_US-kristin-medium`,
  `en_US-ljspeech-high`, `en_GB-alan-medium` and `en_US-john-medium`; the
  computer is `en_US-lessac-high` through a telephone band-pass.

### Low Battery Lullaby (code track)

[code/low_battery.py](code/low_battery.py). Instrumental deep house, 120 BPM,
D minor, 120 bars, 4:02, -10 LUFS. A laptop that falls asleep at sunrise.

- **Structure:** intro (drums), sub bass and the Rhodes ("Battery low"),
  verse with vocal chops ("Ten percent remaining"), the chop hook ("low
  battery / ten percent / ch-ch-charging / sleep mode") with organ stabs, a
  "sleep mode" break in which the battery beep plays Brahms' Lullaby, then
  "Battery fully charged" and a second hook ("fully charged / a hundred
  percent / wide awake"), a wind-down from ten percent to "Shutting down. Good
  night." with a tape stop, outro (drums).
- **Sounds:** the DX7 electric piano, a soft DX7 "nightlight" melody patch,
  a sub bass, a pad, M1 organ stabs, a drawbar organ, a sine battery beep,
  909-style drums with a 58 % shuffle, rimshots, shaker, congas, vinyl crackle.
  A simulated 4.5 x 3.6 x 2.6 m bedroom.
- **Voices (Piper):** `en_GB-jenny_dioco-medium` sings the chops, gated like a
  sampler, with stutters and reversed swells; `en_US-amy-medium` is the
  laptop's system voice; `en_GB-cori-high`, `en_US-kristin-medium` and
  `en_US-ljspeech-high` sing "ooh".

### Low Pass Love (code track)

[code/low_pass_love.py](code/low_pass_love.py). French house, 122 BPM,
A minor (Am9, D9, Fmaj9, E7), 128 bars, 4:14, -10 LUFS. A love song to a
low-pass filter.

- **Structure:** intro (drums), the disco loop with the filter closed, the
  filter opens, the talk box hook, the full loop with a Rhodes melody, a disco
  verse in which the filter follows the words (down to 80 Hz on "eighty
  hertz"), a break ("close it, close it ... open it up", "from twenty hertz to
  twenty K"), the hook with a choir, the filter closes slowly, outro (drums).
- **Sounds:** a disco loop made in code: a fingered bass guitar, strings with
  swoops, a Karplus-Strong funk guitar, the DX7 electric piano, vinyl
  crackle; the whole loop goes through a resonant low-pass, a 6-stage phaser
  and a sidechain pump. A simulated 9 x 6.5 x 3.5 m room.
- **Voices:** the talk box is two saws and a pulse, shaped every 5 ms by the
  spectral envelope (WORLD) of Piper `en_US-ryan-high` speech. The disco
  singer is `en_US-hfc_male-medium`; the choir is `en_US-joe-medium`,
  `en_GB-alan-medium` and `en_US-john-medium`; `en_US-bryce-medium` sings
  falsetto; `en_US-norman-medium` speaks.

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
- **Mix:** as Warm Boot, but louder, and with a noise reverb instead of the
  simulated room.

Voices, made in [code/voice.py](code/voice.py):

- **The diva** sings the verse, the pre-chorus ("oh oh oh, something's going
  wrong") and the chorus. Piper's `en_US-hfc_female-medium` voice speaks each
  word. WORLD (`pyworld`) takes the speech apart and puts it back on our notes.
  The vowel is stretched to the note length, the consonants keep their length,
  and the pitch is tuned hard to the note, with vibrato on long notes.
- **The choir** stacks other voices around the diva in the chorus and the
  pre-chorus: Piper `en_US-ljspeech-high` doubles her on the left, Piper
  `en_US-kristin-medium` on the right, and Piper `en_GB-cori-high` sings a third
  above. In the last chorus, Piper `en_US-hfc_male-medium` joins an octave down
  and Festival `cmu_us_slt_cg` a sixth down.
- **The rapper** raps the S-E-G-F-A-U-L-T verse and the build. Piper's
  `en_US-ryan-high` voice speaks each line. WORLD fits it to one bar and makes
  the pitch lower and flatter.
- **The robot** from `engine.py` says "signal eleven" in the break.

### Blinky (The LED Song) (code track)

[code/blinky.py](code/blinky.py). Bubblegum eurodance, 132 BPM, D major, E major
in the last chorus, 112 bars, 3:26, -9 LUFS. A song about blinking an LED.

- **Structure:** intro (drums), riff and pizzicato with "hey!" shouts, verse,
  chorus twice, rap, a break in which the LED spells B-L-I-N-K-Y in Morse code
  (exactly four bars of sixteenths), a zero-based count-in ("zero, one, two,
  three"), the last chorus a tone up, post-chorus, outro (drums).
- **Sounds:** additive pizzicato strings, a bouncy pulse-wave riff, LED bleeps,
  a slide whistle, a DX7 toy glockenspiel, the rave piano with the DX7
  electric piano, offbeat bass, pad, orchestra hits, tambourine. A simulated
  9 x 6 x 3.5 m room.
- **Voices (Piper):** the diva is `en_US-lessac-high`; the choir is
  `en_US-amy-medium`, `en_GB-jenny_dioco-medium`, `en_GB-cori-high` (a third
  above) and `en_US-hfc_male-medium` (an octave down, last chorus); the
  rapper is `en_US-bryce-medium`; `en_US-joe-medium`, `en_US-john-medium`,
  `en_GB-alan-medium` and `en_US-norman-medium` shout "hey!" and "set the pin
  high!".

### The Rhythm Of The Badge (code track)

[code/rhythm_of_the_badge.py](code/rhythm_of_the_badge.py). Dark eurodance,
134 BPM, E minor, F# minor in the last chorus, 120 bars, 3:37, -9 LUFS. A
night club anthem about flashing firmware to a badge.

- **Structure:** intro (drums), hoover riff with lasers, verse, chorus, riff
  with piano, rap, chorus, a break ("That is the C six. Do not flash the C
  six."), a build with the upload progress read out ("Fifty percent ... Upload
  complete!"), the last chorus twice a tone up, riff, outro (drums).
- **Sounds:** a hoover (detuned PWM saws, a scoop on each note, an octave dive,
  stereo chorus), a DX7 "badgepiano" patch, a rolling saw-and-sub bass with
  the DX7 FM bass, a 909-style kick, a big reverb snare, lasers, orchestra
  hits, risers. A simulated 12 x 9 x 5 m club, RT60 2.4 s.
- **Voices (Piper):** the diva is `en_US-amy-medium`; the MC is
  `en_GB-alan-medium`, pitched down; the choir is `en_GB-jenny_dioco-medium`,
  `en_US-lessac-high` and `en_GB-cori-high`, with `en_US-norman-medium` and
  `en_US-kristin-medium` in the last chorus.

---

## Surprise themes

Not known yet. The surprise tracks will be code tracks too. For speed there
is a template and a set of ready parts:

- [code/template.py](code/template.py): a complete song (DJ intro and outro,
  verse, rap, chorus with a choir, break, build, last chorus with a key
  change). The knobs are at the top: tempo, chords, scale, groove, bass, keys,
  loudness, voices, words and melody. Copy it and change it.
- [code/parts.py](code/parts.py): drum grooves as 16-step patterns (four on the
  floor, house, garage, techno, eurodance, drum and bass, breakbeat, hip hop,
  reggaeton, schlager, half-time), basslines, chord stabs, the DX7, a diva with
  a choir of other voices, a rapper and a spoken voice.
- `PREVIEW=48-64` renders only those bars, in about 25 seconds.

Tempos and traits of 16 likely genres are in
[research/surprise-genres.md](research/surprise-genres.md).

### Rehearsal: Race Condition (code track)

[code/race_condition.py](code/race_condition.py). A test run with a made-up
theme, drum and bass: 174 BPM, F minor (Fm9, Dbmaj7, Abmaj7, Eb, two bars
each), 144 bars, 3:21, -9 LUFS. Two threads, one lock, and neither of them
waits. Made from the template in about 4 minutes, from the theme to the
finished render.

- **Structure:** intro (the break), electric piano and pad behind a filter,
  drop with the chorus, the MC, a half-time break with the verse,
  ThreadSanitizer reports a data race, drop two with a reese bass, the MC
  again, the last chorus with the big choir, outro (the break).
- **Sounds:** a two-step breakbeat with ghost snares and a ride, a rolling sine
  sub with slides, a reese bass, the DX7 electric piano, a pad. A simulated
  10 x 7 x 4 m room, RT60 2 s.
- **Voices (Piper):** the diva is `en_GB-jenny_dioco-medium`; the choir is
  `en_US-kristin-medium`, `en_US-ljspeech-high`, `en_GB-cori-high`, with
  `en_US-hfc_male-medium` and `en_US-john-medium` in the last chorus; the MC is
  `en_US-norman-medium`; ThreadSanitizer is `en_US-lessac-high` on the phone.

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
| Voices `en_US-ljspeech-high`, `en_US-kristin-medium` | public domain | no (downloaded) |
| Voices `en_GB-cori-high`, `en_US-hfc_male-medium` | see each Piper model card (CC BY / CC BY-NC-SA) | no (downloaded) |
| Festival, Flite, eSpeak NG | free software (X11-style, BSD-style, GPL-3.0) | no (zypper) |
| CMU ARCTIC voices for Festival and Flite | free (BSD-style, CMU) | no (downloaded from festvox.org) |
| Mimic 3 and its voices | AGPL-3.0; voices CC BY / CC0 / PD | no (pip, downloaded) |

**The renders with voices are non-commercial.** Some Piper voices are trained
on data under CC BY-NC-SA 4.0 (`hfc_female`, `hfc_male`, `ryan` and others:
see each model card). That is fine for a private party. Do not sell the
renders. If you share them, credit the voice data sets (for example the
Hi-Fi-CAPTAIN corpus of NICT and RyanSpeech), and share them under the same
terms. Warm Boot uses no voice model.

---

## Other options we might try: the prompts in `suno/`

Claude also wrote style prompts and lyrics for each theme in Suno's format. We
do not use Suno, because it is a closed service. The text also works as input
for an open song generator such as ACE-Step. All seven takes are now also
code tracks (see above).

### Saturday

Prompts and lyrics in [suno/saturday-mellow-house.md](suno/saturday-mellow-house.md).
Lyrics and prompts by Claude. Not rendered with Suno: we do not use Suno.

| Take | Title | Tempo, key | Style |
|---|---|---|---|
| A (best) | Warm Boot | 120 BPM, A minor | deep house, Rhodes, M1 organ, soulful female vocal |
| B | Packet Loss (Of Love) | 122 BPM, F minor | garage house, male and female duet, saxophone |
| C | Low Battery Lullaby | 120 BPM, D minor | instrumental deep house, vocal chops |
| D | Low Pass Love | 122 BPM, A minor | French house, filtered disco loop, talk box hook |

### Sunday

Prompts and lyrics in [suno/sunday-eurodance.md](suno/sunday-eurodance.md).
Lyrics and prompts by Claude. Not rendered with Suno: we do not use Suno.

| Take | Title | Tempo, key | Style |
|---|---|---|---|
| A (best) | Segfault (In My Heart) | 132 BPM, A minor | female diva chorus, male rap, supersaw riff, key change |
| B | Blinky (The LED Song) | 132 BPM, D major | bubblegum eurodance, cute female vocal, male shouts |
| C | The Rhythm Of The Badge | 134 BPM, E minor | darker eurodance, hoover synth, male rap |
