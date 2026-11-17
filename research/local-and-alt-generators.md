# Local and alternative AI music generators (state: 17 November 2026)

Scope: what runs on this laptop, and which hosted services can replace Suno.
Machine: Ryzen AI 7 PRO 350 (8 cores, 16 threads, AVX-512), Radeon 860M
(gfx1152, 8 CUs), 27 GB RAM. Measured on the machine: 4 GiB VRAM carve-out
plus 14.5 GB GTT (shared RAM the GPU can use), Mesa 26.2 RADV Vulkan works,
`glslc`, Vulkan and OpenBLAS headers, `cmake` and `uv` are present, user is in
the `render` and `video` groups. System Python is 3.13.

"Guess" marks every number that nobody has measured on this hardware.

## Recommendation for this machine

**1. ACE-Step 1.5 through acestep.cpp on Vulkan (full songs, and vocals over our own tracks).**
ACE-Step 1.5 is the only open model that is permissive (MIT, output usable
commercially), small enough for an iGPU, and has BPM, key, time signature and
duration fields. acestep.cpp is a GGML port: no PyTorch, no ROCm, it uses the
RADV Vulkan driver that already works here.

```
git clone --recurse-submodules https://github.com/ServeurpersoCom/acestep.cpp.git
cd acestep.cpp
./buildvulkan.sh          # or ./buildcpu.sh for a CPU-only build
uv tool install hf        # models.sh needs the hf CLI
./models.sh               # default set, about 7.7 GB (4B LM Q8, turbo DiT Q8, VAE)
./server.sh               # browser UI; CLI: ace-lm then ace-synth with --device Vulkan0
```

- Also fetch `acestep-v15-base-Q8_0.gguf` and a smaller LM (0.6B or 1.7B) from
  the `Serveurperso/ACE-Step-1.5-GGUF` repo.
- **Vocals for the numpy tracks:** the `lego` task takes an existing backing
  track (`--src-audio`) and generates one new layer over it. Track names
  include `vocals` and `backing_vocals`. Lego needs the base DiT (50 steps),
  not turbo. Render a song from `code/`, pass it as source, give lyrics and a
  caption. The model picks the melody; you do not control the notes.
- **Time, 3-minute song (guess):** turbo DiT plus 1.7B LM on the 860M: 3-8
  minutes. Lego with the base DiT: 10-25 minutes. CPU build: 15-30 minutes.
  Basis: a Radeon 780M (12 CUs, ROCm) does a 90 s track at 50 steps in 40-55 s
  of DiT time; a Ryzen 9 7900X3D CPU needs about 2.5 minutes per 30 s of audio
  with the PyTorch version. No published Vulkan timings exist.

**2. OpenUtau with a DiffSinger English voicebank (a real singer on our own melody).**
This is the path when the melody, timing and words must stay exactly as written
in Python. OpenUtau is MIT, ships a Linux AppImage, and has DiffSinger built in.
It runs on CPU.

```
wget https://github.com/openutau/OpenUtau/releases/download/0.1.576/OpenUtau-linux-x64.AppImage
chmod +x OpenUtau-linux-x64.AppImage && ./OpenUtau-linux-x64.AppImage
```

- Drop an English DiffSinger voicebank zip into the window. Read its licence
  file. Most free banks allow non-commercial use only, which covers a compo.
- `robot()` in `code/engine.py` already holds (onset, vowels, MIDI note,
  seconds, coda) per syllable. Write those as notes with lyrics into a `.ustx`
  project (YAML; save an empty project first and copy its layout), render in
  OpenUtau, export WAV, and mix it in numpy instead of the formant robot.
- There is no headless CLI. Fully scripted rendering needs a small ONNX Runtime
  wrapper around the voicebank (see DiffSingerMiniEngine and dsapi below).
- **Time (guess):** 1-3 minutes of CPU per 3 minutes of vocals.

**3. Hosted fallback when local quality is not enough: ACE Music v1 or Mureka.**
ACE Music v1 (acemusic.ai, from ACE Studio, closed model) ranks first on the
Artificial Analysis vocal leaderboard, above Suno v6. Reported: Creator plan
$7.90/month (annual) with unlimited downloads and commercial use, and input from
text, lyrics, a hummed melody or a MIDI file. MIDI input would let us feed our
Python melodies. These plan details come from one secondary source; check the
site. Mureka Basic is $8/month for 400 songs with MP3 downloads and commercial
rights. Time: under 2 minutes per song (server side).

## 1. Open-weight full-song generators (lyrics plus vocals)

