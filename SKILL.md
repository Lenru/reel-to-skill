---
name: reel-to-skill
description: Turn a social video link into a working Claude Code skill. Use this whenever the user pastes an Instagram reel, TikTok, YouTube video or Short and wants the technique in it captured, built, tried, or explained - including phrasings like "build this", "can you do this", "make this a skill", "look at this reel", "here's a video, set it up", "steal this workflow", or when they just drop a link with no instruction at all. Also use it to read what a video actually says before deciding whether the technique is worth building. Downloads and transcribes locally with yt-dlp plus faster-whisper (no API, no cost), then hands the transcript to skill-creator.
---

# Reel to skill

People save a lot of technique videos. Reading them one at a time by hand is the
bottleneck this removes. Paste a link, get either a working skill or an honest
"you already have this".

## The pipeline

```
link  →  yt-dlp (video + caption)  →  faster-whisper (transcript)  →  triage  →  skill-creator
```

Everything up to triage runs locally and costs nothing.

## 1. Rip it

```bash
python ~/.claude/skills/reel-to-skill/scripts/rip.py "<url>" --out <temp dir>/reel-<slug>
```

On Windows use `py` or the full path to your Python if `python` is not on PATH.
Use the interpreter that has `faster-whisper` installed: if `python` resolves to
a different venv, the script stops and says so.

The script prints the caption and transcript straight to the terminal and writes
`caption.txt`, `transcript.txt` and `meta.json` to the out directory. The caption
usually names the exact repos and tools; the transcript carries the reasoning. You
need both, because these creators put the "what" on screen and the "why" in the audio.

**Instagram note:** public reels download fine. If one fails, the script retries
with browser cookies automatically. If every attempt fails, fall back to a
browser tool such as the Playwright MCP: navigate to the reel URL in a profile
that is logged in to Instagram, snapshot, and read the caption out of the
snapshot. That gets you the caption but not the spoken audio, which is usually
enough to triage.

**First run downloads the Whisper model** (a few hundred MB for `small`), then it
is cached. Say so before running rather than letting the user watch a silent pause.

## 2. Triage before you build

This is the step that earns its keep. Most people own a large and partly unused
toolchain, so the most valuable answer is often "you already have this."

Check the transcript's technique against what is installed before proposing anything:

- the folders in `~/.claude/skills/` for the skill list
- the connected MCP servers for capability that is already wired

Then give a verdict per video, in one line each:

- **Build it** - real gap, name what it unblocks
- **Already have it** - name the skill or MCP that covers it, and why the user
  didn't reach for it
- **Skip** - works, but it is a thinner version of something they already run

Real example: a reel pitching `blader/humanizer` triaged to "already installed,
and your global CLAUDE.md already mandates running it." That saved a rebuild.

## 3. Build it

Hand the transcript plus caption to `skill-creator`. Give it the source link and
author in the brief so provenance survives.

Two things to carry over that these videos rarely spell out:

- **Check the upstream repo actually runs on the user's OS before promising it
  works.** Most of these creators are on macOS. On Windows, `make`, `brew` and
  `head` are usually missing and WSL-only tools fail. Test the real commands.
- **Prefer wrapping the upstream repo over reimplementing it.** A skill that
  clones and drives someone else's working tool is smaller and stays current.

Skip skill-creator's full eval harness unless the user asks. It spawns many
subagents; for a single-technique skill the cost outweighs the signal.

## 4. Close the loop

Tell the user what got built and what the first real job for it is. A skill that
never runs is as useless as a dashboard nobody opens.
