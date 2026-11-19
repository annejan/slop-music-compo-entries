# The compo weekend: the playbook

Saturday 21 November: 90's mellow house. Sunday 22 November: eurodance. Each day also has a surprise genre,
announced two hours before the deadline. This page is the short version of what to do and which command does it.
The background is in [README.md](README.md), [research/night-tests.md](research/night-tests.md) and
[research/toolkit-2026-11-19.md](research/toolkit-2026-11-19.md). Every command and name here was checked against
the code on 19 November.

All commands run in `code/` with the project's Python: `cd code`, then `.venv/bin/python <script> ...`.

## The rules, in one breath

- Everything is AI-made: words, music, voices. No hand edits in a DAW, no human-made samples or loops, no
  voice of a real person (no cloning of a friend either).
- The DJ format: a fixed tempo, the beat grid at sample 0, 16 bars of drums only at each end. Radio edits too.
- All songs go on the USB stick; the album tag stays "slop-music-compo-entries".
- The work style on the day: short rounds, MP3 snippets to the phone, the user's ears decide. The software ear
  (Whisper) is only a check at the end.

## Before you start (5 minutes)

1. One heavy job at a time. Close what eats memory; `free -g` should show 15 GB or more available. If an NPU
   server from `quick_gag.py --keep` still runs (about 6 GB): `fuser -k 52626/tcp`.
2. A voice smoke test of all four engines in one MP3 (about 30 s). The line must be new each time, because voices
   are cached by their text:

   ```sh
   .venv/bin/python voice.py --audition "Test, one two, $(date +%a%H%M)." --voices piper_ryan,kokoro_hype,qwen_hype,maya_hype
   ```
3. The first draft round of the day is the ACE-Step smoke test: it shows at once whether the GPU works.

## The surprise round, step by step

The target times are from the rehearsals (S.D.I.O. 33 min, Push It To Prod 26, disco 24 for two songs,
Overclocked Heart 30). Two hours are plenty: the time goes to listening, not to the machine.

| When | What | How |
|---|---|---|
| 0:00 | The genre | The user tells it, or draw one. `kits.py --list` shows the 11 kits with tempo and key. |
| 0:02 | Three pitches | Three one-line song ideas; the user picks one. Hardware and badge jokes land with this crowd. |
| 0:05 | The song script | A kit genre: `cp kit_template.py <name>.py`, set `KIT_NAME`, `TITLE`, `DAY` and the spoken lines. Any other genre: `cp template.py <name>.py` and set its knobs (`parts.GROOVES`). `<name>` in lower case with `_`. |
| 0:08 | The diva | A draft round (below): 4 tunes in about 100 s, best first. The user picks one by ear. |
| 0:12 | The keeper | `--keep` the pick (about 35 s), bring it to the song, pin it (below). |
| 0:15 | Spoken parts | The voice cast (below). The first render with Maya voices takes a few minutes more (about 17 s a line, cached after). |
| 0:20 | First full render | `.venv/bin/python <name>.py` (20-45 s). Then append its `share.SONGS` row and write its lyric sheet now (below): `takes.py --bar`, `produce.py` and `share.py` need them. |
| 0:20-1:15 | Rounds | Previews of one section: `PREVIEW=48-64 .venv/bin/python <name>.py` (8-10 s), the MP3 from `renders/scratch/` to the phone. |
| 0:45 | Words frozen | |
| 1:15 | No more changes | |
| 1:30 | Delivery | `share.py --only <name with ->` and `dj.py --only <name with _>`; check the track list. |
| 1:40 | The stick | Copy `renders/dj/` to the USB stick. |

