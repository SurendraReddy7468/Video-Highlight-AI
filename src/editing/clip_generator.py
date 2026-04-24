import os
from moviepy.editor import VideoFileClip, concatenate_videoclips


def generate_clip(
    video_path: str,
    scored_segments: list,
    mode: str = "shorts",
    output_dir: str = None,
    output_name: str = "final_clip",
) -> str:
    """
    Cut and join the highest-scoring segments into a final clip.

    Mode controls how many seconds of content to select:
      shorts     → 30–60 seconds  (vertical 9:16 after format_converter)
      highlights → 60–180 seconds (horizontal 16:9)

    Args:
        video_path:       Original video file
        scored_segments:  List from highlight_score.py (sorted best-first)
        mode:             'shorts' or 'highlights'
        output_dir:       Where to save (auto-set from mode if None)
        output_name:      Output filename without extension

    Returns:
        Path to the generated clip
    """
    # Target durations in seconds
    targets = {
        "shorts":     {"min": 30,  "max": 60},
        "highlights": {"min": 60,  "max": 180},
    }
    target = targets.get(mode, targets["shorts"])

    if output_dir is None:
        output_dir = f"data/outputs/{mode}s" if mode == "short" else f"data/outputs/{mode}"
    os.makedirs(output_dir, exist_ok=True)

    # ── Select segments greedily until we hit target duration ──
    selected   = []
    total_secs = 0.0

    for seg in scored_segments:
        seg_duration = seg["end"] - seg["start"]
        if total_secs + seg_duration > target["max"]:
            continue   # skip if it would push us over the max
        selected.append(seg)
        total_secs += seg_duration
        if total_secs >= target["min"]:
            break      # we have enough

    if not selected:
        raise ValueError(f"[ClipGen] ❌ No segments selected. Check scored_segments.")

    # Sort selected segments back into chronological order
    selected.sort(key=lambda x: x["start"])

    print(f"[ClipGen] ✂️  Selected {len(selected)} segments ({total_secs:.1f}s total)")
    for s in selected:
        print(f"          [{s['start']}s → {s['end']}s]  score={s['score']}  {s['text'][:45]}...")

    # ── Cut and join clips ──────────────────────────────────────
    video  = VideoFileClip(video_path)
    clips  = []

    for seg in selected:
        # Clamp timestamps to video duration
        start = max(0, seg["start"])
        end   = min(seg["end"], video.duration)
        clip  = video.subclip(start, end)
        clips.append(clip)

    final      = concatenate_videoclips(clips, method="compose")
    output_path = os.path.join(output_dir, f"{output_name}.mp4")

    print(f"[ClipGen] 🎬 Rendering final clip → {output_path}")
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        verbose=False,
        logger=None,
    )

    video.close()
    final.close()

    print(f"[ClipGen] ✅ Done: {output_path}  ({total_secs:.1f}s)")
    return output_path