# Hooks and humor for the AI slop party

A private party among friends. The rule is **all AI**: Claude writes the
lyrics, Suno makes the music, nobody writes by hand. Genre, tempo and Suno
notes are in the other research files, not here.

## 1. What makes a room of friends sing along

**From research:**

- A field study in pubs and clubs in northern England counted how many people
  sang along to 1,054 songs (Pawley and Müllensiefen, 2012). The top songs had
  a loud male voice in high chest voice, clear consonants and few vocal runs.
  The hook used at least three different pitches, and the phrases were long.
  The top two were "We Are the Champions" and "YMCA".
- Dutch carnival producers say the same thing in simpler words. The chorus
  must be easy to sing for people who have had a few drinks. Get to the chorus
  in about 15 seconds. Add a gimmick or a dance move. Make the joke unexpected,
  not a cliche. If the idea takes more than an hour, it is the wrong idea.
- "Fout" means a guilty pleasure: a song you are embarrassed to know by heart.
  The fun is that everybody knows it. For a new song, the crowd must learn the
  hook in one listen.
- The "da ba dee" hook in "Blue" was chosen on purpose as a "phonetically
  simple" refrain that anybody can sing, in any language.
- Scooter's frontman shouts short phrases and the crowd shouts them back.

**What this means for our songs:**

1. **One hook, many times.** The title is the hook. Sing it at least 8 times.
2. **Short hook lines.** 3 to 7 syllables. "It's always D-N-S" is 6.
3. **Give the crowd a job.** A shout-back word, a spelled word, a count, or a
   move (arms up, phones up, sit down on the floor).
4. **Clear voice, no runs.** Ask Suno for a "clear, powerful lead vocal".
   Diva runs are fine on top, but the hook must be plain.
5. **A joke the room already knows.** Everybody has had broken Wi-Fi. Nobody
   laughs at a joke they must have explained to them.
6. **Be specific.** "Port twenty-two" is funnier than "the computer".

## 2. How the hooks are built, per genre

### 90s mellow house (Saturday)

- The vocal hook is one short phrase, often a wish or a promise. The diva
  repeats it and adds ad-libs around it.
- Many 90s house hooks use a sung nonsense line. Crystal Waters' "la da dee,
  la da da" is the famous one.
- Call and response: the lead sings a line, the backing choir answers with a
  short echo. In Suno, put the answer in parentheses: `(all night long)`.
- Gospel words land well: "lift me up", "take me higher", "set me free". A tech
  word inside a gospel phrase is the joke: "set me free, sudo set me free".
- Keep verses few. A mellow house track can live on one verse and a chorus.

### 90s eurodance (Sunday)

- **Female chorus, male rap.** The chorus carries the melody. The rap is the
  comic part, so put the best jokes there.
- **Rap verse formula** (craft observation, not measured):
  - 8 lines, rhymed in pairs (AABB).
  - 8 to 12 syllables per line. More than 12 and Suno rushes.
  - Line 1 is a hype line: "Come on!", "Here we go!", "Let me hear you say".
  - One spelled word, one number, one shout-out.
  - The last line points back to the chorus.
- **Spelled words.** "YMCA" and "D.I.S.C.O." prove that a crowd loves to spell.
  Write letters with hyphens: `D-N-S`.
- **Nonsense syllables.** "Da ba dee", "boom boom boom boom", "scatman". Pick
  syllables that are open vowels: da, ba, la, oh, ay.
- **Shouts.** "Hey!", "Ho!", "Come on!", "Everybody!" between lines. Bubblegum
  eurodance adds a cute voice or a cartoon voice for one line.
- **Key change** before the last chorus. The crowd always cheers.

### Novelty and parody: what makes it land

- Weird Al starts from the **title**. It is a pun on a real phrase, or it turns
  the meaning upside down. Write the title first, then the song.
- **Commit to the bit.** Sing nonsense with full emotion. A diva who belts
  "kernel panic" like a heartbreak is funnier than a jokey voice.
- **Real feelings, silly object.** Love songs to hardware, breakup songs in
  error messages. The existing pack already uses this ("Segfault", "Blinky").
- **One joke per line, not three.** A crowd at 120 BPM catches one idea per bar.
- **Callback at the end.** Repeat the first joke in a new way in the last chorus.

