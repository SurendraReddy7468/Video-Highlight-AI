from moviepy.editor import VideoFileClip

def extract_audio(video_path, output_path="data/audio/audio.wav"):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(output_path)
    
    return output_path