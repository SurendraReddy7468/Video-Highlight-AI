import yt_dlp
import os


def load_video(input_source, output_path="data/raw_videos"):
    print(f"\n📥 Input source: {input_source}")

    if input_source.startswith("http"):
        print("🌐 Detected URL → Downloading video...")
        return download_youtube_video(input_source, output_path)
    else:
        print("📁 Detected local file → Using existing video...")
        return load_local_video(input_source)


def download_youtube_video(url, output_path):
    os.makedirs(output_path, exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),

        # ✅ FIXED: ensures compatible audio (m4a/AAC) + video
        'format': 'bestvideo+bestaudio[ext=m4a]/best',

        # ✅ Merge into MP4
        'merge_output_format': 'mp4',

        # ✅ Force proper conversion (extra safety)
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],

        'quiet': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        # Final merged file path
        final_path = os.path.join(output_path, f"{info['id']}.mp4")

    print(f"✅ Download completed: {final_path}")
    return final_path


def load_local_video(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ File not found: {path}")

    print(f"✅ Found local video: {path}")
    return path