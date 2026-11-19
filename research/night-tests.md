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

The rest follows when the night is over.
