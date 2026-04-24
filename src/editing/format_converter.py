import os
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip


def convert_to_vertical(input_path: str, output_path: str = None) -> str:
    """
    Convert a 16:9 horizontal clip to 9:16 vertical (for Shorts/Reels).

    Strategy: crop the center of the frame — this keeps the speaker's
    face in frame for most talking-head podcast videos.

    Output resolution: 1080 x 1920 (standard Shorts resolution)
    """
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_vertical.mp4"

    print(f"[FormatConverter] 📱 Converting to vertical 9:16 ...")

    clip         = VideoFileClip(input_path)
    target_w     = 1080
    target_h     = 1920
    target_ratio = target_w / target_h   # 0.5625

    orig_w, orig_h = clip.size
    orig_ratio     = orig_w / orig_h

    if orig_ratio > target_ratio:
        # Video is wider than 9:16 — crop sides
        new_w  = int(orig_h * target_ratio)
        x1     = (orig_w - new_w) // 2
        cropped = clip.crop(x1=x1, x2=x1 + new_w)
    else:
        # Video is taller than 9:16 — crop top/bottom
        new_h  = int(orig_w / target_ratio)
        y1     = (orig_h - new_h) // 2
        cropped = clip.crop(y1=y1, y2=y1 + new_h)

    resized = cropped.resize((target_w, target_h))

    resized.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
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
        verbose=False,
        logger=None,
    )

    clip.close()
    print(f"[FormatConverter] ✅ Horizontal clip saved: {output_path}")
    return output_path