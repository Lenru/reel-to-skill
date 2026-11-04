# reel-to-skill

A Claude Code skill. Paste an Instagram reel, TikTok or YouTube link, and Claude reads what the video actually says, checks whether you already have the technique installed, and if you don't, builds it into a working Claude Code skill.

I built it because I save a lot of technique videos and never got round to reading them. Transcription runs on my own machine, so a video costs nothing to look at.

## The pipeline

```
link  →  yt-dlp (video + caption)  →  faster-whisper (transcript)  →  triage  →  skill-creator
```

1. **Download.** `yt-dlp` fetches the video and its metadata. Public posts need nothing else. If a download fails, it retries with cookies from Chrome, Edge, then Firefox, so private or age-gated posts work when you're logged in.
2. **Transcribe.** `ffmpeg` pulls the audio out as 16 kHz mono and `faster-whisper` transcribes it on the CPU. The script writes `caption.txt`, `transcript.txt` and `meta.json`, and deletes the video unless you pass `--keep-video`.
3. **Triage.** Claude compares the technique against the skills and MCP servers you already have and gives one verdict: build it, already have it, or skip. This is the step that saves the most time, because the honest answer is often "you have this already".
4. **Build.** If it's a real gap, the transcript, caption and source link go to Anthropic's `skill-creator` skill, which writes the new skill. The source link stays in the brief so you can trace where the skill came from.

The caption and the transcript are both kept on purpose. Creators tend to put the "what" (repo names, commands) in the caption and the "why" in what they say.

## Why transcribe locally

- **No API and no cost.** Whisper runs on your CPU. The model downloads once (a few hundred MB for the default `small`) and is cached after that.
- **Private.** The audio never leaves your machine. Only the text goes into your Claude Code session.
- **No keys to manage.** Nothing to sign up for, nothing to leak.

## Example

This is an illustrative example written for this README, not output from a real run. The URL and names are made up.

You paste:

```
https://www.instagram.com/reel/EXAMPLE123/  build this
```

The script prints what it found:

```
=== /tmp/reel-git-hooks ===
author: some_creator

--- caption ---
Stop committing broken code. One pre-commit hook that runs your tests ...

--- transcript ---
So the trick here is a hook that runs before every commit ...
```

Claude triages it ("Build it: you have no pre-commit hook skill") and hands it to `skill-creator`, which leaves a new skill on disk:

```
~/.claude/skills/pre-commit-tests/
  SKILL.md        when to use it, the steps, source: the reel URL + author
  scripts/...     whatever the technique needs
```

A real triage from using it: a reel pitching the `blader/humanizer` skill came back as "already installed, and your global CLAUDE.md already says to run it". Nothing was rebuilt.

## Install

You need Python 3.9 or newer, `ffmpeg` on your PATH, and [Claude Code](https://claude.com/claude-code). `skill-creator` is used for the build step.

```bash
# 1. ffmpeg (pick one)
winget install Gyan.FFmpeg     # Windows
brew install ffmpeg           # macOS
sudo apt install ffmpeg       # Debian / Ubuntu

# 2. yt-dlp and faster-whisper
pip install -r requirements.txt

# 3. drop the skill in
git clone <this repo> ~/.claude/skills/reel-to-skill
```

On Windows, `~/.claude/skills` is `%USERPROFILE%\.claude\skills`. Claude Code picks the skill up on its next session. Then paste a video link into Claude Code.

To run the download and transcription step on its own:

```bash
python scripts/rip.py "<url>" --out ./reel-out --model small
```

`--model` takes `tiny`, `base`, `small`, `medium` or `large-v3`. Bigger is more accurate and slower.

## Tests

```bash
python -m unittest discover -s tests
```

These cover the metadata handling only, with no network and no model. The download and transcription steps are thin calls to `yt-dlp`, `ffmpeg` and `faster-whisper`.

## Provenance

Taken out of the Claude Code setup I run day to day, with its git history kept as it was. The last commit removes the paths and names specific to my machine so it runs anywhere.

MIT licensed.
