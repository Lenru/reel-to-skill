---
name: reel-to-skill
description: Turn a social video link into a working Claude Code skill. Use this whenever Noah pastes an Instagram reel, TikTok, YouTube video or Short and wants the technique in it captured, built, tried, or explained - including phrasings like "build this", "can you do this", "make this a skill", "look at this reel", "here's a video, set it up", "steal this workflow", or when he just drops a link with no instruction at all. Also use it to read what a video actually says before deciding whether the technique is worth building. Downloads and transcribes locally with yt-dlp plus faster-whisper (no API, no cost), then hands the transcript to skill-creator.
---

# Reel to skill

Noah saves a lot of technique videos, mostly from `jens.heitmann`. Reading them
one at a time by hand is the bottleneck this removes. Paste a link, get either a
working skill or an honest "you already have this".

## The pipeline

```
link  →  yt-dlp (video + caption)  →  faster-whisper (transcript)  →  triage  →  skill-creator
```

Everything up to triage runs locally and costs nothing.

## 1. Rip it

```powershell
& "C:\Users\me\AppData\Local\Programs\Python\Python312\python.exe" `
  "C:\Users\me\.claude\skills\reel-to-skill\scripts\rip.py" "<url>" `
  --out "$env:TEMP\reel-<slug>"
```

Use that specific Python. The generic `python` on this machine points at a
hermes venv that does not have `faster-whisper`.

The script prints the caption and transcript straight to the terminal and writes
`caption.txt`, `transcript.txt` and `meta.json` to the out directory. The caption
usually names the exact repos and tools; the transcript carries the reasoning. You
need both, because these creators put the "what" on screen and the "why" in the audio.

**Instagram note:** public reels download fine. If one fails, the script retries
with browser cookies automatically. If every attempt fails, fall back to the
Playwright MCP: navigate to the reel URL (the profile is logged in as
`watsonsmedia`), snapshot, and read the caption out of the snapshot yml. That
gets you the caption but not the spoken audio, which is usually enough to triage.

**First run downloads the Whisper model** (a few hundred MB for `small`), then it
is cached. Say so before running rather than letting Noah watch a silent pause.

## 2. Triage before you build

This is the step that earns its keep. Noah owns a large and partly unused
toolchain, so the most valuable answer is often "you already have this."

Check the transcript's technique against what is installed before proposing anything:

- `Get-ChildItem C:\Users\me\.claude\skills -Directory` for the skill list
- the connected MCP servers for capability that is already wired

Then give a verdict per video, in one line each:

- **Build it** - real gap, name what it unblocks
- **Already have it** - name the skill or MCP that covers it, and why he didn't
  reach for it
- **Skip** - works, but it is a thinner version of something he already runs

Real example: a reel pitching `blader/humanizer` triaged to "already installed,
and your global CLAUDE.md already mandates running it." That saved a rebuild.

## 3. Build it

Hand the transcript plus caption to `skill-creator`. Give it the source link and
author in the brief so provenance survives.

Two things to carry over that these videos rarely spell out:

- **Check the upstream repo actually runs on Windows 10 / PowerShell 5.1 before
  promising it works.** Most of these creators are on macOS. `make`, `brew`,
  `head`, and Remotion-in-WSL all fail on this machine. Test the real commands.
- **Prefer wrapping the upstream repo over reimplementing it.** A skill that
  clones and drives someone else's working tool is smaller and stays current.

Skip skill-creator's full eval harness unless Noah asks. It spawns many
subagents; for a single-technique skill the cost outweighs the signal.

## 4. Close the loop

Tell Noah what got built and what the first real job for it is. A skill that
never runs is the same failure mode as the dashboard he stopped opening.
