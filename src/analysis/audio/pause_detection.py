import librosa
import numpy as np


def compute_pause_score(audio_path: str, start: float, end: float) -> float:
    """
    Detect dramatic pauses in speech and return a highlight score.

    Why pauses matter: In motivational/podcast content, a speaker
    pauses deliberately before or after a key point. These moments
    of silence signal importance — "let that sink in" effect.

    Scoring logic:
      - A segment with NO pauses → neutral score (0.5)
      - Short pauses (0.3–0.8s) → slight boost (speaker emphasis)
      - Long dramatic pauses (0.8s+) → strong boost (key moment)
      - Too much silence (>40% of segment) → penalty (dead air)

    Returns score between 0.0 and 1.0
    """
    y, sr = librosa.load(audio_path, sr=None, offset=start,
                         duration=end - start, mono=True)

    if len(y) == 0:
        return 0.5

    segment_duration = end - start

    # Detect non-silent intervals (speech regions)
    # top_db=30 means anything 30dB below peak is considered silence
    speech_intervals = librosa.effects.split(y, top_db=30)

    if len(speech_intervals) == 0:
        return 0.0   # entire segment is silence

    # Calculate pause durations (gaps between speech intervals)
    pauses = []
    for i in range(1, len(speech_intervals)):
        pause_start = speech_intervals[i - 1][1] / sr
        pause_end   = speech_intervals[i][0]     / sr
        pause_dur   = pause_end - pause_start
        if pause_dur >= 0.3:   # ignore tiny gaps < 300ms (natural speech rhythm)
            pauses.append(pause_dur)

    if not pauses:
        return 0.5   # no meaningful pauses — neutral

    total_pause_time = sum(pauses)
    pause_ratio      = total_pause_time / segment_duration
    max_pause        = max(pauses)
    num_pauses       = len(pauses)

    # Penalty: too much dead air (>40% silence = boring segment)
    if pause_ratio > 0.4:
        return round(max(0.1, 0.5 - (pause_ratio - 0.4)), 4)

    # Score based on dramatic pause presence
    # Long single pause (0.8s+) = speaker letting point land
    dramatic_pauses = [p for p in pauses if p >= 0.8]

    if dramatic_pauses:
        # Normalize: a 2-second pause = perfect score
        drama_score = min(max(dramatic_pauses) / 2.0, 1.0)
        # Blend with pause count signal
        count_score = min(num_pauses / 3.0, 1.0)
        score = 0.7 * drama_score + 0.3 * count_score
    else:
        # Only short pauses — mild emphasis
        score = min(num_pauses / 5.0, 0.6)

    return round(float(score), 4)


if __name__ == "__main__":
    import sys
    score = compute_pause_score(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
    print(f"Pause score: {score}")