import re

def merge_segments(transcript_segments, max_gap=0.5, max_duration=12):
    merged = []
    current = transcript_segments[0].copy()

    for next_seg in transcript_segments[1:]:
        gap = next_seg["start"] - current["end"]
        duration = next_seg["end"] - current["start"]

        # Split current text into sentences
        sentences = re.split(r'(?<=[.!?]) +', current["text"])

        # If too long OR natural sentence break → finalize segment
        if gap > max_gap or duration > max_duration:
            merged.append(current)
            current = next_seg.copy()
        else:
            current["end"] = next_seg["end"]
            current["text"] += " " + next_seg["text"]

    merged.append(current)

    # 🔥 Post-process: split long segments into sentence chunks
    final_segments = []
    for seg in merged:
        sentences = re.split(r'(?<=[.!?]) +', seg["text"])

        temp_text = ""
        start = seg["start"]

        for sentence in sentences:
            if len(temp_text) + len(sentence) < 200:
                temp_text += " " + sentence
            else:
                final_segments.append({
                    "start": start,
                    "end": seg["end"],
                    "text": temp_text.strip()
                })
                temp_text = sentence

        if temp_text:
            final_segments.append({
                "start": start,
                "end": seg["end"],
                "text": temp_text.strip()
            })

    return final_segments