| Model | Released | Weights licence | Size | Max length | BPM / key control | Runs here? Time per 3 min (guess) |
|---|---|---|---|---|---|---|
| **ACE-Step 1.5** (ACE Studio + StepFun) | Jan-Feb 2026 | MIT; card says output may be used commercially | 2B DiT (turbo 8 steps, sft/base 50) + 0.6/1.7/4B LM | 10 min | Yes: BPM, key/scale, time signature, duration | Yes: Vulkan (acestep.cpp), ROCm, CPU. 3-8 min iGPU, 15-30 min CPU |
| ACE-Step 1.5 XL | 2 Apr 2026 | MIT | 4B DiT, about 9 GB bf16 | 10 min | Same | Needs 12 GB with offload and quantisation. Maybe on GTT; 20-60 min |
| YuE2-3B (M-A-P) | 9 Sep 2026 | CC BY-NC 4.0 | 4B bf16 (card says 3B) | Demos to 5:00 | No BPM/key; editable ABC score layer (melody and chords) | CUDA-only examples, 11 GiB peak. RTX 4090: 215 s song in 71 s. Here: 30-90 min if ROCm works, hours on CPU |
| YuE (v1) | Jan 2025 | Apache 2.0 | 7B + 1B stages | 5 min | No | 4090 needs 360 s per 30 s of audio. Not practical |
| MiniMax Music 3 | Aug 2026 | CC BY-NC 4.0 | 57 GB repo | 5 min | Not documented | 24 GB+ VRAM, 8 GB with CPU offload. Not practical |
| LeVo 2 / SongGeneration 2 (Tencent) | 1 Mar 2026 | Custom: "academic, research and education purposes" only | 4B (large), medium version | 4:30 | Text description, prompt audio | 12-28 GB VRAM. RTF 0.82 on a big GPU. Not practical |
| HeartMuLa-oss-3B | 14 Jan 2026 | Apache 2.0 | 3B + codec | 4 min default | Tags only | CUDA examples, RTF about 1.0 on GPU. 1-3 h on CPU |
| DiffRhythm 2 (ASLP / Xiaomi) | 30 Oct 2025 | Apache 2.0 | about 1B | Not stated | Style from a reference WAV, no text prompt | CUDA script; CPU maybe 30-60 min |
| SongBloom (Tencent) | 2025 | "other", not checked | 2B | 2:30 | 10 s WAV prompt | Not tested by anyone on AMD |

Not available as weights: Qwen-Music (paper only, July 2026), StepAudio 3 Music
(free preview API only), ACE Music v1 (hosted).

