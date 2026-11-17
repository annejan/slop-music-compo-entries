# Suno tips for the compo (state: November 2026)

Suno changes fast. Most numbers below come from third-party guides, not from
Suno's own help pages. Check the live app on the day.

## Current model

- **v6 family, released 9 September 2026.** Three models:
  - **v6:** flagship. Pro and Premier only.
  - **v6-wild:** more experimental, less predictable output. Pro and Premier.
  - **v6-mini:** faster, cheaper. Available to everyone, including Free.
- Previous model: v5.5 (26 March 2026). Suno says it will retire earlier
  models as v6 rolls out.
- v6 was trained on licensed catalogue (Warner Music Group, BMG, Believe).
- New in v6: edit one section in plain language ("change the chorus to a
  gospel choir"), change one lyric line without regenerating, mashups from
  several songs, sample a riff from an uploaded song, and prompts from text,
  audio, images or video.

**Compo impact:** Free users only get v6-mini. If an entrant cares about
quality, one month of Pro is the cheapest way to get v6.

## Field limits

| Field | Limit | Confidence |
|---|---|---|
| Style of Music | approx. 1,000 characters on v4.5 / v5 / v5.5; about 200 on v4 and older | third-party guides; v6 limit not published |
| Lyrics | approx. 3,000-5,000 characters | guides disagree |
| Song length | up to approx. 8 min per generation; Extend for more | one guide; unverified for v6 |
| Duration | "Custom" or "Auto" slider (added 20 July 2026) | guide plus v6 coverage |

- Suno cuts text over the limit **without a warning**. Put the important tags
  (genre, BPM, vocal) first.
- Keep compo prompts under 200 characters anyway. Short prompts are less
  likely to contradict themselves.
- Use the separate **Exclude** field (Advanced Options) for things you do not
  want. "no drums" inside the Style field is unreliable.

## Advanced Mode controls (v6)

- Vocal Gender (male / female).
- Duration (Custom or Auto).
- Max Mode on/off: aimed at consistency over long songs and covers, not at raw
  audio quality.
- Sliders: Weirdness and Style Influence (both default 50%), Variety (new,
  default Normal).
- Higher Style Influence should make Suno follow your style text more
  closely. Lower Weirdness gives safer, more generic output. Both effects are
  community observations, not documented guarantees.

## Lyrics meta tags

Suno officially calls labels such as Verse and Outro "song structure labels".
The other tags are community conventions: they often work, but nothing is
guaranteed. Tags go in square brackets on their own line, in the Lyrics field,
before the section they describe. They are case-insensitive.

**Structure:** `[Intro]`, `[Verse]` / `[Verse 1]`, `[Pre-Chorus]`, `[Chorus]`,
`[Post-Chorus]`, `[Hook]`, `[Bridge]`, `[Break]`, `[Breakdown]`, `[Build]` /
`[Build-Up]`, `[Drop]`, `[Interlude]`, `[Outro]`.

**End:** `[End]` acts as a hard stop and reduces trailing audio. `[Fade Out]`
asks for a fade (bad for DJs: a fade-out is hard to mix out of).

**Instrumental:** `[Instrumental]`, `[Instrumental Intro]`, `[Instrumental
Break]`, solo tags such as `[Piano Solo]`, `[Synth Solo]`, `[Drum Solo]`.
There is no reliable `[no vocals]` tag. For a fully instrumental track use the
Instrumental switch in the create screen.

**Vocals:** `[Male Vocal]`, `[Female Vocal]`, `[Duet]`, `[Choir]`,
`[Harmony]`, `[Rap]`, `[Spoken Word]`, `[Whisper]`, `[Ad-lib]`, `[Backing
Vocals]`. Community practice (not sourced here): put backing lines in round
brackets inside a lyric line, for example `Tonight (tonight!)`.

**Dynamics:** `[Key Change]`, `[Crescendo]`, `[Silence]`, `[Tempo: slow]`.
Avoid tempo tags in a DJ track.

**Descriptors after a colon:** `[Verse: whispered vocals, piano only]`,
`[Intro: drums only, 16 bars]`, `[Chorus: female vocal, full energy]`. This
form is widely used. The exact grammar is not documented.

## Getting a stable BPM

Suno has **no BPM lock** for song generation. Guides call the BPM in the Style
field "approximate". Some v6 reviews report that v6 often ignores BPM and other
specific details. Suno Studio (the DAW) has tempo tools: time-stretch to project
tempo (October 2026) and a BPM-aware chat bar (September 2026).

What helps:

1. **Write a number, not a word.** "128 BPM", not "fast". Guides report that
   Suno ignores qualitative tempo words more often.
2. **Put the BPM near the start** of the Style field, next to the genre.
3. **Use one tempo only.** Do not write "120-128 BPM" and do not mix genres
   with very different tempos (for example "house and drum and bass").
4. **Pick a genre tag that implies the tempo.** "90s eurodance" already pulls
   toward 125-140 BPM. The BPM number then only fine-tunes.
5. **Add "steady tempo"** or "consistent BPM". Some guides recommend it. The
   effect is unverified.
6. **Generate several versions** and measure each one in DJ software (Mixxx,
   rekordbox, Traktor, Serato). Keep the one closest to target with a stable
   beat grid.
7. **Let the DJ fix the rest.** A difference of 2-4 BPM is easy for the DJ
   to pitch live. (Our rule is all AI: no time-stretching by hand.) A track
   whose tempo drifts during the song is much harder to fix. Reject it.
8. **Half-time traps:** at 170+ BPM, Suno and BPM analysers sometimes land on
   half time (85 BPM). Listen before you trust the number.

## Getting instrumental (DJ-friendly) intros and outros

Suno likes to start singing early and to end with a fade or a sudden stop.
DJs need 16-32 bars of beat at both ends. Combine these methods:

1. **Style field:** add "DJ-friendly drum intro and outro" or "extended club
   mix" at the end of the prompt.
2. **Lyrics field:** start with `[Intro: drums only]` and `[Instrumental]`
   before the first vocal. End with `[Outro: drums only]` and `[End]`. Do not
   use `[Fade Out]`.
3. **Extend:** if the song ends too soon, extend from near the end and start
   the extension lyrics with `[Outro: drums only]` and `[End]`. Each extension
   adds approx. 30-60 seconds.
4. **Replace Section / section edit:** regenerate only the intro or outro.
   Budget 2-5 tries for a clean join. In v6 you can describe the change in
   plain language.
5. **Not for us: edit in a DAW.** Copying drum bars by hand to the start and
   end is the most reliable fix, but it breaks our all-AI rule. Use Extend and
   Replace Section, or generate another take.

## Extend, Replace, Cover, Persona / Voices, stems

- **Extend:** continues a song past its end. Start the extension with a
  structure tag such as `[Chorus]` or `[Outro]`. Costs credits.
- **Replace Section (Song Editor):** regenerates a chosen section or time range
  with new instructions. Good to fix a bad bridge or a missing intro.
- **Cover:** Pro and Premier. Keeps the melody and lyrics and changes the
  style and arrangement. Useful when the surprise theme drops: cover a track
  you already like into the new genre. (Check that the compo rules allow
  this.)
- **Persona to Voices:** a Persona kept a singer's timbre and basic delivery,
  not melodies. Since v5.5 the Create menu has "Voices" instead, with Style
  Personas inside it. Since August 2026 you can "record your voice once and use
  it on any song" (also on iOS and Android; more on paid plans).
- **Stems:** Split from Mix (one instrument or voice versus the rest), Auto
  Split (up to 12 groups, Pro and Premier), Advanced Split (approx. 100
  instruments, Premier). Sources disagree on whether Free gets any stems.
  Premier also gets MIDI from stems (10 credits) and Suno Studio.

## Plans, downloads and formats

Prices from a guide checked on 25 October 2026. Check suno.com/pricing.

| | Free | Pro | Premier |
|---|---|---|---|
| Price | $0 | $10/month ($8/month yearly) | $30/month ($24/month yearly) |
| Credits | 50/day (approx. 10 songs) | 2,500/month | 10,000/month |
| Models | v6-mini | v6, v6-wild, v6-mini | v6, v6-wild, v6-mini |
| Downloads | up to 7 lifetime (eligible accounts) | 20 songs/month | 60 songs/month; Studio exports unlimited |
| Formats | MP3 (WAV not confirmed) | MP3 and WAV | MP3 and WAV |
| Commercial use | no | yes, subject to terms | yes, subject to terms |

- Download caps started in September 2026. One song counts as one download,
  including its stems. Re-downloads, extra formats and failed downloads do not
  count.
- Upgrading does not make earlier Free songs commercial.
- Suno is adding audio watermarking and fingerprinting (announced August 2026).
- **Compo impact:** a Free account can download only a handful of songs in
  total. Do not waste downloads on test versions: listen in the browser first,
  then download the final one as **WAV**.

## Artist names are blocked

- Suno's August 2026 policy post: Suno has "never allowed prompts for specific
  artists or copyrighted songs". When a prompt names an artist, Suno removes
  the name and steers toward descriptive traits.
- Users report an error like "we don't reference specific artists on Suno"
  when names appear in lyrics. Exact wording unverified.
- There is no public list of blocked words. Song titles and producer names can
  also trigger the filter.
- **Workaround:** describe era, genre, instruments, vocal type and mood.
  "1993 eurodance, belting female chorus, male rap verse" works better than
  any artist name ever did.

## Compo checklist

1. Prepare 2-3 prompts per theme before the party (see the genre files).
2. Generate 4-8 versions per prompt. Listen in the browser.
3. Measure BPM in DJ software. Keep tracks within 2 BPM of target.
4. Check for a beat-only intro and outro of at least 16 bars. Fix with
   Replace Section or Extend (no hand edits: all AI).
5. Download the final version once, as WAV.
6. Name the file `Artist - Title (BPM, key).wav` so the DJ can sort fast.

## Alternatives in 2026

- **Udio:** settled with UMG in October 2025 and then disabled downloads. It
  plans a licensed, more closed platform in 2026. As of the sources found, it
  is unclear whether downloads are back. Not usable if you need a file.
- **ElevenLabs Eleven Music:** launched as a separate product in 2026 (per one
  source). Clear commercial rights. Reviewers say it is better at
  instrumentals than full vocal songs.
- **Google Flow Music (Lyria):** one guide lists it with free daily credits.
  Unverified.
- **Stable Audio:** instrumental only, no vocals. Trained on licensed data;
  open-weights models can run locally, which suits a techy crowd.

## Sources

- https://suno.com/blog/introducing-v6
- https://suno.com/release-notes/introducing-v6
- https://suno.com/release-notes
- https://suno.com/blog/building-the-future-of-music-responsibly
- https://weraveyou.com/2026/09/suno-v6-models-features-editing-sampling-advanced-mode/
- https://www.digitalmusicnews.com/2026/03/26/suno-launches-version-5-5/
- https://datanorth.ai/news/suno-launches-v6-v6-wild-and-v6-mini
- https://blakecrosley.com/guides/suno-ai-music-generation
- https://jackrighteous.com/ja/blogs/guides-using-suno-ai-music-creation/suno-ai-4-5-metatag-tutorial
- https://hookgenius.app/learn/suno-metatags-complete-list/
- https://hookgenius.app/learn/suno-tempo-bpm-guide/
- https://hookgenius.app/learn/suno-character-limits/
- https://usesuno.pages.dev/guide/limits
- https://www.layer3labs.io/guides/how-to-write-suno-prompts
- https://sonilo.com/blog/guides/what-suno-tags-mean-video-background-music
- https://www.eesel.ai/blog/suno-v6-review
- https://aireiter.com/blog/suno-v6-review-tested-migration-guide
- https://diyai.io/ai-tools/audio-generation/suno-pricing/
- https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-prompt-contained-inappropriate-material
- https://hookgenius.app/learn/suno-content-filter-blocked-words/
- https://www.all-ai.de/news/news26/suno-neue-regeln
- https://routenote.com/blog/udio-stops-user-downloads-after-umg-deal-heres-why/
- https://www.digitalmusicnews.com/2025/11/20/will-udio-still-exist-in-2026/
- https://undetectr.com/blog/udio-download
- https://fast.io/resources/suno-alternatives-2026/
- https://elevenlabs.io/blog/suno-alternatives
- https://getimg.ai/blog/best-ai-music-generator
