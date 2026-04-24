import os
import json


def merge_segments(
    raw_segments: list,
    max_gap: float = 1.5,
    min_duration: float = 3.0,
    max_duration: float = 15.0,
) -> list:
    """
    Merge raw Whisper chunks into meaningful sentence-level segments.

    Why do we need this?
    Whisper splits audio into small chunks (often 1-3 seconds each).
    Those tiny chunks are too short to score meaningfully — we need
    complete thoughts/sentences.  This function glues nearby chunks
    together into segments that are long enough to analyze.

    Merging rules:
      1. If the gap between two chunks is small (≤ max_gap seconds), merge them.
      2. Always merge if the current segment is still too short (< min_duration).
      3. Stop merging if the current segment is already long enough (≥ max_duration).

    Args:
        raw_segments:  List of {start, end, text} from Whisper
        max_gap:       Max silence gap (sec) that still triggers a merge
        min_duration:  Minimum segment length in seconds
        max_duration:  Maximum segment length before forcing a split

    Returns:
        List of merged segments [{start, end, text}, ...]
    """
    if not raw_segments:
        print("[Segmenter] ⚠️  No segments to merge.")
        return []

    merged = []
    current = raw_segments[0].copy()

    for next_seg in raw_segments[1:]:
        gap = next_seg["start"] - current["end"]
        current_duration = current["end"] - current["start"]

        # Decision: should we merge next_seg into current?
        too_short  = current_duration < min_duration
        gap_small  = gap <= max_gap
        not_too_long = current_duration < max_duration

        if (gap_small and not_too_long) or too_short:
            # Merge: extend end time and append text
            current["end"]  = next_seg["end"]
            current["text"] = current["text"].rstrip() + " " + next_seg["text"].lstrip()
        else:
            # Finalize current segment and start a new one
            merged.append(current)
            current = next_seg.copy()

    merged.append(current)  # Don't forget the last segment

    print(
        f"[Segmenter] ✅ {len(raw_segments)} raw chunks → "
        f"{len(merged)} merged segments"
    )
    return merged


def save_segments(segments: list, output_dir: str = "data/segments", name: str = "segments") -> str:
    """Save segments list to a JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{name}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)
    print(f"[Segmenter] 💾 Segments saved: {out_path}")
    return out_path


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python segmenter.py <transcript.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        raw = json.load(f)

    segments = merge_segments(raw)
    save_segments(segments)

    print("\nAll segments:")
    for i, s in enumerate(segments):
        duration = round(s["end"] - s["start"], 1)
        print(f"  [{i+1}] {s['start']}s → {s['end']}s ({duration}s)  |  {s['text'][:60]}...")