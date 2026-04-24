import os
from moviepy.editor import VideoFileClip


def extract_audio(video_path: str, output_dir: str = "data/audio") -> str:
    """
    Extract audio from a video file and save it as a 16 kHz mono WAV.

    Why 16 kHz mono?  Whisper (used in transcription.py) was trained on
    16 kHz audio.  Giving it the correct sample rate avoids an internal
    resampling step and produces more accurate transcripts.

    Args:
        video_path:  Path to the input video (.mp4, .mkv, etc.)
        output_dir:  Folder where the WAV file will be saved

    Returns:
        Path to the extracted WAV file
    """
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join(output_dir, f"{base_name}.wav")

    print(f"[AudioExtractor] 🎵 Extracting audio from: {video_path}")

    with VideoFileClip(video_path) as clip:
        if clip.audio is None:
            raise ValueError("[AudioExtractor] ❌ This video has no audio track.")

        clip.audio.write_audiofile(
            audio_path,
            fps=16000,      # 16 kHz — Whisper's native sample rate
            nbytes=2,       # 16-bit PCM
            ffmpeg_params=["-ac", "1"],   # force mono
            verbose=False,
            logger=None,
        )

    size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"[AudioExtractor] ✅ Audio saved: {audio_path}  ({size_mb:.1f} MB)")
    return audio_path


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python audio_extractor.py <video_path>")
        sys.exit(1)

    out = extract_audio(sys.argv[1])
    print(f"Audio ready at: {out}")