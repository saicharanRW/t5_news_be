import os
import glob
from PIL import Image
import numpy as np
from moviepy.editor import VideoClip, CompositeVideoClip, AudioFileClip, concatenate_audioclips
from moviepy.video.fx.all import fadein
from moviepy.video.compositing.transitions import slide_in
import random
import math

try:
    from PIL.Image import Resampling
    LANCZOS_RESAMPLE = Resampling.LANCZOS
except ImportError:
    LANCZOS_RESAMPLE = Image.LANCZOS

SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
VIDEO_FPS = 30
VIDEO_MIN_ZOOM_EFFECT = 1.05
VIDEO_MAX_ZOOM_EFFECT = 1.25
VIDEO_PAN_MAX_PERCENTAGE = 0.15

def ease_in_out_sine(t_normalized):
    return -(math.cos(math.pi * t_normalized) - 1) / 2

def transition_crossfade(clip, duration, target_size=None, fps=None):
    return clip.crossfadein(duration)

def transition_slide_in_from_left(clip, duration, target_size=None, fps=None):
    return slide_in(clip, duration, 'left')

def transition_slide_in_from_right(clip, duration, target_size=None, fps=None):
    return slide_in(clip, duration, 'right')

def transition_slide_in_from_top(clip, duration, target_size=None, fps=None):
    return slide_in(clip, duration, 'bottom')

def transition_slide_in_from_bottom(clip, duration, target_size=None, fps=None):
    return slide_in(clip, duration, 'top')

def transition_fade_in_overlay(clip, duration, target_size=None, fps=None):
    return fadein(clip, duration)

AVAILABLE_TRANSITIONS = [
    transition_crossfade,
    transition_slide_in_from_left,
    transition_fade_in_overlay,
    transition_slide_in_from_right,
    transition_slide_in_from_top,
    transition_slide_in_from_bottom,
]

def lerp(start, end, t_eased):
    return start + t_eased * (end - start)

def create_ken_burns_clip_from_processed_image(image_path, duration, target_size, fps):
    try:
        pil_image_source = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Error loading processed image {image_path} for Ken Burns: {e}")
        return VideoClip(lambda t: np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8), duration=duration)

    source_img_w, source_img_h = pil_image_source.size
    target_w, target_h = target_size
    if not (source_img_w == target_w and source_img_h == target_h):
        pil_image_source = pil_image_source.resize((target_w, target_h), LANCZOS_RESAMPLE)
        source_img_w, source_img_h = pil_image_source.size

    start_zoom = random.uniform(VIDEO_MIN_ZOOM_EFFECT, VIDEO_MAX_ZOOM_EFFECT * 0.95)
    end_zoom = random.uniform(VIDEO_MIN_ZOOM_EFFECT, VIDEO_MAX_ZOOM_EFFECT)
    min_zoom_diff = 0.03
    while abs(start_zoom - end_zoom) < min_zoom_diff:
        end_zoom = random.uniform(VIDEO_MIN_ZOOM_EFFECT, VIDEO_MAX_ZOOM_EFFECT)
    if random.choice([True, False]):
        start_zoom, end_zoom = end_zoom, start_zoom
    start_pan_x_factor = random.uniform(0.0, 1.0)
    start_pan_y_factor = random.uniform(0.0, 1.0)
    end_pan_x_factor = random.uniform(0.0, 1.0)
    end_pan_y_factor = random.uniform(0.0, 1.0)
    min_pan_factor_diff_sq = (VIDEO_PAN_MAX_PERCENTAGE * 0.2)**2
    pan_distance_sq = (start_pan_x_factor - end_pan_x_factor)**2 + (start_pan_y_factor - end_pan_y_factor)**2
    retry_pan = 0
    while pan_distance_sq < min_pan_factor_diff_sq and retry_pan < 5:
        if random.random() < 0.3:
            end_pan_x_factor = random.uniform(0.0, 1.0)
            end_pan_y_factor = random.uniform(0.0, 1.0)
        else:
            end_pan_x_factor = random.uniform(0.5 - VIDEO_PAN_MAX_PERCENTAGE, 0.5 + VIDEO_PAN_MAX_PERCENTAGE)
            end_pan_y_factor = random.uniform(0.5 - VIDEO_PAN_MAX_PERCENTAGE, 0.5 + VIDEO_PAN_MAX_PERCENTAGE)
            end_pan_x_factor = max(0.0, min(1.0, end_pan_x_factor))
            end_pan_y_factor = max(0.0, min(1.0, end_pan_y_factor))
        pan_distance_sq = (start_pan_x_factor - end_pan_x_factor)**2 + (start_pan_y_factor - end_pan_y_factor)**2
        retry_pan +=1
    if retry_pan == 5 and pan_distance_sq < min_pan_factor_diff_sq:
        start_pan_x_factor, start_pan_y_factor = 0.5, 0.5
        end_pan_x_factor, end_pan_y_factor = 0.5, 0.5

    def make_frame(t):
        t_normalized = t / duration
        eased_progress = ease_in_out_sine(t_normalized)
        current_zoom = lerp(start_zoom, end_zoom, eased_progress)
        src_crop_w = target_w / current_zoom
        src_crop_h = target_h / current_zoom
        max_pan_x = (source_img_w - src_crop_w)
        max_pan_y = (source_img_h - src_crop_h)
        current_pan_x_f = lerp(start_pan_x_factor, end_pan_x_factor, eased_progress)
        current_pan_y_f = lerp(start_pan_y_factor, end_pan_y_factor, eased_progress)
        crop_x1 = max_pan_x * current_pan_x_f
        crop_y1 = max_pan_y * current_pan_y_f
        crop_x2 = crop_x1 + src_crop_w
        crop_y2 = crop_y1 + src_crop_h
        final_source_box = (
            int(round(crop_x1)), int(round(crop_y1)),
            int(round(crop_x2)), int(round(crop_y2))
        )
        frame_pil = pil_image_source.resize((target_w, target_h),
                                            resample=LANCZOS_RESAMPLE,
                                            box=final_source_box)
        return np.array(frame_pil)

    return VideoClip(make_frame, duration=duration, ismask=False)

