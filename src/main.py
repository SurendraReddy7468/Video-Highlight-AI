from src.preprocessing.video_loader import load_video
from src.preprocessing.audio_extractor import extract_audio
from src.analysis.text.transcription import transcribe_audio
from src.preprocessing.segmenter import merge_segments
import json

# 🔹 OPTION 1: YouTube link
# input_source = "https://www.youtube.com/watch?v=2ePf9rue1Ao"

# 🔹 OPTION 2: Local file
input_source = "data/raw_videos/video_01.mp4"

# STEP 1: Load video
video_path = load_video(input_source)
# print("Video Path:", video_path)

# STEP 2: Extract audio from video
audio_path = extract_audio(video_path)
# print("Audio Path:", audio_path)

# STEP 3: Transcribe audio
transcript = transcribe_audio(audio_path)
# print("Transcript:", transcript[:2])

# STEP 4: Merge segments
segments = merge_segments(transcript)

# Save segments
with open("data/segments/segments.json", "w") as f:
    json.dump(segments, f, indent=4)

print("Final Segments:", segments)