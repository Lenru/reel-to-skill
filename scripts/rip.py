#!/usr/bin/env python3
"""Rip a social video (Instagram / YouTube / TikTok) down to text.

Downloads the video, pulls the caption/description out of yt-dlp's metadata,
transcribes the audio locally with faster-whisper, and writes everything into
one folder. Nothing here talks to an API or costs money.

Usage:
    python rip.py <url> [--out DIR] [--model small] [--keep-video]

Writes into DIR (default: a temp folder printed at the end):
    caption.txt     the post's own caption / description, plus author + title
    transcript.txt  what is actually said in the video
    meta.json       url, author, title, duration, and both text blobs together
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ponytail: chrome cookies are the fallback, not the default. Public reels
# usually download fine without them; private/age-gated ones need the browser
# session. Trying bare first keeps the common case from prompting for a
# locked browser profile.
COOKIE_BROWSERS = ("chrome", "edge", "firefox")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def download(url: str, workdir: Path) -> Path:
    """Fetch the video + its metadata json. Returns the video path."""
    base = ["yt-dlp", "--no-playlist", "--write-info-json",
            "-f", "mp4/bestvideo*+bestaudio/best",
            "-o", str(workdir / "source.%(ext)s"), url]

    attempts = [base] + [base + ["--cookies-from-browser", b] for b in COOKIE_BROWSERS]
    last = None
    for cmd in attempts:
        last = run(cmd)
        vids = [p for p in workdir.iterdir()
                if p.stem == "source" and p.suffix not in (".json",)]
        if vids:
            return vids[0]
    sys.exit(f"yt-dlp could not fetch {url}\n{(last.stderr or '')[-1500:]}")


def read_meta(workdir: Path) -> dict:
    info = next(workdir.glob("*.info.json"), None)
    if not info:
        return {}
    return json.loads(info.read_text(encoding="utf-8", errors="replace"))


def describe(meta: dict) -> tuple:
    """(author, title, caption) from yt-dlp metadata. Instagram fills
    `uploader`, YouTube sometimes only `channel`, and any field can be null."""
    author = meta.get("uploader") or meta.get("channel") or ""
    title = (meta.get("title") or "").strip()
    caption = (meta.get("description") or "").strip()
    return author, title, caption


def transcribe(video: Path, workdir: Path, model_size: str) -> str:
    """Local Whisper. Downloads the model once on first run, then it is cached."""
    wav = workdir / "audio.wav"
    r = run(["ffmpeg", "-y", "-i", str(video), "-vn",
             "-ac", "1", "-ar", "16000", str(wav)])
    if not wav.exists():
        sys.exit(f"ffmpeg failed to extract audio\n{(r.stderr or '')[-1000:]}")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper is not installed. Run: pip install faster-whisper")

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(wav), vad_filter=True)
    return " ".join(s.text.strip() for s in segments).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("url")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--model", default="small",
                    help="whisper size: tiny/base/small/medium/large-v3. "
                         "small is the sweet spot for talking-head reels.")
    ap.add_argument("--keep-video", action="store_true")
    args = ap.parse_args()

    out = args.out or Path(tempfile.mkdtemp(prefix="reel-"))
    out.mkdir(parents=True, exist_ok=True)

    # Captions are full of emoji, and a Windows console codepage raises on
    # them. Replace what it cannot show; the files on disk stay UTF-8.
    sys.stdout.reconfigure(errors="replace")

    video = download(args.url, out)
    meta = read_meta(out)
    author, title, caption = describe(meta)

    transcript = transcribe(video, out, args.model)

    (out / "caption.txt").write_text(
        f"author: {author}\ntitle: {title}\n\n{caption}\n",
        encoding="utf-8")
    (out / "transcript.txt").write_text(transcript + "\n", encoding="utf-8")
    (out / "meta.json").write_text(json.dumps({
        "url": args.url, "author": author, "title": title,
        "duration_seconds": meta.get("duration"),
        "caption": caption, "transcript": transcript,
    }, indent=2), encoding="utf-8")

    if not args.keep_video:
        for p in (out / "audio.wav", video):
            p.unlink(missing_ok=True)

    print(f"\n=== {out} ===")
    print(f"author: {author}")
    print(f"\n--- caption ---\n{caption[:2000]}")
    print(f"\n--- transcript ---\n{transcript[:4000]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
