from moviepy.editor import VideoFileClip, AudioFileClip
import os

def add_music_to_video(video_path, audio_path, output_path, duration=25):
    """
    Add audio to video, trimming audio to the specified duration (default 25s),
    and export the final video. No temp audio file is left on disk.
    """
    clip = VideoFileClip(video_path)
    audioclip = AudioFileClip(audio_path).subclip(0, duration)
    videoclip = clip.set_audio(audioclip)
    videoclip.write_videofile(output_path)
    clip.close()
    audioclip.close()
    videoclip.close()

def add_music_to_video_with_defaults(video_path, output_path, duration=25, audio_path="audio.mp3"):
    """
    Add default music (audio.mp3) to the video, trimming to 25 seconds.
    """
    add_music_to_video(video_path, audio_path, output_path, duration=duration)