def images_to_advanced_video(image_folder, output_video, fps=30):
    VIDEO_TRANSITION_DURATION = 1.2
    VIDEO_IMAGE_DURATION = 4.5
    VIDEO_TARGET_WIDTH = 1280
    VIDEO_TARGET_HEIGHT = 720
    VIDEO_FPS = fps
    VIDEO_ENCODING_PRESET = 'medium'
    VIDEO_ENCODING_CRF = '18'

    image_files = sorted([
        os.path.join(image_folder, f)
        for f in os.listdir(image_folder)
        if f.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)
    ])

    if not image_files:
        print(f"No images found in '{image_folder}'. Please add images. Exiting.")
        return

    if VIDEO_IMAGE_DURATION <= VIDEO_TRANSITION_DURATION:
        if VIDEO_IMAGE_DURATION == VIDEO_TRANSITION_DURATION:
             VIDEO_TRANSITION_DURATION = VIDEO_IMAGE_DURATION * 0.95
        if VIDEO_IMAGE_DURATION < VIDEO_TRANSITION_DURATION:
            VIDEO_TRANSITION_DURATION = VIDEO_IMAGE_DURATION * 0.5

    raw_video_clips = []
    for i, img_path in enumerate(image_files):
        clip = create_ken_burns_clip_from_processed_image(
                   img_path,
                   VIDEO_IMAGE_DURATION,
                   (VIDEO_TARGET_WIDTH, VIDEO_TARGET_HEIGHT),
                   VIDEO_FPS
               )
        raw_video_clips.append(clip)

    if not raw_video_clips:
        print("No raw video clips were created. Exiting.")
        return

    final_video = None
    video_parts = []
    current_time = 0.0
    final_video_duration = 0
    num_clips = len(raw_video_clips)

    if num_clips == 1:
        final_video = raw_video_clips[0].set_duration(VIDEO_IMAGE_DURATION)
        final_video_duration = VIDEO_IMAGE_DURATION
    elif num_clips > 1:
        first_clip = raw_video_clips[0].set_duration(VIDEO_IMAGE_DURATION).set_start(current_time)
        video_parts.append(first_clip)
        current_time += (VIDEO_IMAGE_DURATION - VIDEO_TRANSITION_DURATION)
        for i in range(1, num_clips):
            ken_burns_clip = raw_video_clips[i]
            clip_for_transition = ken_burns_clip.set_duration(VIDEO_IMAGE_DURATION)
            transition_idx = (i - 1) % len(AVAILABLE_TRANSITIONS)
            transition_function = AVAILABLE_TRANSITIONS[transition_idx]
            transitioned_clip = transition_function(
                clip_for_transition, 
                VIDEO_TRANSITION_DURATION,
                target_size=(VIDEO_TARGET_WIDTH, VIDEO_TARGET_HEIGHT),
                fps=VIDEO_FPS
            )
            final_clip_to_add = transitioned_clip.set_start(current_time)
            video_parts.append(final_clip_to_add)
            if i < num_clips - 1:
                current_time += (VIDEO_IMAGE_DURATION - VIDEO_TRANSITION_DURATION)
        final_video_duration = VIDEO_IMAGE_DURATION + (num_clips - 1) * (VIDEO_IMAGE_DURATION - VIDEO_TRANSITION_DURATION)
        final_video = CompositeVideoClip(video_parts, size=(VIDEO_TARGET_WIDTH, VIDEO_TARGET_HEIGHT)).set_duration(final_video_duration)
    else:
        print("No clips to make a video from after processing. This shouldn't happen if image_files had items.")
        return

    if final_video is None:
        print("Final video could not be assembled. Exiting.")
        return

    print(f"\nWriting video to {output_video} (Total estimated duration: {final_video.duration:.2f}s)...")
    try:
        threads = max(1, (os.cpu_count() or 2) // 2 )
        ffmpeg_params_list = ['-crf', VIDEO_ENCODING_CRF]
        final_video.write_videofile(
            output_video,
            fps=VIDEO_FPS,
            codec='libx264',
            audio_codec='aac',
            threads=threads,
            preset=VIDEO_ENCODING_PRESET,
            ffmpeg_params=ffmpeg_params_list,
            logger='bar',
            temp_audiofile=f"{os.path.splitext(output_video)[0]}_temp_audio.m4a"
        )
        print("Video generated successfully!")
    except Exception as e:
        print(f"An error occurred during video writing: {e}")
        import traceback
        traceback.print_exc()