Adding the song for delivery: the script prints a line like `("my-song_128bpm_Bm.wav", "My Song", "Sunday:
eurodance", 128, "Bm", 112),`. Append it at the END of `share.SONGS` in `code/share.py` (the first new song is row 14;
inserting it anywhere else gives the later songs the wrong lyric sheets and track numbers). The lyric sheet is
`../lyrics/14-my_song.txt` (the repository's `lyrics/` folder, not `code/lyrics`), with `[m:ss]` times.

### The diva: a draft round

```sh
.venv/bin/python takes.py <name> --drafts --name chorus --bars 16 --n 4 \
    --caption "1980s Hi-NRG, a powerful dramatic female dance diva, soaring, theatrical, clear words" \
    --lines "first line|second line|third line|fourth line" \
    --bpm 128 --key "B minor" --chords "Bm Em A F#" --lift 3
```

- One ACE-Step LM run makes 4 tunes, one turbo run renders them: about 100 s for all four. ACE-Step's key is a
  lottery (about 1 take in 5 comes back in the asked key), so `fit.py` measures each take against the chords and
  the listen file brings each to the song's tempo and measured key, best first:
  `renders/ace/takes/<name>/chorus drafts, best first.mp3`. The table is `chorus drafts.txt`: one row per draft
  with its JSON file, its fit, "at N st" (the shift) and "one bar earlier" or "later" (the offset).
- `--lift 3`: ACE-Step is asked to sing 3 semitones lower and sings slower; Rubber Band speeds it up to the song's
  tempo and moves it by fit.py's measured shift. The user's verdict on the lifted sound: "really 90s eurotrash,
  love it". Without `--lift` it sings at the song's tempo.
- The ranking only decides the order. The ear decides the take (an approved take once measured poorly).

The pick, in the better voice (the same tune, about 35 s), then to the song and pinned:

```sh
.venv/bin/python takes.py --keep "renders/ace/takes/<name>/<draft>.json"
.venv/bin/python -c 'import takes; w = takes.finish("<keeper>.wav", 104, 128, -1); print(takes.pin(w, "<name>", "chorus"))'
```

- `<keeper>.wav` is the path `--keep` prints. `104` is the tempo it was sung at (the `"bpm"` in the draft's JSON:
  the song's tempo divided by 1.23 with `--lift`, else the song's tempo), `128` the song's tempo, `-1` the shift
  from the draft's row in `chorus drafts.txt`. `<name>` is the script's name with `_`.
- `takes.pin` writes `renders/ace/takes/<name>/pinned/chorus.wav`. A song made from `kit_template.py` plays exactly
  that file and never makes a take itself. If the table said "one bar earlier": `DIVA_OFFSET=-1` for a test,
  then set `DIVA_OFFSET` in the script.
- `--keep ... --guidance 7 --shift 3` is the docs' setting (twice the DiT time; an A/B, not heard yet).
- Other sections in the same voice: `--keep <verse draft>.json --ref <chorus keeper>.wav` (an A/B, not heard yet).

When a take does not fit the band:
- Measure it: `.venv/bin/python fit.py <take>.wav --bpm <sung bpm> --chords "Bm Em A F#"` (the fit, the shift and
  the bar offset). Try the offset first.
- Retune it onto the chords (not heard yet; the Hi-NRG take went from 26 to 55-58 % on the chord tones):

  ```sh
  .venv/bin/python fit.py <take>.wav --bpm 128 --chords "Bm Em A F#" --snap natural   # or: --snap hard (the Cher effect)
  ```
  Add `--offset -1` when the song plays the take a bar early, `--shift N` for a take not yet in the song's key.
  The result is `<take>_snap_natural.wav`.
- A slower harmony under the take, two chords two bars each (`VAMP=1` in Overclocked Heart; not heard yet).
- Do NOT re-harmonize the band to the take: the user preferred the kit's chords.

### Spoken parts: the voice cast

A part asks for its voice by role. In a song from `kit_template.py`: `say(bar, "<excited> Hands up!", "cast:mc")`.
In a song from `template.py`: `P.say(bar, "...", voice="cast:mc")`. Anywhere else:
`V._finish(V.tts("...", "cast:mc"))` (V.tts alone is 22.05 kHz; `_finish` brings it to the song's 44.1 kHz), or
`V.rap(text, seconds, voice="cast:mc")` to fit a line to the bars.

| Role | Default voice | Other CAST names |
|---|---|---|
| `mc` | `maya_hype` | `qwen_hype`, `kokoro_hype`, `piper_ryan` |
| `narrator` | `maya_narrator` | `qwen_trailer`, `piper_lessac` |
| `announcer` | `maya_announcer` | `qwen_announcer` |
| `robot` | `maya_machine` | `qwen_robot`, `kokoro_deep` |
| `whisper` | `maya_whisper` | `qwen_whisper`, `kokoro_whisper` |
| `diva` (spoken) | `maya_diva` | `qwen_diva`, `kokoro_diva` |
| `angry` | `maya_angry` | `qwen_angry`, `piper_spike` |
| `dutch` | `piper_pim` | `piper_ronnie` (Brabant), `piper_nathalie` (Flemish) |

- Switch a role for one render: `CAST="mc=qwen_hype,narrator=piper_ryan" PREVIEW=32-48 .venv/bin/python <name>.py`.
  The values must be CAST names (the value is split at commas, so a description does not fit there). For a new
  voice or another Maya seed, add an entry to `voice.CAST` (for example `"maya_hype2": "maya:<description>#302"`)
  and use its name. To make a choice final, write it in the script (`"cast:mc"` or the CAST name).
- CAST changes only lines written with `cast:<role>`. The older songs use Piper names; Overclocked Heart switches
  its narrators with `NARRATORS="maya_narrator|qwen_trailer"`.
- Hear a line in many voices: `.venv/bin/python voice.py --audition "<excited> Make some noise!"` (15 voices,
  about 3 minutes; `--voices a,b,c` for fewer).
- Emotion tags in the text: `<excited>`, `<laugh>`, `<whisper>`, `<angry>`, `<sarcastic>`, `<sigh>`. Only Maya
  uses them; the others get the line without tags. Maya's whisper needs a `<whisper>` before every sentence.
- Speed per line: Maya about 17 s, Qwen about 3 s, Kokoro and Piper about 1 s; every line is cached after.
- The user's verdicts: the new engines are "way better than other options so far"; in the song test "Maya wins",
  Qwen is nice too.
- Gang shouts: 16 speakers of `en_US-libritts_r-medium#N` (see `room_shout()` in `rhythm_of_the_badge.py`). A
  speaker of a many-speaker Piper model is `voice#speaker` (`en_GB-semaine-medium#spike`).

### Crowd moments (an A/B on The Rhythm Of The Badge, `CROWD=1`, not heard yet)

- The title within 8 bars of the music's entry (a teaser in the echo, bars 20 and 22).
- The band stops for one bar before the last chorus (bar 79), one shout: "Everybody!".
- "Sing it!" (bar 87), then the room shouts the first line of the last chorus's second pass (bar 88; hear it with
  `CROWD=1 PREVIEW=86-92`).
- A punchline right before the drums-only outro (bar 102; the DJ needs those 16 bars clean).

### 90s house vocal chops (an A/B on Warm Boot, `CHOPS=1`, not heard yet)

`chops.py`: words of an ACE-Step a cappella take cut by faster-whisper, each tuned to the bar's chord, played from
a 16-step pattern. In a song: `b = chops.bank(take_wav, {"hold", "on", "tight"})`, then per bar
`chops.play(S, bar, b, "hold . . on . . tight . . . . . . . . .", chord, swing=SWING)`.
`.venv/bin/python chops.py <take>.wav` lists the words it hears.

## The cheat sheet

### Rendering a song

| Command | What |
|---|---|
| `.venv/bin/python <name>.py` | the whole song to `renders/` |
| `PREVIEW=48-64` | only bars 48-63 (about 8 s) |
| `SOLO=vox` | only these buses, dry (no room, no delay) |
| `MUTE=vox` | without these buses (an instrumental) |
| `GAIN=keys:0.5` | a bus louder or softer, without editing |
| `AIR=1` | made-up highs above 11 kHz on the TTS and Piper-sung voices (our voices stop at 11-12 kHz; not on ACE takes, chops or a `ds:` diva) |
| `CAST="mc=qwen_hype"` | another CAST voice for a role |
| `DIVA=...` | the voice of `parts.Band`'s diva in template songs (a Piper voice or `ds:hanami`); do not use the name for anything else |

Every switch in this table except `DIVA` makes a test render: it goes to `renders/scratch/` with the switch in its
name (`<song>-preview48-64-air1.wav` and an MP3), and never replaces the song's render. So do the song-specific
A/B switches (`CROWD`, `CHOPS`, `VAMP`, `HARM`, `SINGER`, `NARRATORS`, `DIVA_WAV`, `DIVA_OFFSET`). A choice that
wins goes into the script; render once more without switches before `share.py` and `dj.py`.

Two leaks to know: with a `ds:` diva, `MUTE=vox` still keeps her last-word echoes; `low_pass_love.py` writes its
loop stems into the buses directly, so `MUTE` does not remove them.

### ACE-Step

```sh
.venv/bin/python takes.py <name> --drafts ...                         # a draft round (above)
.venv/bin/python takes.py --keep DRAFT.json [--guidance 7 --shift 3] [--ref WAV]   # a picked draft in SFT
.venv/bin/python takes.py <name> --bar 48 --lines "line one|line two" --caption "..."   # the older round: 4 SFT takes laid over the rendered song (needs it in share.SONGS)
.venv/bin/python takes.py --menu                                      # the voice menu: 18 kinds of voice
.venv/bin/python fit.py TAKE.wav --bpm 128 --chords "Bm Em A F#" [--snap natural] [--offset -1] [--shift N]
.venv/bin/python gag.py "Title" --lyrics words.txt --style "..." --bpm 150 --key "A minor" --lang en --seed 1
.venv/bin/python quick_gag.py "genre, language, topic" [--best] [--nerd]
.venv/bin/python produce.py <name> --project projects/_polish.toml --tag polish   # needs the song in share.SONGS
```

- `gag.py`: our own words, the 4B LM and the SFT DiT, about 3 minutes. Make three seeds (`--seed 1`, `2`, `3`):
  the seed matters a lot. Each seed gets its own folder (`<title>-seed2/`).
- `quick_gag.py`: Qwen writes the words (weaker than our own). Without `--best` it uses the fast 1.7B LM and the
  turbo DiT; `--best` is the 4B LM and SFT that the ears kept.
- Every ACE-Step step goes through one GPU door (`ace.gpu`): a lock (`renders/.gpu.lock`, or `ACE_LOCK=FILE`), a
  timeout, one retry after a VAE crash. The VAE runs in tiles of 512 (1024 crashed the GPU 15 times out of 15).

### Delivery

```sh
.venv/bin/python share.py --only my-song          # radio-edit MP3s and the DJ MP3s (all songs without --only)
.venv/bin/python dj.py --only my_song             # the DJ WAVs and the track list in renders/dj/
.venv/bin/python dj.py --use my_song=renders/produce/my_song/my_song-polish.wav   # a polished version instead
.venv/bin/python mix.py saturday --order auto     # the day as the DJ would play it
ffmpeg -i big.mp3 -b:a 192k small.mp3             # the phone takes files up to 30 MiB
```

`dj.py` checks each file: the grid, the true peak, drums-only ends, the length (a preview or a cut file), and a
render older than its script. It shows the loudness but does not check it. It stops on a name that is not in
`share.SONGS` and lists the names.

## What the ears decided

Keep:
- ACE-Step diva takes, a cappella (4B LM and SFT DiT), played WHOLE over our band (disco, big beat, Hi-NRG).
- The 3-semitone lift of an ACE take ("90s eurotrash").
- Maya and Qwen voices for spoken parts ("Maya wins"); Piper Ryan and Lessac as plain-speech MCs.
- Our numpy kits ("SOOOO much better" than LMMS).
- Gags: our own words, 4B LM + SFT, three seeds.
- The kit's own chords under a take.

Avoid (lost by ear):
- A free ACE take laid over our synthesized voices ("improvises like an idiot").
- ACE cover or re-sing of our vocal stem: a near copy, "very subtle".
- ACE lego (vocals over our instrumental): noise.
- A band re-harmonized to the take.
- LMMS; mastering plugins on a whole mix ("not exciting").
- Piper female voices singing (choppy).

Not heard yet (A/Bs on the phone, 19 November): drafts against full quality and guidance on; the slower
harmony; voice conversion with the original take (SoulX, Seed-VC: "a bit rough still"); crowd moments; the
snapped takes; the house chops; one singer across sections; the lyric tags; air above 11 kHz.

## Trouble and fixes

| Trouble | Fix |
|---|---|
| ACE-Step crashes the GPU (`vk::DeviceLostError`) | tiles of 512 are the default; `ace.gpu` tries once more; never two GPU jobs at once |
| A take comes back in another key | `fit.py` measures it; the draft round shifts it already |
| The last word is cut | drafts ask for a second more; `fit.py` says "ENDS MID-WORD": pick another draft |
| A song makes a new take while rendering | pin the take (`takes.pin`) and read the file (`kit_template.py` does) |
| Maya: a take runs on, or drops a sentence | a CAST entry with another seed (`#<other number>`); check its length |
| Qwen: the voice changes between lines | keep one seed per voice (`#42`); the CAST entries do |
| faster-whisper fails on a file path (PyAV) | pass the samples as an array (`asr.py`, `chops.py` do) |
| `dj.py --only` writes nothing | fixed: it stops on a name not in `share.SONGS` and lists the names |
| The voice sounds dull | it stops at 11-12 kHz; try `AIR=1` |
| A file is too big for the phone | a 192k copy with ffmpeg |
| The laptop swaps | one heavy job at a time; `free -g`; `fuser -k 52626/tcp` stops a kept Qwen NPU server |

## Where things are

| Path | What |
|---|---|
| `code/renders/` | the songs' WAVs (not in git); `renders/scratch/` test renders and previews |
| `code/renders/ace/takes/<name>/` | takes, drafts, keepers; `pinned/` the ones the songs play |
| `code/renders/ace/gags/` | gags (not on the stick, not in git); `picks.txt` the user's picks |
| `code/renders/dj/` | what goes on the USB stick |
| `code/renders/kits/` | the 11 kit sketches |
| `lyrics/` | the lyric sheets (`NN-<name>.txt`, NN the row in `share.SONGS`) |
| `~/Projects/acestep.cpp` | ACE-Step 1.5 (Vulkan), models in `models/` |
| `~/Projects/kokoro`, `~/Projects/qwentts.cpp`, `~/Projects/maya1` + `~/Projects/llama.cpp` | the three new voice engines |
| `~/Projects/audiocpp`, `~/Projects/audiocpp-src`, `~/Projects/audiocpp-models` | audio.cpp: Seed-VC and SoulX-Singer voice conversion (slow, not in the main route) |

## Timings on this laptop

| Job | Time |
|---|---|
| A preview of 16 bars | about 8-10 s |
| A whole song | 20-45 s (a first render with new Maya lines: minutes, about 17 s a line) |
| A draft round, 4 tunes (turbo) | about 100 s |
| A keeper in SFT, 16 bars | about 35 s (60 s with guidance on) |
| A gag, 2 minutes of song | about 3 minutes |
| A spoken line: Piper, Kokoro / Qwen / Maya | about 1 s / about 3 s / about 17 s |
| A voice audition, 15 voices | about 3 minutes |
| SoulX voice conversion, 36 s of singing | 1:42 at 16 steps, 4:07 at 32 |
| Seed-VC voice conversion, 36 s | about 8.5 minutes |
