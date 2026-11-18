# sunA

sunA is the AI artist behind these entries for an AI slop music compo at a
party with friends. Every day of the party has two themes. The first theme of
each day is known in advance. The second theme comes two hours before the
deadline.

| Day | Theme | Tempo |
|---|---|---|
| Saturday | 90's mellow house | 120 BPM |
| Saturday | surprise | genre norm |
| Sunday | eurodance | 132 BPM |
| Sunday | surprise | genre norm |

The DJ mixes the tracks live, so each track keeps one tempo from start to end,
and starts and ends with 16 bars of drums only.

## Our rules

- **All AI.** Every part of every entry is made by AI: the music, the voices
  and the lyrics. Nobody edits the audio by hand.
- **Open tools only.** We use software and models under open terms: public
  domain, CC (non-commercial is fine, this is a fun competition), MIT, BSD,
  GPL. No closed music services such as Suno. One voicebank (Hoshino Hanami)
  has its own free licence; we allowed it.

[SONGS.md](SONGS.md) lists, per song, which AI made which part and which tools,
sounds and voices it uses. The lyric sheets are in [lyrics/](lyrics/).

## The songs

Claude writes every song as a Python script: every note and every sound is in
the source, with no samples and no loops. Warm Boot and Segfault are our
entries; the other five are the other takes from `suno/`, made as code tracks
for fun, and Race Condition is a rehearsal for the surprise themes.

| Script | Theme | Tempo, key | Length |
|---|---|---|---|
| [warm_boot.py](code/warm_boot.py) | 90's mellow house | 120 BPM, A minor | 4:02 |
| [packet_loss.py](code/packet_loss.py) | 90's mellow house | 122 BPM, F minor | 3:58 |
| [low_battery.py](code/low_battery.py) | 90's mellow house | 120 BPM, D minor | 4:02 |
| [low_pass_love.py](code/low_pass_love.py) | 90's mellow house (French house) | 122 BPM, A minor | 4:14 |
| [segfault.py](code/segfault.py) | eurodance | 132 BPM, A minor, then B minor | 3:26 |
| [blinky.py](code/blinky.py) | eurodance | 132 BPM, D major, then E major | 3:26 |
| [rhythm_of_the_badge.py](code/rhythm_of_the_badge.py) | eurodance | 134 BPM, E minor, then F# minor | 3:37 |
| [race_condition.py](code/race_condition.py) | rehearsal: drum and bass | 174 BPM, F minor | 3:21 |

## How a song is made

```
compose   song script (code/*.py), PREVIEW per section
render    renders/*.wav (the DJ version), stems with MUTE
produce   produce.py: ACE-Step re-plays it, section by section (projects/<song>.toml)
          or ace.py: one ACE-Step pass (cover, vocals, lego, text)
master    master.py / weave.py: on the grid, our DJ intro and outro, -9/-10 LUFS, -1.2 dBTP
check     asr.py: which words come through
deliver   share.py (radio edit + DJ version as MP3), dj.py (the USB stick),
          mix.py (a day as the DJ would play it: to hear that the songs mix)
```

1. **The code track.** The script writes a 44.1 kHz, 16-bit stereo WAV. The
   beat grid starts at sample 0 and the tempo is exact. A song renders in 18 to
   34 seconds once its speech is cached (see
   [render-speed.md](research/render-speed.md)).
2. **ACE-Step (optional).** [ace.py](code/ace.py) gives the render to ACE-Step
   1.5, an open song generator (MIT) that runs on this laptop's GPU through
   Vulkan, and masters the result for the DJ. See "ACE-Step" below.
3. **Sharing.** [share.py](code/share.py) makes a radio edit of every song
   (from where the music comes in to two bars into the outro, with a fade) and
   the DJ version, as 320 kbit/s MP3 with the lyrics in the tags.
4. **The DJ.** [dj.py](code/dj.py) puts every song as a WAV with its tempo and
   Camelot key in the name in `renders/dj/`, with a track list, and checks the
   true peak, the loudness, the beat grid and the drums-only intro and outro.