**Quality against Suno.** The Artificial Analysis AA-Music-Vocal v1.1 board
lists no open model in its top 14 except possibly MiniMax Music 3.0 (rank 10,
the board's anchor). Suno v6 is at rank 2. ACE-Step's paper claims it beats
Suno v5 on SongEval; YuE2 claims it beats Suno v5 on WildSongBench. Both are the
authors' own benchmarks. Guess: ACE-Step 1.5 sounds like Suno v4.5 to v5 on a
good seed, with weaker vocals. Expect to generate 5-10 takes per keeper.

**Licences and the compo.** Playing a track at a non-commercial party compo is
non-commercial use, so CC BY-NC weights are probably fine with attribution.
Tencent's "academic, research and education" wording is narrower; a party compo
is a grey area. Only ACE-Step, HeartMuLa and DiffRhythm 2 are clean for a later
Bandcamp or streaming release. This is not legal advice.

## 2. Instrumental and stem generators

| Model | Licence | Size / length | Notes for this machine (times are guesses) |
|---|---|---|---|
| **ACE-Step 1.5** with `[Instrumental]` | MIT | as above | Same setup as recommendation 1. Tasks `extract`, `lego`, `complete`, `repaint`, `cover` give stems, layers, inpainting and restyling. Best all-round choice here |
| Stable Audio 3 Small (music) | Stability Community Licence: free under $1M revenue, you own output | 459M, up to 2 min | Released 20 May 2026. Built for phones and laptops. Gated on Hugging Face (log in, accept terms). Instrumental only. 1-5 min on CPU |
| Stable Audio 3 Medium | Same | 1.4B, up to 6:20 | GPU recommended (8 GB). Large (2.7B) is API-only |
| Stable Audio Open 1.0 / Open Small | Same | 47 s / 11 s | Old; sound design and loops more than songs |
| MusicGen (Meta audiocraft) | Code MIT, weights CC BY-NC 4.0 | 300M-3.3B, 30 s windows | Small model runs on CPU, about 1-3 min per 30 s. Outdated quality |
| Magenta RealTime (v1) | Code Apache 2.0, weights CC BY 4.0 | 800M, live streaming | JAX. JAX on gfx1152 needs the ROCm 10.2 nightly (fix landed 21 Oct 2026). Not real-time here |
| Magenta RealTime 2 | Open weights, terms not stated on the page | 2.4B / 230M | Released 4 June 2026. Apple Silicon (MLX) app and plugin; one community CUDA port. Not for this machine |
| DEMON (Daydream) | AGPL-3.0, uses ACE-Step weights | Streaming | Real-time diffusion engine on top of ACE-Step 1.5. Needs a real GPU |

## 3. Singing voice synthesis we can drive from Python

Requirements: note plus lyric input, CPU, English, permissive licence,
single binary or pip.

| Tool | Note + lyric input | CPU | English | Licence | Install |
|---|---|---|---|---|---|
| **OpenUtau 0.1.576** (20 Oct 2026) + DiffSinger voicebank | Yes (piano roll, `.ustx`, MIDI import) | Yes (ONNX) | Yes, community banks (ARPAbet) | App MIT; each voicebank has its own terms | AppImage |
| DiffSinger (openvpi) | Yes, `.ds` JSON (phonemes, notes, durations) | Yes | Depends on the model | Code Apache 2.0 | `git clone`; `python scripts/infer.py acoustic FILE.ds --exp EXP` needs PyTorch checkpoints, not OpenUtau ONNX banks |
| DiffSingerMiniEngine / dsapi | `.ds` input | Yes (onnxruntime) | As the voicebank | See repos | Small Python projects; dsapi loads OpenUtau-format banks in `src/dsapi/voicebank.py` |
| SoulX-Singer (Feb 2026) | MIDI notes + lyrics, or an F0 curve, plus a reference voice clip | Not documented; GPU assumed | Trained on Mandarin, English, Cantonese | Apache 2.0 (code and weights) | `git clone`, conda, `pip install -r requirements.txt`, `hf download` |
| NNSVS | MusicXML to HTS labels | Yes | No English pretrained model | MIT; models often research-only | `pip install nnsvs` |
| Sinsy / pysinsy | MusicXML | Yes | Japanese focus (from memory, not checked) | Modified BSD | pip |

**English DiffSinger voicebanks.** No CC0 English bank turned up. Peiton DS
needs a paid licence for commercial use. LUNAI and Ameko banks are
non-commercial. Lotte V says her DiffSinger banks need no permission for
commercial use, but that is a blog post, not a licence file. For the compo,
non-commercial terms are enough.

**Zero-shot voice cloning (SoulX-Singer and its SVC model).** These need a
reference recording of a singer. Use your own voice or one with consent.

**TTS fallback (pitched speech).** Render each syllable with a TTS engine, then
force it onto the note with a vocoder. It sounds like hard auto-tune, but the
words are clear, which already beats the formant robot.

- Kokoro: 82M, Apache 2.0, English voices, much faster than real time on CPU
  (guess: seconds per song). `pip install kokoro soundfile` (needs `espeak-ng`).
- Piper: now GPL-3.0 (`OHF-Voice/piper1-gpl`), `pip install piper-tts`. Each
  voice has its own licence.
- Pitch and time: `pip install pyworld` (WORLD vocoder: replace F0 with the note,
  stretch the time axis) or `pip install praat-parselmouth` (PSOLA).

**Hybrid idea (untested).** Feed the formant-robot vocal stem to ACE-Step's
`cover-nofsq` task with a "female pop vocal" caption. It keeps timing and
melody better than plain `cover`. Whether it turns a robot into a singer is
unknown.

## 4. ROCm on gfx1152 (Radeon 860M) in late 2026

- **Official now.** ROCm 10.1.0 lists the Radeon 860M (gfx1152) and PyTorch
  2.14.0. AMD's install page has a per-device wheel extra:

  ```
  python -m pip install --index-url https://stable.repo.amd.com/rocm/whl-next/ \
    "torch[device-gfx1152]==2.14.0+rocm10.1.0" \
    "torchvision[device-gfx1152]==0.29.0a0+rocm10.1.0" \
    "torchaudio==2.11.0.3+rocm10.1.0"
  ```

  ROCm 7.14.x wheels (PyTorch 2.11/2.12) also list gfx1152. Python 3.10-3.14.
- **Field report.** ROCm/TheRock issue 9303 (October 2026): PyTorch
  2.14.0+rocm10.1.0 on an 860M, `torch.cuda.is_available()` is True, an FFT
  forward and backward pass runs. No speed numbers. JAX failed on gfx1152 in
  10.1.0; the fix is in the 10.2.0 nightlies from 20 Oct 2026.
- **HSA_OVERRIDE_GFX_VERSION** (for example `11.0.0`) was the 2025 workaround.
  It is no longer needed and can break PyTorch's AOTriton attention kernels,
  which pick code by architecture. Do not set it.
- **First run is slow.** A 7900 XT user saw 10-15 minutes of MIOpen kernel
  compilation on the first ACE-Step generation. Later runs use the cache.
- **Memory (guess).** The GPU has a 4 GiB carve-out and 14.5 GB GTT. Vulkan
  (RADV) uses GTT freely. Check `torch.cuda.mem_get_info()` under ROCm; if it
  only reports 4 GiB, raise the UMA size in the BIOS or stay on Vulkan.
- **openSUSE.** AMD lists no openSUSE support. The system already has ROCm 7.2
  packages. Keep the AMD wheels in a separate venv so they do not mix (guess).
  ACE-Step's Python code needs Python 3.11-3.12; `uv` fetches one.
- **Verdict.** Vulkan through GGML is the lowest-risk GPU path. ROCm PyTorch is
  worth one try for the official ACE-Step UI and LoRA training. CPU-only is a
  realistic fallback: ACE-Step at 15-30 minutes per song (guess), every
  singing-synthesis option in section 3 in minutes.

Official ACE-Step on ROCm (untested here):

```
git clone https://github.com/ACE-Step/ACE-Step-1.5.git && cd ACE-Step-1.5
uv sync
uv pip install --index-url https://stable.repo.amd.com/rocm/whl-next/ \
  "torch[device-gfx1152]==2.14.0+rocm10.1.0" "torchaudio==2.11.0.3+rocm10.1.0"
uv run --no-sync acestep      # Gradio UI on http://localhost:7860
```

For under 6 GB of GPU memory, the project says: 2B turbo, no LM, INT8, full
CPU offload. With 6-8 GB: 2B turbo plus the 0.6B LM. A `comfyui` checkout
exists in `~/Projects` without torch; AMD's own guide runs ACE-Step 1.5 through
ComfyUI (Strix Halo: about 1.8 times faster than real time).

## 5. Hosted alternatives to Suno

| Service | Status (Nov 2026) | Price | Downloads | Commercial use |
|---|---|---|---|---|
| Suno | v6 since 9 Sep 2026 | see `suno-tips.md` | Capped (Free about 7 total, Pro 20/month per earlier research) | Paid plans |
| **ACE Music v1** (acemusic.ai) | #1 on AA vocal board (Elo 1160 vs Suno v6 1144) | Free 20 credits/day (10 songs); Creator $7.90/mo annual, 1,000 credits (about 500 songs); Artist $16.58/mo annual | Free: none. Creator: unlimited | Creator and up |
| **Mureka** (Kunlun) | V9 (Mar 2026), V9.5 on AA board at #4 | Basic $8/mo, 400 songs; Pro $24/mo, 1,600 songs | Basic MP3; Pro WAV and stems | Yes from Basic. Training data undisclosed; litigation pending |
| **Google Flow Music** (was Riffusion / ProducerAI) | Bought Feb 2026, renamed Apr 2026, Lyria 3.5 since 29 Jul 2026 | Free daily credits; Starter $8 (about 600 songs), Plus $24, Member $64 per month | MP3, WAV, M4A, stems | Free tier reportedly non-commercial and watermarked (unverified) |
| Google Lyria API | Paid API key, no free tier | about $0.08 per song | Direct | Check API terms |
| **ElevenLabs Eleven Music** v2.5 | AA rank 8 | Starter $6/mo; higher tiers on the pricing page | Free: none. Starter: 17 min generated and 30 min downloaded per month. Creator: 62 / 250 min | All paid plans; streaming distribution only from Creator up |
| Udio | Downloads off since 29-30 Oct 2025; UMG platform not launched | n/a | None | n/a. Not usable for the compo |
| StepAudio 3 Music (StepFun) | Free preview API, up to 5:30 | Free for now | API output | Terms unclear |
| Sonauto | Review sites say free and unlimited | Unclear | Unclear | Not stated; assume no |

Most prices above come from third-party reviews. Check the pricing page on the
day. ElevenLabs numbers come from its own terms page.

## Sources

- ACE-Step 1.5 repo: https://github.com/ACE-Step/ACE-Step-1.5
- ACE-Step GPU tiers: https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/GPU_COMPATIBILITY.md
- ACE-Step 1.5 model card (MIT, commercial output): https://huggingface.co/ACE-Step/Ace-Step1.5
- ACE-Step 1.5 paper: https://arxiv.org/abs/2602.00744
- acestep.cpp: https://github.com/ServeurpersoCom/acestep.cpp
- acestep.cpp task docs (lego, cover, metadata): https://github.com/ServeurpersoCom/acestep.cpp/blob/master/docs/ARCHITECTURE.md
- ACE-Step GGUF weights: https://huggingface.co/Serveurperso/ACE-Step-1.5-GGUF
- AMD blog, ACE-Step 1.5 on Ryzen AI and Radeon: https://www.amd.com/en/blogs/2026/commercial-grade-ai-music-generation-on-amd-ryzen-ai-and-radeon-ace-step-1-5.html
- ACE-Step on RX 7900 XT, CPU vs GPU timings: https://github.com/ace-step/ACE-Step/discussions/404
- ACE-Step on Radeon 780M (summary in search result): https://note.com/samehadaonsen/n/n0dd053ba40c1
- YuE2-3B model card: https://huggingface.co/m-a-p/YuE2-3B
- YuE2 overview: https://comfyui-wiki.com/en/models/yue2
- YuE repo: https://github.com/multimodal-art-projection/YuE
- MiniMax Music 3 licence: https://mer.vin/news/minimax-music-3-is-open-weight-but-not-open-for-business/
- LeVo 2 / SongGeneration 2: https://gaga.art/blog/songgeneration-2/
- SongGeneration licence text (mirror): https://github.com/xzm2004260/SongGeneration/blob/main/LICENSE
- HeartMuLa: https://github.com/HeartMuLa/heartlib
- DiffRhythm 2: https://huggingface.co/ASLP-lab/DiffRhythm2
- SongBloom: https://huggingface.co/CypressYang/SongBloom
- Open-weights release list: https://theopenweights.com/categories/music
- Qwen-Music report: https://arxiv.org/abs/2607.11699
- StepAudio 3 Music: https://wavespeed.ai/blog/audio-and-voice-models/stepaudio-3-model-guide/
- AA-Music-Vocal leaderboard: https://artificialanalysis.ai/music/leaderboard/vocals
- ACE Music v1: https://www.orcarouter.ai/blog/ace-music-v1-tops-aa-music-vocal
- Stable Audio 3: https://the-decoder.com/stability-ai-launches-stable-audio-3-0-with-up-to-six-minute-tracks-and-open-weights/
- Stable Audio Open Small: https://stability.ai/news/stability-ai-and-arm-release-stable-audio-open-small-enabling-real-world-deployment-for-on-device-audio-control
- MusicGen licence: https://replicate.com/meta/musicgen/readme
- Magenta RealTime 2: https://magenta.tensorflow.org/mrt2
- Magenta RealTime 2 licence and release: https://mer.vin/2026/06/magenta-realtime-2-open-local-live-music-model-with-midi-and-200ms-latency/
- DEMON paper: https://arxiv.org/abs/2605.28657
- OpenUtau releases: https://github.com/openutau/OpenUtau/releases/tag/0.1.576
- DiffSinger: https://github.com/openvpi/DiffSinger
- DiffSingerMiniEngine: https://github.com/openvpi/DiffSingerMiniEngine
- OpenUtau DiffSinger integration: https://deepwiki.com/stakira/OpenUtau/4.2-diffsinger-integration
- Lotte V DiffSinger terms: https://lottev.moe/category/vocal-synth/diffsinger/
- Peiton DS terms: https://utaurepository.miraheze.org/wiki/Peiton
- SoulX-Singer: https://github.com/Soul-AILab/SoulX-Singer
- NNSVS install: https://nnsvs.github.io/installation.html
- NNSVS English status: https://www.github.com/intunist/nnsvs-english-support
- Kokoro: https://github.com/hexgrad/kokoro
- Piper (GPL): https://github.com/OHF-Voice/piper1-gpl
- ROCm 10.1.0 release notes: https://rocm.docs.amd.com/en/latest/about/release-notes.html
- PyTorch ROCm install: https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/frameworks/pytorch/install.html
- gfx1152 PyTorch/JAX report: https://github.com/ROCm/TheRock/issues/9303
- HSA_OVERRIDE caveats: https://localaimaster.com/blog/rocm-unsupported-gpu-hsa-override
- Udio downloads: https://music.loop.fans/ai/what-happened-to-udio
- ElevenLabs music terms: https://elevenlabs.io/eleven-music-model-specific-terms
- Mureka: https://invideo.io/blog/mureka-ai-music-generator/
- Flow Music: https://www.veena.studio/blog/google-flow-music
- Flow Music free tier: https://clipjury.pages.dev/reviews/riffusion
- Lyria API pricing: https://omcircle.ai/radar/ai-models/lyria-3
- Sonauto: https://sonauto.ai/developers/pricing
