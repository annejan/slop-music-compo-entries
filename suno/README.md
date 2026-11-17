# AI slop music compo: Suno pack

Rules from the organisers:

- Make the whole track with AI. You can write the lyrics yourself. Keep it fun.
- Each day has two themes. The second theme comes two hours before the deadline.
- The DJ mixes the tracks live. Use the normal tempo of the genre.
- Each person gets at least one track played. If you send more, mark the best one.
- Hand in on a USB stick. Watch the download limit on your Suno plan.

| Day | Theme | Tempo | Files |
|---|---|---|---|
| Saturday | 90's mellow house | 120 BPM | [saturday-mellow-house.md](saturday-mellow-house.md) |
| Saturday | announced 2 h before | see the recipe | [surprise-theme-recipe.md](surprise-theme-recipe.md) |
| Sunday | eurodance | 140 BPM | [sunday-eurodance.md](sunday-eurodance.md) |
| Sunday | announced 2 h before | see the recipe | [surprise-theme-recipe.md](surprise-theme-recipe.md) |

## How to use a prompt in Suno

1. Open **Create** and turn on **Custom** mode.
2. Copy the **Style** block into the style field.
3. Copy the **Lyrics** block into the lyrics field. Keep the `[tags]`: they set
   the song structure.
4. Copy the **Exclude** block into "Exclude styles", if your version has it.
5. Generate. Each run gives two takes. Listen to the full take, not only the first
   30 seconds.
6. Use **Extend** or **Replace section** to fix a bad bar. Do not regenerate the
   full song for one bad bar.

## Make it easy for the DJ

- Keep the tempo the same from start to end. Do not add "tempo change" tags.
- Ask for a drum-only intro and outro. Suno does not always obey. If it does not,
  cut the intro and outro of a good take with Extend.
- Download as **WAV**, not MP3, if your plan allows it.
- Name the files like this: `annejan_sat_mellow-house_BEST_120bpm_Am.wav`.
- Put the tempo and key in the file name. The DJ can then mix without searching.
- Check the tempo after download. `ffmpeg` cannot detect BPM. Use a DJ app,
  Audacity (Analyze > Beat Finder), or `aubio tempo file.wav`.

## Download budget

Generate a lot, download a little. Pick the best take in the browser first.
Download only the takes that you will hand in, plus one spare per theme.
