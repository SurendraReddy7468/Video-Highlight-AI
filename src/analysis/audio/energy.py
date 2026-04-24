import librosa
import numpy as np


def compute_energy(audio_path: str, start: float, end: float) -> float:
    """
    Measure loudness (RMS energy) of an audio segment.
    Returns a normalized score between 0.0 and 1.0.

    Why energy matters: Loud, punchy moments in a podcast
    (emphasis, excitement, key points) score higher — these
    are exactly what makes a good highlight.
    """
    y, sr = librosa.load(audio_path, sr=None, offset=start, duration=end - start, mono=True)

    if len(y) == 0:
        return 0.0

    rms = librosa.feature.rms(y=y)[0]
    mean_rms = float(np.mean(rms))

    # Normalize: typical speech RMS sits between 0.01 and 0.15
    normalized = np.clip(mean_rms / 0.15, 0.0, 1.0)
    return round(float(normalized), 4)


if __name__ == "__main__":
    import sys
    score = compute_energy(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
    print(f"Energy score: {score}")