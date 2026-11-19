"""The voice bank per genre: for each likely surprise genre (research/surprise-genres.md), ACE-Step sings a cappella
with that genre's typical voice, 4 seeds, at the genre's prompt tempo. One MP3 per genre (for the day) and one with
all of them (for the morning listen)."""
import os
import sys

sys.path.insert(0, "/home/annejan/Projects/music/code")
import engine as e  # noqa: E402
import master  # noqa: E402
import takes as T  # noqa: E402

SING, RAP, DUTCH = T.SING, T.RAP, T.DUTCH
CHANT = ["Feel the machine", "Move to the beat", "Feel the machine", "Lose control"]
GENRES = [  # (genre, BPM, key, caption, words, tag, language)
    ("synthwave", 118, "A minor", "1980s synthwave, a dreamy female singer, nostalgic, lush reverb", SING, "Chorus"),
    ("disco", 120, "A minor", "late 1970s disco, a soulful female diva, powerful and soaring, gospel runs", SING,
     "Chorus"),
    ("italo disco", 120, "D minor", "1980s Italo disco, a melancholic male singer with an Italian accent", SING,
     "Chorus"),
    ("big beat", 120, "E minor", "late 1990s big beat, a gritty soulful female vocal, bluesy", SING, "Chorus"),
    ("french house", 124, "A minor", "late 1990s French house, a smooth male disco soul singer with falsetto", SING,
     "Chorus"),
    ("acid house", 124, "A minor", "late 1980s acid house, a deep spoken male voice, hypnotic chant", CHANT, "Verse"),
    ("hi-nrg", 128, "A minor", "1980s Hi-NRG, a powerful dramatic female dance diva", SING, "Chorus"),
    ("chiptune", 130, "C major", "chiptune pop, a bright cute female pop singer", SING, "Chorus"),
    ("techno", 132, "A minor", "1990s techno, a deep monotone spoken male voice, hypnotic", CHANT, "Verse"),
    ("carnaval", 140, "G major", "Dutch carnival schlager, a cheerful male sing-along singer, beer hall", DUTCH,
     "Chorus", "nl"),
    ("trance", 138, "A minor", "late 1990s trance, an ethereal soaring female vocal, emotional", SING, "Chorus"),
    ("eurobeat", 155, "A minor", "late 1990s eurobeat, an energetic male singer, fast and dramatic", SING, "Chorus"),
    ("hardstyle", 150, "A minor", "hardstyle, an epic powerful male vocal, anthemic and euphoric", SING, "Chorus"),
    ("happy hardcore", 170, "C major", "mid 1990s happy hardcore, a high pitched cheerful female vocal", SING,
     "Chorus"),
    ("drum and bass", 174, "F minor", "1990s drum and bass, a fast rhythmic male MC, clear words", RAP, "Rap"),
    ("gabber", 180, "A minor", "1990s Rotterdam gabber, a distorted shouting male MC, aggressive", T.SHOUT, "Chorus"),
]


def main():
    out = os.path.join(T.TAKES, "genres")
    everything = []
    for g in GENRES:
        genre, bpm, key, caption, lines, tag = g[:6]
        lang = g[6] if len(g) > 6 else "en"
        bars = 8 if bpm < 150 else 16
        parts = [T.label(f"{genre}, {bpm} B P M.", .09)]
        for s in (1, 2, 3, 4):
            w = T.take(caption, T.ace_words(lines, tag), bpm, key, bars, s, out, T.slug(genre), lang)
            if not w:
                print(f"{genre}, seed {s}: no take", file=sys.stderr, flush=True)
                continue
            y = T.roomy(e.bandpass(T.mono(w), 80, 12000), .15)
            parts += [T.label(T.WORDS[s], .06), master.master(y, -16.0), T.gap(.5)]
        T.listen(parts, os.path.join(out, f"{genre}.mp3"), f"ACE voices: {genre}")
        everything += parts + [T.gap(.6)]
        print(f"{genre}: done", flush=True)
    open(os.path.join(out, "genres.txt"), "w").write(
        "\n".join(f"{g[0]}: {g[1]} BPM, {g[2]}: {g[3]}" for g in GENRES) + "\n")
    print(T.listen(everything, os.path.join(out, "ACE voices per genre.mp3"), "ACE voices per genre"))


if __name__ == "__main__":
    main()
