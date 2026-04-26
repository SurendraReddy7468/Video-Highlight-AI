import json
import os

def _narrative_penalty(seg_a: dict, seg_b: dict) -> float:
    """
    Calculate a penalty (0.0–0.3) for jumping between two unrelated segments.
    Lower penalty = more related = better flow.

    Checks word overlap between adjacent segment texts.
    Segments sharing key words are likely on the same topic.
    """
    import re
    STOP = {"a","an","the","and","or","but","in","on","at","to","for","of",
            "with","is","it","was","are","i","you","he","she","we","they",
            "this","that","so","just","not","be","do","get","have","my","your"}

    def keywords(text):
        words = re.findall(r"[a-z]+", text.lower())
        return set(w for w in words if w not in STOP and len(w) > 3)

    kw_a = keywords(seg_a["text"])
    kw_b = keywords(seg_b["text"])

    if not kw_a or not kw_b:
        return 0.15   # neutral penalty

    overlap = len(kw_a & kw_b) / max(len(kw_a | kw_b), 1)

    # overlap=0 (no common words) → penalty=0.25
    # overlap=1 (identical topics) → penalty=0.0
    return round(0.25 * (1.0 - overlap), 4)

def score_segments(
    segments: list,
    audio_path: str,
    video_path: str,
    mode: str = "podcast",
) -> list:
    """
    Combine all audio/text/video features into a single highlight score
    for each segment.

    Weights (from settings):
      podcast mode  → audio 0.45 | text 0.45 | video 0.10
      normal mode   → audio 0.30 | text 0.30 | video 0.40

    Args:
        segments:    List of feature-enriched segments (from analysis step)
        audio_path:  Path to the WAV file (used by audio analyzers)
        mode:        'podcast' or 'normal'

    Returns:
        List of segments with an added 'score' field, sorted best-first
    """
    from src.analysis.audio.energy   import compute_energy
    from src.analysis.audio.pitch    import compute_pitch_variation
    from src.analysis.audio.pause_detection import compute_pause_score
    from src.analysis.text.keywords  import compute_keyword_score
    from src.analysis.text.sentiment import compute_sentiment_score
    from src.analysis.text.hook_detector import compute_hook_score
    from src.analysis.video.scene_change import compute_scene_change_score
    from src.analysis.video.face_detect  import compute_face_score

    # Scoring weights
    weights = {
        "podcast": {"audio": 0.45, "text": 0.45, "video": 0.10},
        "normal":  {"audio": 0.30, "text": 0.30, "video": 0.40},
    }.get(mode, {"audio": 0.45, "text": 0.45, "video": 0.10})

    all_texts = [s["text"] for s in segments]
    scored    = []

    print(f"[Scorer] ⚡ Scoring {len(segments)} segments (mode: {mode}) ...")

    for seg in segments:
        start, end = seg["start"], seg["end"]

        # ── Audio features ──────────────────────────────────────
        energy = compute_energy(audio_path, start, end)
        pitch  = compute_pitch_variation(audio_path, start, end)
        pause       = compute_pause_score(audio_path, start, end)
        audio_score = (energy + pitch + pause) / 3

        # ── Text features ────────────────────────────────────────
        keywords  = compute_keyword_score(seg["text"], all_texts)
        sentiment = compute_sentiment_score(seg["text"])
        hook      = compute_hook_score(seg["text"])
        text_score = (keywords * 0.4 + sentiment * 0.3 + hook * 0.3)

        # ── Video features (now fully active) ───────────────────────
        scene       = compute_scene_change_score(video_path, start, end)
        face_result = compute_face_score(video_path, start, end)
        face        = face_result["score"]
        face_cx     = face_result["center_x"]
        video_score = (scene + face) / 2

        # ── Final weighted score ─────────────────────────────────
        final_score = (
            weights["audio"] * audio_score +
            weights["text"]  * text_score  +
            weights["video"] * video_score
        )

        scored.append({
            "start":         start,
            "end":           end,
            "text":          seg["text"],
            "energy":        energy,
            "pitch":         pitch,
            "pause":         pause,          
            "keywords":      keywords,
            "sentiment":     sentiment,
            "hook":          hook,
            "scene":         scene,          
            "face":          face,           
            "face_center_x": face_cx,        
            "audio_score":   round(audio_score, 4),
            "text_score":    round(text_score,  4),
            "video_score":   round(video_score, 4),
            "score":         round(final_score, 4),
        })

    # Sort best first
    scored.sort(key=lambda x: x["score"], reverse=True)

    print(f"[Scorer] ✅ Top segment: [{scored[0]['start']}s → {scored[0]['end']}s]  score={scored[0]['score']}")
    return scored


def save_scores(scored: list, output_dir: str = "data/temp", name: str = "scores") -> str:
    """Save scored segments to JSON."""
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{name}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2, ensure_ascii=False)
    print(f"[Scorer] 💾 Scores saved: {out_path}")
    return out_path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    with open("data/segments/segments.json", "r") as f:
        segs = json.load(f)

    scored = score_segments(segs, "data/audio/video_01.wav", mode="podcast")
    save_scores(scored)

    print("\nTop 5 segments:")
    for i, s in enumerate(scored[:5]):
        print(f"  #{i+1}  score={s['score']}  [{s['start']}s→{s['end']}s]  {s['text'][:55]}...")