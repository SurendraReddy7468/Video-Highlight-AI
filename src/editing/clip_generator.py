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
    Generate a 25–30 second intro clip designed to hook viewers.

    Strategy:
      1. Opener  → highest hook score from FIRST 25% of video only
      2. Teaser  → 1–2 high-scoring segments from middle 25–75% of video
      3. All segments in chronological order for natural narrative flow
    """
    import re
    os.makedirs(output_dir, exist_ok=True)

    MIN_DURATION = 25
    MAX_DURATION = 40
    FADE         = 0.6   # longer fade = more polished

    # Get total video duration for position filtering
    probe = VideoFileClip(video_path)
    video_duration = probe.duration
    probe.close()

    early_cutoff  = video_duration * 0.25   # first 25%
    middle_cutoff = video_duration * 0.75   # up to 75%

    # ── Opener: best hook from early video only ───────────────
    # NEW — only consider segments longer than 10 seconds
    early_segs = [s for s in scored_segments 
                if s["start"] < early_cutoff 
                and (s["end"] - s["start"]) >= 10.0]
    if not early_segs:
        early_segs = scored_segments[:3]   # fallback

    def intro_score(seg):
        length_bonus = min((seg["end"] - seg["start"]) / 15.0, 1.0)
        return (seg.get("hook", 0) * 0.5 +
                length_bonus           * 0.3 +
                seg.get("score", 0)    * 0.2)

    opener = max(early_segs, key=intro_score)
    selected = [opener]
    total_sec = opener["end"] - opener["start"]

    print(f"[ClipGen] 🎣 Intro opener (from first {early_cutoff:.0f}s): "
          f"[{opener['start']}s→{opener['end']}s]  "
          f"hook={opener.get('hook',0):.3f}  {opener['text'][:50]}...")

    # ── Teasers: high-score segments from middle of video ─────
    middle_segs = [
        s for s in scored_segments
        if early_cutoff <= s["start"] <= middle_cutoff
        and s["start"] != opener["start"]
        and (s["end"] - s["start"]) >= 10.0
    ]
    middle_segs.sort(key=intro_score, reverse=True)

    for seg in middle_segs:
        dur = seg["end"] - seg["start"]
        if total_sec + dur > MAX_DURATION:
            continue
        selected.append(seg)
        total_sec += dur
        print(f"[ClipGen]   + teaser [{seg['start']}s→{seg['end']}s]  "
              f"score={seg['score']:.3f}  {seg['text'][:45]}...")
        if total_sec >= MIN_DURATION:
            break

    # Sort chronologically for natural narrative flow
    selected.sort(key=lambda x: x["start"])

    print(f"[ClipGen] 🎬 Intro: {len(selected)} segments ({total_sec:.1f}s)")

    # ── Cut and join with smooth fades ────────────────────────
    video = VideoFileClip(video_path)
    clips = []
    for seg in selected:
        start = max(0, seg["start"])
        end   = min(seg["end"], video.duration)
        clips.append(video.subclip(start, end))

    from moviepy.video.fx.fadein  import fadein
    from moviepy.video.fx.fadeout import fadeout

    faded = []
    for i, clip in enumerate(clips):
        c = clip
        if i > 0:
            c = fadein(c, FADE)
        if i < len(clips) - 1:
            c = fadeout(c, FADE)
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