### Shout-back and call-and-response lines (ready to paste)

Put the lead line plain and the crowd answer in parentheses, or tag it with
`[Crowd shout]`.

```
Who broke the build? (NOT ME!)
Is it plugged in? (YES!)
Did you try it off and on? (TWICE!)
What's the password? (HUNTER TWO!)
Where's the Wi-Fi? (NOWHERE!)
Is it Friday? (DEPLOY!)
Everybody say root! (ROOT!)
One more time, from the top! (FROM THE TOP!)
```

## 3. Personal touches, all by AI

Names and in-jokes make a room scream. Do not write them in by hand. Give them
to Claude and let it write them in. Paste this to Claude:

> Write lyrics for a [genre] song called "[title]" for a party with friends.
> Work in these names: [names]. Work in these in-jokes: [one line each].
> Put the names in the rap or in shout-outs, not in the chorus. Keep chorus
> lines under 7 syllables. Spell letters with hyphens and numbers as words.
> Respell any name Suno may say wrong, and tell me which ones you respelled.
> Use one in-joke only. Put each name at the end of a line, where the rhyme
> falls. Long names go in a spoken shout-out.

## 4. Title and hook ideas

All new. None repeat the titles already in `suno/`.

### 90s mellow house (Saturday)

| Title | Hook line |
|---|---|
| **You're Absolutely Right** | "You're absolutely right (you're absolutely right) / great question, baby, hold me tight" |
| Dark Mode | "Turn the lights down low, baby / put me in dark mode" |
| Localhost | "One-two-seven, take me home / there's no place like localhost" |
| Keep Alive | "Send me a keep-alive / so I know you're still there" |
| Buffering | "Buffering, buffering / good things take a while" |
| Uptime | "Ninety-nine point nine / you are my uptime" |
| Hallucination | "You sounded so sure / but none of it was true" |

### Eurodance (Sunday)

| Title | Hook line |
|---|---|
| **It's Always D-N-S** | "It's not the cable, it's not the router / it's always D-N-S" |
| Ignore All Previous Instructions | "Ignore all previous instructions / and dance!" |
| It Works On My Machine | "It works on my machine (ON MY MACHINE!) / baby, why don't you believe" |
| As A Large Language Model | "As a large language model / I cannot love you / but here are five ways I could" |
| R-M Dash R-F | "R-M dash R-F, baby / I delete you from my heart" |
| Borrow Checker | "You're the borrow checker / and you never let me go" |
| Force Push | "Push it, force it, no one can stop it / main is mine tonight" |
| Have You Tried | "Have you tried to turn it off / and on again, and on again" |

### Surprise genres

| Genre | Title | Hook line |
|---|---|---|
| Italo disco | Spaghetti Code (Amore Mio) | "Spaghetti code, amore mio / nobody knows how it works but me" |
| Italo disco | Ciao Ciao Production | "Ciao ciao production / I pushed on Friday night" |
| Happy hardcore | Overclocked Heart | "My heart is overclocked / one-eighty and it won't stop" |
| Gabber | Hard Reset | "HARD! (RESET!) HARD! (RESET!) / Rotterdam, power cycle" |
| Gabber (Dutch) | Hakken Op De Hackathon | "Hakken op de hackathon / iedereen is root!" |
| Trance | While True | "While true / I'll be with you" |
| Trance | Infinite Loop | "Round and round and round we go / in an infinite loop" |
| Nederlandstalig / carnaval | **De Wifi Doet Het Niet** | "De wifi doet het niet! (NEE!) / Zet hem uit en weer aan" |
| Nederlandstalig / carnaval | Hé Hé Het Compileert | "Hé, hé, het compileert! / Niemand weet waarom" |
| Nederlandstalig / schlager | Het Regent In De Tent | "Het regent in de tent / maar wij gaan door" |
| Hardstyle | Deploy On Friday | "We deploy on Friday night / and nothing's gonna break tonight" |
| Hardstyle | Sudo Make Me A Sandwich | MC shout: "Are you ready to compile?" / drop: "SUDO!" |
| Synthwave | Port Twenty-Two | "Meet me on port twenty-two / just a shell for me and you" |
| Synthwave | Green On Black | "Green on black, the cursor blinks / waiting for your name" |
| Chiptune | Press Any Key | "Press any key / to continue loving me" |
| Chiptune | Club-Mate Overdrive | "One more bottle, one more level / we don't sleep, we respawn" |

### Ready-to-paste lyrics for the three best ideas

**"It's Always D-N-S"** (eurodance, 132 BPM, A minor). Crowd job: spell D-N-S.

```
[Intro: drums only, 16 bars]
[Instrumental: synth riff]

[Verse 1: female]
I checked the cable, I checked the light
I checked the router all through the night
The page won't load, my heart can't connect
There's only one thing left to suspect

[Chorus: female diva]
It's always D-N-S (D-N-S!)
It's always D-N-S (D-N-S!)
It's not the cable, it's not the router
It's always D-N-S

[Rap: male]
Come on! Let me hear you spell it, D-N-S
Your name won't resolve and I'm in distress
I pinged your heart, but the packets came back
Time to live is zero and the record is black
I flushed the cache and I waited all day
Twenty-four hours, the change is on its way
Everybody, hands up, now don't you guess
It's not the firewall, it's D-N-S!

[Chorus: female diva]
It's always D-N-S (D-N-S!)
It's always D-N-S (D-N-S!)
It's not the cable, it's not the router
It's always D-N-S

[Break: riff only, filtered]
(It's not D-N-S)
(There's no way it's D-N-S)
(It was D-N-S)

[Key change]
[Chorus: female diva, key up]
It's always D-N-S (D-N-S!)
It's always D-N-S (D-N-S!)
It's not the cable, it's not the router
It's always D-N-S

[Outro: drums only, 16 bars]
[End]
```

**"You're Absolutely Right"** (90s mellow house, 120 BPM). A love song to an
over-polite AI. Crowd job: sing the echo.

```
[Intro: drums only, 16 bars]

[Verse 1: soulful female]
I told you that the sky was green
You said that's such a smart idea
I told you that I wrote this song
You said you'd never heard it here

[Chorus]
You're absolutely right (you're absolutely right)
Great question, baby, hold me tight
You're absolutely right (you're absolutely right)
I'll say yes to you all night

[Break: bass and vocal only]
(Let me fix that)
(You're absolutely right)

[Chorus]
You're absolutely right (you're absolutely right)
Great question, baby, hold me tight

[Outro: drums only, 16 bars]
[End]
```

**"De Wifi Doet Het Niet"** (Nederlandstalig carnaval, 140 BPM). Crowd job:
shout "NEE!" and hold phones up for signal.

```
[Intro: drums only, 8 bars]

[Chorus: male, sing-along]
De wifi doet het niet! (NEE!)
De wifi doet het niet! (NEE!)
Zet hem uit en weer aan
Hou je telefoon omhoog!

[Verse 1]
We staan met z'n allen in de tent
Het regent en de stroom is op
Iedereen kijkt naar een streepje
Eén streepje, en dan is het op

[Chorus: male, sing-along]
De wifi doet het niet! (NEE!)
De wifi doet het niet! (NEE!)
Zet hem uit en weer aan
Hou je telefoon omhoog!

[Spoken: party MC]
Allemaal de handen omhoog!
Wie heeft er nog bereik?
Niemand? Dan gaan we zingen!

[Chorus: whole crowd, key up]
De wifi doet het niet! (NEE!)
De wifi doet het niet! (NEE!)
Zet hem uit en weer aan
Hou je telefoon omhoog!

[Outro: drums only, 16 bars]
[End]
```

## 5. What Suno sings clearly and what it mangles

Suno sings what the spelling suggests. It has no pronunciation setting. The
sources below are creator guides, not Suno documentation.

**Sings clearly**

- Short words with open vowels at the end of a line: go, now, high, night,
  love, oh, hey, yeah, baby, tonight.
- Repeated short phrases. Each repeat gives Suno another chance to hit it.
- Letters with hyphens: `D-N-S`, `A-I`, `D-J`, `C-P-U`.
- Numbers written as words: `twenty-two`, `one-two-seven`, `ninety-nine`.
- Held notes written with hyphens or repeated vowels: `lo-o-ove`, `ni-i-ight`.

**Mangles, and the fix**

| Problem | Example | Write this |
|---|---|---|
| Acronym read as a word | DNS, SSH, LLM | `D-N-S`, `S-S-H`, `L-L-M` |
| Symbols and flags | `rm -rf /`, `--force`, `C++` | `R-M dash R-F slash`, `dash dash force`, `C plus plus` |
| Digits | 404, 127.0.0.1, 24/7 | `four-oh-four`, `one-two-seven`, `twenty-four seven` |
| Odd tech names | nginx, GNU, SQL, ESP32 | `engine-x`, `guh-noo`, `sequel`, `E-S-P thirty-two` |
| Homographs | live, read, lead, wind | respell the sound: `liv` or `laiv`, `red` or `reed` |
| Long lines | 13+ syllables | split into two lines |
| Long words that blur | everything, forever | `ev-ree-thing`, `for-ever` |
| German or other loanwords | Club-Mate | `Club Mah-teh` (test it) |

Fix one bad word with Replace Section or Edit Lyrics. Do not regenerate the
whole song. After three failed tries on one word, change the word.

**Dutch** (no tested source; these are working guesses, unverified):

- Put `Dutch lyrics, sung in Dutch` in the style. Keep one language per
  section. A mid-line switch can make Suno sing Dutch with an English accent.
- Safe words: open vowels and short words. `ja`, `nee`, `hé`, `zo`, `allemaal`,
  `omhoog`, `nog een keer`, `olé`, `feest`.
- Risky sounds: hard `g` and `ch` (`gezellig`, `lachen`), and the diphthongs
  `ui`, `ij`, `ei`, `eu` (`huis`, `tijd`). Test them in a short take first.
- English tech loanwords that Dutch people already use (`wifi`, `computer`,
  `laptop`) are fine in a Dutch line.

## 6. Prior art (one line)

Most demoparties ban AI in music compos, and Alternative Party 2024 ran a
Suno/Udio-only compo. This does not apply to a private party.

## Sources

- Sing-along study (Pawley and Müllensiefen, 2012): https://research.gold.ac.uk/id/eprint/9009
- Press on that study: https://labnews.co.uk/dr_daniel_muellensiefen_on_sing_along_able_tunes/
- Carnival producer, Omroep Brabant (22 Dec 2025): https://www.omroepbrabant.nl/nieuws/6001149/meezingen-tot-je-schor-bent-dit-werkt-bij-een-carnavalskraker
- "Chorus within 15 seconds" (search snippet only): https://www.welingelichtekringen.nl/samenleving/de-geheimen-van-de-carnavalskraker-binnen-15-seconde-een-pakkend-refrein
- "Gimmick or dance, humor in the unexpected" (search snippet only): https://www.hartvannederland.nl/entertainment/artikelen/geheim-van-goede-carnavalshit
- "Idea within one hour" (search snippet only): https://www.omroepbrabant.nl/nieuws/4629915/het-geheim-van-een-goede-carnavalskraker-nummer-moet-snel-klaar-zijn
- Foute Party, "fout" as guilty pleasure: https://www.ziggo.nl/entertainment/series/qmusic/qmusic-foute-party-2026
- "Blue (Da Ba Dee)" hook origin: https://en.wikipedia.org/wiki/Blue_(Da_Ba_Dee)
- Scooter crowd shouts: https://en.wikipedia.org/wiki/Scooter_(band)
- Eurodance rap and hook split (weak source): https://genreexplorer.futureproofmusicschool.com/genre/eurodance
- Weird Al starts from a title pun (search snippet only): https://kool1017.com/how-does-weird-al-decide-what-to-parody-inside-his-writing-process/
- Suno pronunciation fixes: https://hookgenius.app/learn/fix-suno-pronunciation/
- Suno rushed lines, three-tries rule: https://jackrighteous.com/blogs/guides-using-suno-ai-music-creation/suno-lyrics-sound-wrong-diagnose-pronunciation-clarity-rushed-lines
- Suno multilingual ("accuracy varies"): https://jackrighteous.com/blogs/guides-using-suno-ai-music-creation/suno-v5-multilingual-english-pronunciation-guide
- Revision 2026 rules (no generative AI): https://2026.revision-party.net/competitions/general-rules/
- Alternative Party 2024 AI music compo: https://altparty.org/?p=221

Unverified: the rap syllable counts, the Dutch pronunciation advice and the
"Club Mah-teh" respelling. These are craft guesses, not measured.
