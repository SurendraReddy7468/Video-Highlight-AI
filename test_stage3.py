# test_stage3.py
import sys, json
sys.path.insert(0, ".")

from src.preprocessing.segmenter      import merge_segments
from src.scoring.highlight_score       import score_segments, save_scores
from src.editing.clip_generator        import generate_clip
from src.editing.format_converter      import convert_to_vertical

VIDEO_PATH = "data/raw_videos/video_01.mp4"
AUDIO_PATH = "data/audio/video_01.wav"
MODE       = "shorts"   # change to "highlights" for long clip

# Load segments
with open("data/segments/segments.json", "r") as f:
    segments = json.load(f)

# Score
scored = score_segments(segments, AUDIO_PATH, mode="podcast")
save_scores(scored)

# Generate clip
raw_clip = generate_clip(VIDEO_PATH, scored, mode=MODE, output_name="raw_clip")

# Convert format
final = convert_to_vertical(raw_clip, "data/outputs/shorts/final_short.mp4")

print(f"\n🎉 FINAL OUTPUT: {final}")