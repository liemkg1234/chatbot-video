import subprocess
from pathlib import Path

DOWNLOAD_DIR = Path("/temp").resolve()
DOWNLOAD_DIR.mkdir(exist_ok=True)

def run_yt_dlp(args: list[str]) -> str:
    process = subprocess.run(
        ["yt-dlp", *args],
        cwd=DOWNLOAD_DIR,
        capture_output=True,
        text=True
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip())
    return process.stdout.strip()

def find_latest_file(extension: str) -> Path:
    files = sorted(DOWNLOAD_DIR.glob(f"*.{extension}"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"No {extension} file found")
    return files[0]

def download_video(url: str, quality: int = 720) -> str:
    run_yt_dlp([
        "-f", f"bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/best[ext=mp4][height<={quality}]",
        "--merge-output-format", "mp4",
        "-o", "%(title)s.%(ext)s",
        url
    ])
    return str(find_latest_file("mp4"))

def download_audio(url: str) -> str:
    run_yt_dlp([
        "-f", "bestaudio",
        "-x", "--audio-format", "mp3",
        "-o", "%(title)s.%(ext)s",
        url
    ])
    return str(find_latest_file("mp3"))

def download_subtitles(url: str, lang: str = "en") -> str:
    run_yt_dlp([
        "--write-auto-sub",
        "--sub-lang", lang,
        "--convert-subs", "srt",
        "--skip-download",
        "-o", "%(title)s.%(ext)s",
        url
    ])
    srt_file = find_latest_file("srt")
    return srt_file.read_text(encoding="utf-8")
