import cv2
import numpy as np


def compute_scene_change_score(video_path: str, start: float, end: float,
                                threshold: float = 30.0) -> float:
    """
    Detect scene changes (camera cuts) in a video segment.

    Returns a score between 0.0 and 1.0.

    Why scene changes matter: Camera cuts in podcasts signal
    deliberate editing — the original creator already marked
    these as important moments worth cutting to.

    Scoring:
      0 cuts   → 0.3  (static single shot — neutral)
      1–2 cuts → 0.6  (some visual variety)
      3+ cuts  → 0.9  (highly edited = high energy moment)

    Args:
        video_path:  Path to original video
        start:       Segment start in seconds
        end:         Segment end in seconds
        threshold:   Mean pixel difference to count as a scene cut (default 30)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.5

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30

    # Seek to start frame
    start_frame = int(start * video_fps)
    end_frame   = int(end   * video_fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    prev_frame  = None
    scene_cuts  = 0
    frame_count = 0

    while True:
        current_frame_num = cap.get(cv2.CAP_PROP_POS_FRAMES)
        if current_frame_num >= end_frame:
            break

        ret, frame = cap.read()
        if not ret:
            break

        # Downsample for speed — we only need rough pixel differences
        small = cv2.resize(frame, (160, 90))
        gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        if prev_frame is not None:
            diff = cv2.absdiff(gray, prev_frame)
            mean_diff = float(np.mean(diff))

            if mean_diff > threshold:
                scene_cuts += 1

        prev_frame   = gray
        frame_count += 1

    cap.release()

    if frame_count == 0:
        return 0.5

    # Normalize cut count to 0–1 score
    if scene_cuts == 0:
        return 0.3       # static shot
    elif scene_cuts <= 2:
        return 0.6
    elif scene_cuts <= 5:
        return 0.8
    else:
        return 0.9       # heavily edited segment


if __name__ == "__main__":
    import sys
    score = compute_scene_change_score(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
    print(f"Scene change score: {score}")