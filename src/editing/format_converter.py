import os
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip


def convert_to_vertical(input_path: str, output_path: str = None,
                         face_center_x: float = 0.5,
                         per_segment_faces: list = None) -> str:
    """
    Convert to 9:16 vertical (1080x1920) with per-segment face-aware cropping.

    per_segment_faces: list of (start_sec, end_sec, face_center_x)
        Each segment of the clip gets its own crop position based on
        where the speaker's face was detected in that segment.
        This correctly handles two-speaker videos where speakers sit
        at different positions in the frame.

    face_center_x: fallback single crop position if per_segment_faces is None
    """
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_vertical.mp4"

    print(f"[FormatConverter] 📱 Converting to vertical 9:16 ...")

    clip         = VideoFileClip(input_path)
    target_w     = 1080
    target_h     = 1920
    target_ratio = target_w / target_h
    orig_w, orig_h = clip.size
    crop_w = min(int(orig_h * target_ratio), orig_w)

    def get_crop_x(fx):
        """Blend face position toward center, clamp to valid range."""
        blended = 0.7 * fx + 0.3 * 0.5
        ideal   = int(blended * orig_w - crop_w / 2)
        return max(0, min(ideal, orig_w - crop_w))

    if per_segment_faces and len(per_segment_faces) > 1:
        # ── Per-segment cropping (multi-speaker or changing position) ──────
        from moviepy.editor import concatenate_videoclips
        from moviepy.video.fx.fadein  import fadein
        from moviepy.video.fx.fadeout import fadeout

        sub_clips = []
        total_dur = clip.duration

        for i, (seg_start, seg_end, face_x) in enumerate(per_segment_faces):
            # Clamp to clip duration
            seg_start = max(0.0, seg_start)
            seg_end   = min(seg_end, total_dur)
            if seg_end <= seg_start:
                continue

            x1      = get_crop_x(face_x)
            seg     = clip.subclip(seg_start, seg_end)
            cropped = seg.crop(x1=x1, x2=x1 + crop_w)
            resized = cropped.resize((target_w, target_h))

            # Smooth fade between different crop positions
            if i > 0:
                resized = fadein(resized, 0.35)
            if i < len(per_segment_faces) - 1:
                resized = fadeout(resized, 0.35)

            sub_clips.append(resized)
            print(f"[FormatConverter]   Seg {i+1}: "
                  f"[{seg_start:.1f}s-{seg_end:.1f}s] "
                  f"face_x={face_x:.3f} → crop_x1={x1}px")

        if not sub_clips:
            # Fallback
            x1      = get_crop_x(face_center_x)
            cropped = clip.crop(x1=x1, x2=x1 + crop_w)
            final   = cropped.resize((target_w, target_h))
        else:
            final = concatenate_videoclips(sub_clips, method="compose")

    else:
        # ── Single crop for whole clip ──────────────────────────────────────
        x1      = get_crop_x(face_center_x)
        cropped = clip.crop(x1=x1, x2=x1 + crop_w)
        final   = cropped.resize((target_w, target_h))
        print(f"[FormatConverter]   Single crop: face_x={face_center_x:.3f} → x1={x1}px")

    final.write_videofile(
        output_path,
        codec="libx264", audio_codec="aac",
        bitrate="8000k", audio_bitrate="192k",
        verbose=False, logger=None,
    )
    clip.close()
    print(f"[FormatConverter] ✅ Vertical clip saved: {output_path}")
    return output_path


def convert_to_horizontal(input_path: str, output_path: str = None) -> str:
    """
    Ensure clip is proper 16:9 horizontal (1920x1080) for highlights.
    Adds black bars (letterbox) if needed — never distorts the image.
    """
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_horizontal.mp4"

    print(f"[FormatConverter] 🖥️  Converting to horizontal 16:9 ...")

    clip         = VideoFileClip(input_path)
    target_w     = 1920
    target_h     = 1080
    target_ratio = target_w / target_h   # 1.777...

    orig_w, orig_h = clip.size
    orig_ratio     = orig_w / orig_h

    # Scale to fit within 1920x1080
    if orig_ratio >= target_ratio:
        scale = target_w / orig_w
    else:
        scale = target_h / orig_h

    new_w    = int(orig_w * scale)
    new_h    = int(orig_h * scale)
    resized  = clip.resize((new_w, new_h))

    # Pad with black bars to reach exactly 1920x1080
    background = ColorClip(size=(target_w, target_h), color=[0, 0, 0], duration=clip.duration)
    x_offset   = (target_w - new_w) // 2
    y_offset   = (target_h - new_h) // 2
    final      = CompositeVideoClip([background, resized.set_position((x_offset, y_offset))])

    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",        # higher bitrate = sharper image
        audio_bitrate="192k",   # better audio quality
        verbose=False,
        logger=None,
    )

    clip.close()
    print(f"[FormatConverter] ✅ Horizontal clip saved: {output_path}")
    return output_path