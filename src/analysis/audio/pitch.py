import librosa
import numpy as np


def compute_pitch_variation(audio_path: str, start: float, end: float) -> float:
    """
    Measure voice pitch variation (excitement/expressiveness).
    Returns a normalized score between 0.0 and 1.0.

    Why pitch variation matters: A monotone speaker scores low.
    An excited, expressive speaker has high pitch variation —
    a strong signal that this moment is engaging.
    """
    y, sr = librosa.load(audio_path, sr=None, offset=start, duration=end - start, mono=True)

    if len(y) == 0:
        return 0.0

    # Extract fundamental frequency (F0)
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),   # ~65 Hz  — lowest human voice
        fmax=librosa.note_to_hz("C7"),   # ~2093 Hz — highest human voice
        sr=sr,
    )

    # Keep only voiced frames (ignore silence/unvoiced)
    voiced_f0 = f0[voiced_flag] if voiced_flag is not None else f0[~np.isnan(f0)]
    voiced_f0 = voiced_f0[~np.isnan(voiced_f0)]

    if len(voiced_f0) < 5:
        return 0.0   # too little speech detected

    # Coefficient of variation: std/mean — measures relative variation
    variation = float(np.std(voiced_f0) / (np.mean(voiced_f0) + 1e-6))

    # Normalize: typical expressive speech variation is 0.1–0.4
    normalized = np.clip(variation / 0.4, 0.0, 1.0)
    return round(float(normalized), 4)


if __name__ == "__main__":
    import sys
    score = compute_pitch_variation(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
    print(f"Pitch variation score: {score}")