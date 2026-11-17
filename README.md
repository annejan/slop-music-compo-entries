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
  GPL. No closed music services such as Suno.

[SONGS.md](SONGS.md) lists, per song, which AI made which part and which tools,
sounds and voices it uses.

## The tracks: `code/`

Eight songs written by Claude as Python code. Every note and every sound is in
the source: there are no samples and no loops. The synthesis is numpy and
scipy. Warm Boot sings with a formant robot; the other songs have AI singers
and rappers (see Voices). Warm Boot and Segfault are our entries; the other
five are the other takes from `suno/`, made as code tracks for fun, and Race
Condition is a rehearsal for the surprise themes.

| Script | Theme | Tempo, key | Length |
|---|---|---|---|
| [code/warm_boot.py](code/warm_boot.py) | 90's mellow house | 120 BPM, A minor | 4:02 |
| [code/packet_loss.py](code/packet_loss.py) | 90's mellow house | 122 BPM, F minor | 3:58 |
| [code/low_battery.py](code/low_battery.py) | 90's mellow house | 120 BPM, D minor | 4:02 |
| [code/low_pass_love.py](code/low_pass_love.py) | 90's mellow house (French house) | 122 BPM, A minor | 4:14 |
| [code/segfault.py](code/segfault.py) | eurodance | 132 BPM, A minor, then B minor | 3:26 |
| [code/blinky.py](code/blinky.py) | eurodance | 132 BPM, D major, then E major | 3:26 |
| [code/rhythm_of_the_badge.py](code/rhythm_of_the_badge.py) | eurodance | 134 BPM, E minor, then F# minor | 3:37 |
| [code/race_condition.py](code/race_condition.py) | rehearsal: drum and bass | 174 BPM, F minor | 3:21 |

For a new song, start from [code/template.py](code/template.py): a complete
song with the knobs at the top, built from the ready parts in
[code/parts.py](code/parts.py) (drum grooves for many genres, basslines,
chords, a diva with a choir, a rapper). See SONGS.md, "Surprise themes".

[code/engine.py](code/engine.py) holds the shared parts: oscillators,
instruments, drums, the robot voice, and the mixdown (sidechain, delay, reverb,
glue compressor, true-peak limiter). It comes from the soundtrack of the QtPass
2.0 film.

Two more parts come from the NPU demos in `~/Projects/npu` (MIT, same author),
ported from the NPU to numpy so that the tracks render on any computer:

- [code/dx7.py](code/dx7.py): a DX7-style FM synthesizer: six operators, the
  32 algorithms of the DX7, operator feedback. Warm Boot's Rhodes is its
  electric piano patch.
- [code/room.py](code/room.py): a 3-D wave simulation (FDTD) of the air in a
  7 x 5 x 3 m room. It records the room's stereo impulse response, and Warm
  Boot's reverb uses it. The simulation takes 6 seconds and is cached.

### Voices