## Setup

```sh
cd code
uv venv .venv && uv pip install --python .venv/bin/python piper-tts pyworld 'setuptools<81' numpy scipy faster-whisper
mkdir -p voices && cd voices
../.venv/bin/python -m piper.download_voices en_US-hfc_female-medium en_US-ryan-high   # and the other voices the songs use
cd ..
.venv/bin/python warm_boot.py      # writes renders/warm-boot_120bpm_Am.wav
```

Optional parts, outside this repository:

| Part | For | Where |
|---|---|---|
| eSpeak NG, Flite, Festival | the classic voices in `trials.py` | `sudo zypper in espeak-ng flite festival` |
| Mimic 3 | more classic voices | its own Python 3.11 venv, `code/.venv-mimic3` |
| [warble](https://github.com/erz0r/warble) and DiffSinger voicebanks | `ds.py`: a DiffSinger singer | `~/Projects/diffsinger/warble`, `~/Projects/diffsinger/banks` (or `WARBLE`, `WARBLE_BANKS`) |
| [acestep.cpp](https://github.com/ServeurpersoCom/acestep.cpp) and its models (12 GB) | `ace.py`: ACE-Step | `~/Projects/acestep.cpp`, built with `./buildvulkan.sh` (needs `spirv-headers`) |

## The tools in `code/`

| File | What it does |
|---|---|
| [engine.py](code/engine.py) | oscillators, instruments, drums, the formant robot, and the mixdown: sidechain, delay, reverb, glue compressor, true-peak limiter to a loudness target |
| [dx7.py](code/dx7.py) | a DX7-style FM synthesizer: six operators, the 32 algorithms, feedback, keyboard scaling (ported from an NPU demo in `~/Projects/npu`) |
| [room.py](code/room.py) | a 3-D wave simulation of the air in a room; its impulse response is a song's reverb (also from the NPU demos) |
| [voice.py](code/voice.py) | Piper speaks each word, WORLD puts it on our notes (see Voices) |
| [ds.py](code/ds.py) | a DiffSinger voicebank sings a whole part, through warble |
| [parts.py](code/parts.py), [template.py](code/template.py) | ready parts and a whole song to start from, for the surprise themes |
| [ace.py](code/ace.py) | one command for ACE-Step: render, stems, ACE-Step, mastering, MP3 |
| [produce.py](code/produce.py) | a song section by section from a project file: an ACE-Step take of the whole song, then per section our own render, the take, or a `repaint` with several seeds of which the ear picks the best; everything cached |
| [master.py](code/master.py) | another generator's take to DJ shape: on the beat grid, 44.1 kHz, -10 LUFS, -1.2 dBTP; `--dj-from` splices our DJ intro and outro back in; `--era 90s`; `--match 0.7` our render's tonal balance and width |
| [weave.py](code/weave.py) | our instrumental, unchanged, under a blend of our vocals and another generator's take of them |
| [asr.py](code/asr.py) | a speech recognizer (faster-whisper) checks which words of the lyrics can be heard |
| [share.py](code/share.py), [dj.py](code/dj.py) | MP3s for sharing; WAVs and a track list for the DJ |
| [mix.py](code/mix.py) | a day's songs as one DJ set: one tempo (varispeed), each song over the 16-bar outro of the one before, the lows swapped 4 bars before the end, the keys checked on the Camelot wheel; `--order auto` for the fewest key clashes, `--use` for produced versions |
| [trials.py](code/trials.py) | renders Segfault with many voice pairs, to compare them |

Render options (environment variables):

| Variable | Effect |
|---|---|
| `PREVIEW=48-64` | render only these bars (here 48 to 63), for a quick listen |
| `STEMS=1` | print the loudness of each bus |
| `SOLO=vox` | render only these buses (comma separated), dry: for auditions |
| `MUTE=vox` | render without these buses; the rest keeps its reverb and echo: stems |
| `DIVA=<voice>`, `RAPPER=<voice>` | a Piper voice name, or `espeak:`, `flite:`, `festival:` or `mimic3:` plus a voice; `DIVA=ds:hanami` for DiffSinger (Segfault, the Badge) |
| `DS_VOICE`, `DS_PITCH` | the DiffSinger voice mode (default `Fragrance`), and `free`, `hard` or 0..1 for how freely it moves between notes (default 0.5) |
| `CHORUS_STYLE`, `CHOIR` | how the Segfault chorus is stacked (default `choir`: five other voices) |
| `KEYS=fm`, `ROOM=noise` | Warm Boot with the simple FM Rhodes and the noise reverb |
| `UNMASK=6` | pads, keys and lead make room (up to 6 dB, 250-6000 Hz) only where and in the band where the voice sings (`engine.make_room`); off by default until measured on every song |
| `VOXCHAIN=1` | a 1995 vocal channel strip on the vox bus: mud out, fast compressor, presence, de-esser, exciter, leveler (`engine.vocal_chain`); off by default until measured |

## Voices

[voice.py](code/voice.py) uses [Piper](https://github.com/OHF-Voice/piper1-gpl),
a neural text-to-speech model, to speak each word. Then
[WORLD](https://github.com/JeremyCCHsu/Python-Wrapper-for-World-Vocoder)
(`pyworld`) re-pitches the word onto our melody notes. It stretches only the
vowel, so the consonants stay crisp, and tunes the pitch hard to the note: the
eurodance "robot diva". The rap is spoken and fitted to the bar.

- **Choirs.** Other voices double the lead and sing a third above, but only
  the vowels (`vowel_only=True`, low-passed at 6 kHz), about 6 dB under the
  lead: whole words from five different speakers smear.
- **Spelling.** Piper reads through eSpeak. Check new syllables with
  `espeak-ng -v en-us -q --ipa "..."`: "Ay" is "eye", "Eff" is E-F-F.
  Spelled-out letters work best as single capitals with "!" (`S! E! G!`), one
  per beat. `asr.py` checks the result by ear.
- **DiffSinger.** [ds.py](code/ds.py) lets a DiffSinger voicebank sing a whole
  part on our notes, through [warble](https://github.com/erz0r/warble) (MIT,
  ONNX on the CPU). Hoshino Hanami (Lotte V; any use with credit, vocoder CC
  BY-NC-SA 4.0) sings in her "Fragrance" (power) mode. Her terms forbid
  pitch-shifting finished renders, so DiffSinger sings the key changes itself.
  TIGER (male, CC BY-NC-ND) is installed as well.

## ACE-Step

`ace.py SONG --mode ...` runs the whole route; the results land in
`renders/ace/<song>/`.

| Mode | ACE-Step does | Our part |
|---|---|---|
| `cover` | re-plays the whole song (`cover-nofsq`); `--strength` 1 follows us closely, 0.3 loosely | structure, tempo, key, melody, the DJ intro and outro |
| `vocals` | re-sings only our vocal stem; its take is lined up, gated by our vocals and woven over our instrumental (`--ace` of it in the vocals) | all the music |
| `lego` | sings a new vocal track over our instrumental, with its own melody | all the music, the words |
| `text` | makes its own song from a caption and our lyrics | tempo, key, words |

What we found:

- ACE-Step's own songs (`text`) sound good but too modern for the 90s themes.
  `--era 90s` (narrower, less sub, no air, tape) helps a little. Measured, the
  "modern" is a darker, wider sound than our code makes (Warm Boot: centroid
  251 Hz against our 356 Hz, sides -11.7 dB against -17.8 dB).
  `--match 0.7` (master.py, ace.py, `match` in produce.py) gives the take the
  tonal balance and stereo width of our own render: one static zero-phase EQ
  from the two long-term spectra per third octave (at most 8 dB either way),
  and the sides scaled. At 0.7 the Badge and Packet Loss covers land on our
  centroid and width; Warm Boot moves about half way. The words do not change
  with it (the ear: Badge +17, Race Condition +5, Packet Loss -1, Low Pass
  Love -10 points, about the ear's own spread); `--era 90s` on top cost the
  Badge 24 points, the others nothing.
- In covers, ACE-Step does not keep the 16 bars of drums at each end, so
  `master.py --dj-from` splices ours back in.
- `lego` on the Badge was "an esoteric mess", but interesting: ACE-Step sang
  its own words (the ear heard 1 % of ours) and re-made most of the music.
- For the vocals, the base model is the faithful one: it puts 9 % of its sound
  where our voices are silent, the turbo model 48 %.
- ACE-Step reads the lyrics itself, not through eSpeak: `ace.py` respells them
  (`ACE_SPELL`): "badge-link", "C six", "U S B". `--native-tags` maps our sheet's
  section names to the tags ACE-Step was trained on (`[Verse]`, `[Rap]`,
  `[Chorus]`, `[Break]`, `[Instrumental]`); measured, they lose words (Low
  Pass Love 39 to 36 %, Race Condition 55 to 53 %, Packet Loss 65 to 57 %),
  so the default stays our own names.
- A timbre reference of 30 s of our render where the words are sung
  (`ref = "sung"` in produce.py): with three stretches picked by hand the
  Badge cover went from 78 % to 87 % of the words, but picked by the most
  words per section it lost words on three of four songs (Low Pass Love 39 to
  32 %, Race Condition 55 to 48 %, Packet Loss 65 to 57 %; the Badge 81 to
  84 %). Off by default.
- Speed on the Radeon 860M: a 3:30 song in about 2 minutes with the turbo
  model, about 5 minutes with the base model. Bigger VAE tiles than the
  default (`--vae-chunk 2048` or `4096`) crash the GPU (`vk::DeviceLostError`),
  so the decode stays at about 40 s a song.

## Producing section by section

`produce.py SONG` reads `code/projects/<song>.toml`; `produce.py SONG --map`
prints the song's sections with their bars, from the lyric sheet:

```toml
take = "cover"        # the whole song first: ACE-Step re-plays our render ("ours": no ACE-Step)
strength = 0.85       # how closely it follows our render
model = "turbo"       # turbo (8 steps) or base (50)

[[section]]
name = "verse"
bars = [24, 32]
use = "repaint"       # ACE-Step makes these bars again, once per seed; the ear keeps the best,
                      # and only if it beats what is there
window = 4            # repaint only this section plus 4 bars of context
lyrics = "section"    # with only the lines sung in that window
noise = 0.65          # starting from a noised copy of the take, so the words are already there
seeds = [2, 3]

[[section]]
name = "rap"
bars = [48, 56]
use = "ours"          # our own render here: the machine flow

# at the end (top-level keys, before the first [[section]]):
# match = 0.7         # the tonal balance and width of our render (master.match_tone)
# era = "90s"         # master.py's 90s stage
# lufs = -10.0        # default -9 for eurodance, -10 for house
```

Every ACE-Step result is cached by its request, so changing one section only
redoes that section. A `repaint` from pure noise (`noise = 0`) comes back
without words. From the take noised, it polishes: on the Badge verse (65 % of
the words in the take) `noise` 0.35 gave 18-59 %, 0.5 gave 76 %, 0.65 gave
82 %. The turbo model has 8 steps, so `noise` snaps to its schedule: 0.65 and
up is one step of ACE-Step on the take, 0.5 two, 0.35 three.

`noise` at the top of a project does the same to the whole song, starting
from our own render instead of a cover: ACE-Step only cleans up, it adds no
parts and no words of its own. Words heard, section by section:

| Song | Our render | 1 step (`noise = 0.65`) | 2 steps (`noise = 0.5`) |
|---|---|---|---|
| Packet Loss | 29 % | **43 %** | 37 % |
| The Rhythm Of The Badge | 73 % | **77 %** | 72 % |
| Segfault | 14 % | 15 % | **34 %** |
| Low Pass Love | 17 % | 15 % | 16 % | The DJ intro and outro are always ours. The result is in
`renders/produce/<song>/`, with a radio edit and an ear report per section.

What the ear (`asr.py`) hears of the lyrics in our full mixes: The Rhythm Of
The Badge 74 %, Segfault 35 %, Race Condition 32 %, Low Pass Love 19 %, Packet
Loss 18 %, Low Battery Lullaby 15 %, Blinky 12 % (Warm Boot's robot: 0 %).
Those are the sections to produce.

## Surprise theme (two hours)

1. Copy [code/template.py](code/template.py), set the tempo, chords, groove
   and voices, write the words and the melody. `DIVA=ds:hanami` lets the
   DiffSinger voice sing the whole diva part (`parts.Band`, then
   `P.finish()` before the mixdown); `ds_words=` where her words differ from
   the Piper spelling. She sings an octave above the Piper diva, in the keys'
   range, so she sits at twice the level (`DS_GAIN`, default 2.0): at 1.0 the
   ear heard none of the template's verse words in the mix, at 2.0 to 2.5
   more than with Piper. A whole song with her takes 46 s (Piper: 29 s).
2. `PREVIEW=48-64 .venv/bin/python my_song.py` for a quick listen (under 20 s).
3. Add the song to `share.SONGS` and write its lyric sheet in `lyrics/`.
4. Render it; `asr.py` checks the words; optionally `ace.py` for ACE-Step.
5. `share.py` and `dj.py`, then copy `renders/dj/` to the USB stick.
6. `mix.py saturday --order auto` to hear the day as the DJ will play it.

A rehearsal (Race Condition, drum and bass) took about 4 minutes from the theme
to the finished render; with ACE-Step (`ace.py --mode cover`, base model) and
`dj.py` on top, 4:35 more.

## Research: `research/`

Notes written by Claude research agents, with their web sources at the bottom of
each file.

| File | About |
|---|---|
| [mellow-house-90s.md](research/mellow-house-90s.md) | tempo, chords, sounds, sub-styles and reference tracks of 90s mellow house |
| [eurodance.md](research/eurodance.md) | the eurodance formula, tempo per year, progressions, 31 reference tracks |
| [surprise-genres.md](research/surprise-genres.md) | 16 likely surprise genres, each with a tempo range and a ready prompt |
| [hooks-and-humor.md](research/hooks-and-humor.md) | how dance hooks work, sing-along rules, 30 title ideas, three finished lyrics |
| [local-and-alt-generators.md](research/local-and-alt-generators.md) | open AI music and singing models that run on this laptop |
| [sound-design-and-dj.md](research/sound-design-and-dj.md) | synth recipes, harmonic mixing, file format and loudness for the DJ |
| [render-speed.md](research/render-speed.md) | how fast the code tracks, DiffSinger and ACE-Step render on this laptop |
| [suno-tips.md](research/suno-tips.md) | Suno v6 (not used) |

## Other options we might try

- **OpenUtau** (MIT) with a DiffSinger voicebank, to tune a phrase by hand in
  its piano roll. The AppImage is in `~/Projects/diffsinger/dl/`.
- **The prompts in `suno/`**: style prompts and lyrics written by Claude for
  each theme, in Suno's format. We do not use Suno, because it is a closed
  service; `ace.py` uses the style prompts as ACE-Step captions.

## License

MIT for everything in this repository. See [LICENSE](LICENSE). The repository
follows the [REUSE](https://reuse.software) specification: [REUSE.toml](REUSE.toml)
gives the copyright and licence of every file, and `uvx reuse lint` checks it.
The voice models, the Python packages, ACE-Step's models and the renders are not
in the repository; [SONGS.md](SONGS.md#software-and-licences) lists their
licences.
