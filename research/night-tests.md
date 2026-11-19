# Night tests, 19 November

Research for the compo weekend, run overnight on the laptop's iGPU and CPU while the user slept. Nothing here is
heard and approved yet: the user listens in the morning and decides. The scripts that ran the night are in
[night-2026-11-19/](night-2026-11-19/) (they ran from a scratch folder; the paths in them point there).

## The questions

1. **An ACE-Step singer for the weekend entries.** Our voices are "partly on purpose, partly by accident still very
   synthetic". In practice rounds 3 and 4 an ACE-Step take, sung a cappella (4B LM and SFT DiT) and played whole on
   the grid, worked. Does a layer of it suit the seven Saturday and Sunday songs? For each song, the first chorus
   (and the raps of Segfault, Blinky and the Badge) in four seeds, laid over our render at -8 dB
   ([takes.py](../code/takes.py)).
2. **A voice menu for surprise day.** Which kinds of voice does ACE-Step sing well a cappella? 18 kinds, 3 seeds each,
   on neutral words (`takes.py --menu`).
3. **Voices per genre.** For each of the 16 likely surprise genres ([surprise-genres.md](surprise-genres.md)) the
   genre's typical voice at its tempo, 4 seeds, so the singer for a drawn genre is chosen before the draw.
4. **The polish with SFT.** The earlier polish used the turbo DiT; for text to music the SFT DiT sounded best by ear.
   The same polish with SFT ([_polish_sft.toml](../code/projects/_polish_sft.toml)), against ours and turbo, 16
   chorus bars each.
5. **VAE stability.** On 18 November one ACE-Step VAE decode crashed the GPU (`vk::DeviceLostError`) while the CPU was
   busy; gag.py has used tiles of 512 since, the rest 1024. 30 runs with a CPU load, then runs without our own load
   until 07:00, tiles of 512 and 1024 in turn.
6. **Genre kits.** For the 11 likely genres not tried yet, a tempo, a key, a chord loop and the genre's band, one bar
   at a time, in `code/kits.py`, each with a 24-bar sketch. Written by agents, one genre at a time.
7. **Dry-run rounds.** Three whole surprise rounds by agents alone (synthwave, hardstyle and gabber, drawn at random),
   timed from the draw to the DJ file, to find where the time goes and what breaks.

## How it ran

- One ACE-Step job on the GPU at a time: two queues one after the other, and a lock file (`flock`) between the second
  queue and the dry-run rounds. Each ACE-Step step is its own process, so its models leave memory when it ends.
- A job starts only with 6 GB of RAM free (it waits up to 20 minutes, else it is skipped); a job is killed when free
  RAM falls under 1.5 GB or it runs past its time. RAM, swap and GPU memory were logged every 10 s.
- Before the night, the user's own FastFlowLM translation server (port 52625) was stopped, on the user's word: it
  held about 1.9 GB of shared memory.

## Results

Memory, from the queue's log: a 16 s take with the 4B LM and the SFT DiT needs about 25 s and at most about 5 GB of
RAM and 5.6 GB of GPU memory (GTT); free RAM never fell under 11.4 GB in the first queue (it starts at about 19 GB).

**VAE stability (5).** The first soak, 30 runs of a 115 s turbo synth with a song render and a numpy load on the
CPU: tiles of 512 passed 15 of 15 runs (76 s a run), tiles of 1024 crashed 15 of 15 (`vk::DeviceLostError`, 47 s
to the crash). Two of the seven SFT polishes crashed the same way (produce.py used the default 1024); with 512 both
went through. ace.py and produce.py now pass `--vae-chunk 512` (`ace.VAE_CHUNK`), as gag.py and takes.py already
did. The long soak until 07:00 runs only 512 (a crash at 1024 resets the GPU, the desktop's too).

**Genre kits (6).** `code/kits.py` has 11 kits, built by six agents one genre group at a time between 01:40 and
02:55: trance (138, Gm), eurobeat (155, Cm), hardstyle (150, F#m), gabber (180, Am), happy hardcore (170, F),
chiptune (130, Em), techno (132, Fm), acid house (124, Am), synthwave (118, Dm), Hi-NRG (128, Bm), carnaval (140,
Bb). Each sketch renders in about 8 to 13 s, at about -9 LUFS and -1.2 dBTP, on the beat grid (0.4 to 1.5 ms), with
only drums in its first 8 bars. Found on the way: in hardstyle and gabber the distorted kick's ripples fooled the
beat finder (17 to 20 ms off the grid); a kick sweep that drifts a little from beat to beat fixed it. A song that
adds a loud sustained part to those kits needs dj.py's grid check again. Nobody has heard the kits yet.

**Dry-run rounds (7).** Three whole surprise rounds by agents alone, each to a DJ file with no problems in dj.check:

| Genre | Song | Start to DJ file | Where the time went |
|---|---|---|---|
| synthwave | Outrun The Watchdog (`outrun_the_watchdog.py`) | 32 min | 29 min for three ACE takes, of it about 25 waiting for the GPU lock held by a 5-8 minute ace.py job of the other queue |
| hardstyle | Hard Reset (`hard_reset.py`) | 17 min | 14 min for the takes, again mostly the lock |
| gabber | Solder Harder (`solder_harder.py`) | 5 min | 3 min for the takes (44-48 s each, no wait); full render 29 s |

With the kit ready and the GPU free, a round without the user takes about 5 minutes; the song script is written
while the takes run. On compo day the time is the user's listening rounds, not the machine. The software ear picked
each round's take seed (the most words heard); the user picks by ear. None of the three is in share.SONGS.

**ACE-Step on our melody (1).** After the user's verdict at 01:58 (a free ACE take over our voices "improvises like
an idiot": its voice is nicer, its melody is its own), ace.py `--mode vocals --model sft` re-sang the vocal stems of
six songs at cover strength 0.95 and 1.0 (0.85 was there already), all 12 runs without a crash, 4 to 8 minutes each
(with the lock). The listen file puts ours, 0.85, 0.95 and 1.0 of each song in a row. Not heard yet.

**Voices per genre (3).** 16 genres, 4 seeds each, in 26 minutes; one listen file per genre and one for all
(`renders/ace/takes/genres/`, the captions in `genres.txt`). Not heard yet.

**VAE stability, the long soak (5).** From 04:11 to 07:00 with tiles of 512 and no load of our own: 240 of 240 runs
passed, no `vk::DeviceLostError`, 39 s a run. With the first soak, tiles of 512 are now 255 of 255 and tiles of 1024
0 of 15 under load. 512 is the setting.

**Memory over the night.** Free RAM was never under 11.2 GB (of about 19 GB at the start, 23 GB in the second
queue); swap was not used; GTT at most 5.7 GB (the 4B LM with the SFT DiT). No job was skipped or killed by the
memory guard. The machine can run one ACE-Step job next to a song render with room to spare; two ACE-Step jobs at
once were never tried and stay out (the GPU lock).

## For the user to decide

- ACE-Step re-singing our melody: which strength, if any, for which songs.
- The voice for each surprise genre: a seed per genre from the voices file.
- The polish: ours, turbo or SFT, per song.
- The kits: which sound right for their genre, which need work.
- The dry-run songs: research only, unless one is worth keeping.
