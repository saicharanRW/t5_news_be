from moviepy.editor import VideoFileClip, AudioFileClip

def add_music_to_video(video_path, audio_path, output_path):
    """
    Add audio to video and export the final video.
    """
    clip = VideoFileClip(video_path)
    audioclip = AudioFileClip(audio_path)
    videoclip = clip.set_audio(audioclip)
    videoclip.write_videofile(output_path)