[code/voice.py](code/voice.py) uses [Piper](https://github.com/OHF-Voice/piper1-gpl),
a neural text-to-speech model that runs on the CPU, to speak each word. Then
[WORLD](https://github.com/JeremyCCHsu/Python-Wrapper-for-World-Vocoder)
(`pyworld`) re-pitches the word onto our melody notes. It stretches only the
vowel, so the consonants stay crisp. In the chorus, a choir of other voices
doubles the diva left and right and sings a third above; in the last chorus a
male voice an octave down and a fifth voice join. The choir sings only the
vowels (`voice.sing(..., vowel_only=True)`), low-passed at 6 kHz, in a
straighter tone, about 6 dB under the lead: every speaker has their own
consonant lengths, so whole words from five voices smear. The rap is spoken and fitted to the bar. The
formant robot from `engine.py` only says "signal eleven" in the break.

The default diva is Piper's `en_US-hfc_female-medium` and the default rapper is
`en_US-ryan-high`. Both are trained on data under CC BY-NC-SA 4.0. Set `DIVA`
and `RAPPER` to try other voices.

### Render

Warm Boot needs Python 3 with numpy and scipy. Segfault also needs the voices.
Set them up once:

```sh
cd code
uv venv .venv && uv pip install --python .venv/bin/python piper-tts pyworld 'setuptools<81' numpy scipy
mkdir -p voices && cd voices
../.venv/bin/python -m piper.download_voices en_US-hfc_female-medium en_US-ryan-high
cd ..
```

Then render:

```sh
.venv/bin/python warm_boot.py      # writes renders/warm-boot_120bpm_Am.wav
.venv/bin/python segfault.py       # writes renders/segfault_132bpm_Am.wav
```

Every song script works the same way. Warm Boot renders in about 30 seconds.
Segfault takes about 90 seconds the first time, because Piper speaks every
word; the speech is cached in `.cache/`. The five other songs take 3 to 5
minutes each and need about 3 GB of memory.

To share the songs in a chat app such as Signal:

```sh
.venv/bin/python share.py    # writes renders/share/NN Title (BPM, key).mp3, 320 kbit/s, about 9 MB each
```

The lyric sheets are in [lyrics/](lyrics/): what each voice sings or says, with
the time of each section. They are written from the code, so they show the
words as rendered. `share.py` copies them next to the MP3s and puts them in
the MP3 tags.

| Variable | Effect |
|---|---|
| `STEMS=1` | print the loudness of each bus |
| `CHORUS_STYLE=octave`, `doubles`, `harmony`, `choir` | how the Segfault chorus is stacked (default `choir`: other voices) |
| `CHOIR=v1,v2,v3,v4,v5` | the choir: left double, right double, third above; in the last chorus also an octave down and a sixth down |
| `DIVA=<voice>`, `RAPPER=<voice>` | the voices of Segfault: a Piper voice name, or `espeak:`, `flite:`, `festival:` or `mimic3:` plus a voice |
| `SOLO=vox` | render only these buses (comma separated), for auditions |
| `PREVIEW=48-64` | render only these bars (here 48 to 63), for a quick listen |
| `KEYS=fm`, `ROOM=noise` | Warm Boot with the simple FM Rhodes and the noise reverb from `engine.py` (default: `dx7`, `sim`) |

`trials.py` renders Segfault with many voice pairs and cuts bars 24-58 (verse,
rap, pre-chorus, chorus) into `renders/voices/`; with `--solo` it renders the
voices a cappella into `renders/voices-solo/`, so they are easy to tell apart.
The classic engines need `sudo zypper in espeak-ng flite festival`; Mimic 3
lives in its own Python 3.11 venv (`.venv-mimic3`, `mycroft-mimic3-tts`).

The output is a 44.1 kHz, 16-bit stereo WAV. The beat grid starts at sample 0
and the tempo is exact, so a DJ can sync it without beat analysis. The renders
are not in the repository. Run the scripts to make them.

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
| [suno-tips.md](research/suno-tips.md) | Suno v6 (not used; see below) |

## Other options we might try

- **ACE-Step 1.5** (MIT, open weights): an open song generator with lyrics and
  vocals that runs on this laptop through Vulkan. See
  [local-and-alt-generators.md](research/local-and-alt-generators.md).
- **OpenUtau with a DiffSinger voice**: a real singing voice on our own melody.
- **The prompts in `suno/`**: style prompts and lyrics written by Claude for
  each theme, in Suno's format. We do not use Suno, because it is a closed
  service. Most of the text also works as input for ACE-Step.
  - [suno/saturday-mellow-house.md](suno/saturday-mellow-house.md): "Warm
    Boot", "Packet Loss (Of Love)", "Low Battery Lullaby", "Low Pass Love".
  - [suno/sunday-eurodance.md](suno/sunday-eurodance.md): "Segfault (In My
    Heart)", "Blinky (The LED Song)", "The Rhythm Of The Badge".
  - [suno/surprise-theme-recipe.md](suno/surprise-theme-recipe.md): a two-hour
    plan and a tempo table for the surprise themes.

## License

MIT for everything in this repository. See [LICENSE](LICENSE). The repository
follows the [REUSE](https://reuse.software) specification: [REUSE.toml](REUSE.toml)
gives the copyright and licence of every file, and `uvx reuse lint` checks it.
The voice models, the Python packages and the renders are not in the
repository; [SONGS.md](SONGS.md#software-and-licences) lists their licences.
