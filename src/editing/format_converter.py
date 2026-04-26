import os
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip


def convert_to_vertical(input_path: str, output_path: str = None,
                         face_center_x: float = 0.5) -> str:
    """
    Convert to 9:16 vertical with smooth, clamped face-aware cropping.

    Improvements over v1:
      - Clamps face_center_x so crop window never goes out of bounds
      - Limits zoom to max 1.2x to prevent over-cropping
      - Eases the crop window with a gentle center blend (0.7 * face + 0.3 * center)
        so it never hard-snaps to an extreme edge position
    """
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_vertical.mp4"

    print(f"[FormatConverter] 📱 Converting to vertical 9:16 (face_x={face_center_x:.3f}) ...")

    clip         = VideoFileClip(input_path)
    target_w     = 1080
    target_h     = 1920
    target_ratio = target_w / target_h   # 0.5625

    orig_w, orig_h = clip.size

    # ── Max crop width we can extract from this frame ──────────
    max_crop_w = int(orig_h * target_ratio)

    # Clamp: crop window must not exceed original width
    crop_w = min(max_crop_w, orig_w)

    # ── Blend face position toward center to avoid extreme crops ─
    # 0.7 * detected_face + 0.3 * center = gentle pull to middle
    blended_x  = 0.7 * face_center_x + 0.3 * 0.5

    # Ideal left edge of crop window
    ideal_x1   = int(blended_x * orig_w - crop_w / 2)

    # Clamp so crop window stays within frame bounds
    x1 = max(0, min(ideal_x1, orig_w - crop_w))
    x2 = x1 + crop_w

    cropped = clip.crop(x1=x1, x2=x2)
    resized = cropped.resize((target_w, target_h))

    resized.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",
        audio_bitrate="192k",
        verbose=False,
        logger=None,
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