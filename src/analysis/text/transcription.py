import whisper
import json

def transcribe_audio(audio_path, output_path="data/transcripts/transcript.json"):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)

    segments = []
    for seg in result['segments']:
        segments.append({
            "start": seg['start'],
            "end": seg['end'],
            "text": seg['text'].strip()
        })

    with open(output_path, "w") as f:
        json.dump(segments, f, indent=4)

    return segments