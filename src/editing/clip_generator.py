import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.video.fx.fadein  import fadein
from moviepy.video.fx.fadeout import fadeout

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
    FADE = 0.4   # seconds — crossfade duration

    faded = []
    for i, clip in enumerate(clips):
        c = clip
        if i > 0:                    # fade in on every clip except first
            c = fadein(c, FADE)
        if i < len(clips) - 1:       # fade out on every clip except last
            c = fadeout(c, FADE)
        faded.append(c)

    final = concatenate_videoclips(faded, method="compose")
    output_path = os.path.join(output_dir, f"{output_name}.mp4")

    print(f"[ClipGen] 🎬 Rendering final clip → {output_path}")
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",        # higher bitrate = sharper image
        audio_bitrate="192k",   # better audio quality
        verbose=False,
        logger=None,
    )

    video.close()
    final.close()

    print(f"[ClipGen] ✅ Done: {output_path}  ({total_secs:.1f}s)")
    return output_path

def generate_intro_clip(
    video_path: str,
    scored_segments: list,
    output_dir: str = "data/outputs/shorts",
    output_name: str = "intro_clip",
) -> str:
    """
    Generate a 15–25 second intro clip designed to hook viewers.

    Strategy:
      1. Pick the highest hook-scoring segment as the opener (first 3s grab attention)
      2. Add 1–2 more high-scoring teaser moments from later in the video
      3. Result: a preview that makes viewers want to watch the full video

    Different from 'shorts' mode — intro clips are designed to be
    placed at the START of a longer video or as a standalone teaser,
    not as a self-contained highlight.
    """
    os.makedirs(output_dir, exist_ok=True)

    MIN_DURATION = 15
    MAX_DURATION = 25

    # Sort by hook score first — intro needs the most attention-grabbing opener
    hook_sorted = sorted(scored_segments, key=lambda x: x.get("hook", 0), reverse=True)

    # Pick best hook as opener
    opener    = hook_sorted[0]
    selected  = [opener]
    total_sec = opener["end"] - opener["start"]

    print(f"[ClipGen] 🎣 Intro opener: [{opener['start']}s→{opener['end']}s]  "
          f"hook={opener.get('hook', 0):.3f}  {opener['text'][:50]}...")

    # Fill remaining time with high overall score segments (not the opener)
    remaining = [s for s in scored_segments if s["start"] != opener["start"]]
    remaining.sort(key=lambda x: x["score"], reverse=True)

    for seg in remaining:
        dur = seg["end"] - seg["start"]
        if total_sec + dur > MAX_DURATION:
            continue
        selected.append(seg)
        total_sec += dur
        if total_sec >= MIN_DURATION:
            break

    # Sort chronologically so the intro flows naturally through the video
    selected.sort(key=lambda x: x["start"])

    print(f"[ClipGen] 🎬 Intro: {len(selected)} segments ({total_sec:.1f}s)")
    for s in selected:
        print(f"          [{s['start']}s→{s['end']}s]  {s['text'][:50]}...")

    # Cut and join
    video  = VideoFileClip(video_path)
    clips  = []
    for seg in selected:
        start = max(0, seg["start"])
        end   = min(seg["end"], video.duration)
        clips.append(video.subclip(start, end))

    from moviepy.video.fx.fadein  import fadein
    from moviepy.video.fx.fadeout import fadeout
    FADE = 0.3
    faded = []
    for i, clip in enumerate(clips):
        c = clip
        if i > 0:              c = fadein(c, FADE)
        if i < len(clips) - 1: c = fadeout(c, FADE)
        faded.append(c)

    final       = concatenate_videoclips(faded, method="compose")
    output_path = os.path.join(output_dir, f"{output_name}.mp4")

    print(f"[ClipGen] 🎬 Rendering intro → {output_path}")
    final.write_videofile(output_path, codec="libx264", audio_codec="aac",
                          bitrate="8000k", audio_bitrate="192k",
                          verbose=False, logger=None)
    video.close()
    final.close()

    print(f"[ClipGen] ✅ Intro done: {output_path}  ({total_sec:.1f}s)")
    return output_path