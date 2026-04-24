import os
import subprocess

def load_from_local(video_path: str) -> str:
    """Validate and return path to a local video file."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"[VideoLoader] ❌ File not found: {video_path}")
    print(f"[VideoLoader] ✅ Local file found: {video_path}")
    return video_path


def load_from_youtube(url: str, output_dir: str = "data/raw_videos") -> str:
    """Download a YouTube video using yt-dlp."""
    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    print(f"[VideoLoader] ⬇️  Downloading: {url}")

    # Download the video
    result = subprocess.run(
        [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "--merge-output-format", "mp4",
            "-o", output_template,
            url,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"[VideoLoader] ❌ yt-dlp failed:\n{result.stderr}")

    # Ask yt-dlp what filename it would produce (without downloading again)
    filename_result = subprocess.run(
        ["yt-dlp", "--get-filename", "-o", output_template, url],
        capture_output=True,
        text=True,
    )
    downloaded_path = filename_result.stdout.strip()

    # yt-dlp may add .mp4 even if the template says otherwise
    if not os.path.exists(downloaded_path):
        # fallback: grab the most recently modified mp4 in output_dir
        mp4s = sorted(
            [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".mp4")],
            key=os.path.getmtime,
            reverse=True,
        )
        if not mp4s:
            raise FileNotFoundError("[VideoLoader] ❌ Download finished but no .mp4 found.")
        downloaded_path = mp4s[0]

    print(f"[VideoLoader] ✅ Downloaded: {downloaded_path}")
    return downloaded_path


def load_video(source: str, output_dir: str = "data/raw_videos") -> str:
    """
    Auto-detect whether source is a YouTube URL or a local file path.

    Args:
        source: YouTube URL (http/https) or local file path
        output_dir: Where to save downloaded videos

    Returns:
        Absolute or relative path to the video file
    """
    if source.startswith("http://") or source.startswith("https://"):
        return load_from_youtube(source, output_dir)
    else:
        return load_from_local(source)


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python video_loader.py <path_or_url>")
        sys.exit(1)

    path = load_video(sys.argv[1])
    print(f"Video ready at: {path}")