import cv2
import numpy as np


# OpenCV's built-in face detector — no extra downloads needed
FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def compute_face_score(video_path: str, start: float, end: float,
                       sample_every: float = 1.0) -> dict:
    """
    Detect face presence and position in a video segment.

    Returns a dict with:
      score      → 0.0–1.0  (how consistently a face is visible)
      center_x   → 0.0–1.0  (average horizontal face center, 0.5 = middle)
      center_y   → 0.0–1.0  (average vertical face center, 0.5 = middle)

    Why this matters:
      score    → segments WITH a face score higher (speaker = more engaging)
      center_x/y → used by format_converter to crop around the face
                   instead of blindly cropping the frame center

    Args:
        video_path:    Path to the original video
        start:         Segment start time in seconds
        end:           Segment end time in seconds
        sample_every:  Sample one frame every N seconds (default: 1.0)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"score": 0.5, "center_x": 0.5, "center_y": 0.5}

    fps          = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 30
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_fps    = cap.get(cv2.CAP_PROP_FPS) or 30

    face_detected  = []
    face_centers_x = []
    face_centers_y = []

    current_time = start
    while current_time < end:
        # Seek to the frame at current_time
        frame_num = int(current_time * video_fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()

        if not ret:
            break

        # Convert to grayscale for face detection
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w  = gray.shape

        faces = FACE_CASCADE.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )

        if len(faces) > 0:
            face_detected.append(1)
            # Use the largest face found
            largest = max(faces, key=lambda f: f[2] * f[3])
            x, y, fw, fh = largest
            face_centers_x.append((x + fw / 2) / w)
            face_centers_y.append((y + fh / 2) / h)
        else:
            face_detected.append(0)

        current_time += sample_every

    cap.release()

    if not face_detected:
        return {"score": 0.5, "center_x": 0.5, "center_y": 0.5}

    score    = round(sum(face_detected) / len(face_detected), 4)
    center_x = round(float(np.mean(face_centers_x)) if face_centers_x else 0.5, 4)
    center_y = round(float(np.mean(face_centers_y)) if face_centers_y else 0.5, 4)

    return {"score": score, "center_x": center_x, "center_y": center_y}


if __name__ == "__main__":
    import sys
    result = compute_face_score(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
    print(f"Face score:  {result['score']}")
    print(f"Face center: x={result['center_x']}  y={result['center_y']}")