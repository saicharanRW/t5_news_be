import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import VideoClip, CompositeVideoClip
import random
import math
from moviepy.video.fx import fadein, fadeout
from moviepy.video.compositing.transitions import slide_in, crossfadein

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

# Constants for text styling
TARGET_DISPLAY_WIDTH = 1280
TARGET_DISPLAY_HEIGHT = 720

# Centralized text styling parameters
TEXT_PARAMS = {
    'text_bold': True,
    'text_box_corner_radius': 15,
    'text_box_bg_color': (0, 0, 0, 180),
    'text_color_hex': '#FFFFFF',
    'text_stroke_color_hex': '#000000',
    'text_stroke_width': 2,
    'text_box_padding_x': 25,
    'text_box_padding_y': 20,
    'text_box_margin_horizontal': 40,
    'text_box_bottom_offset': 30,
    'text_ratio': 1.0
}

def ease_in_out_sine(t_normalized):
    return -(math.cos(math.pi * t_normalized) - 1) / 2

def transition_crossfade(clip, duration, target_size=None, fps=None):
    return clip.crossfadein(duration)

def transition_slide_in_from_left(clip, duration, target_size=None, fps=None):
    return slide_in(clip, duration, 'left')

def transition_slide_in_from_right(clip, duration, target_size=None, fps=None):
    return slide_in(clip, duration, 'right')

def transition_slide_in_from_top(clip, duration, target_size=None, fps=None):
    return slide_in(clip, duration, 'top')

def transition_slide_in_from_bottom(clip, duration, target_size=None, fps=None):
    return slide_in(clip, duration, 'bottom')

def transition_fade_in(clip, duration, target_size=None, fps=None):
    return fadein.fadein(clip, duration)

def transition_zoom_in(clip, duration, target_size=None, fps=None):
    def effect(get_frame, t):
        if t < duration:
            zoom_factor = 1.0 + (0.5 * (t / duration))
            frame = get_frame(t)
            pil_img = Image.fromarray(frame)
            w, h = pil_img.size
            new_w, new_h = int(w / zoom_factor), int(h / zoom_factor)
            img = pil_img.resize((new_w, new_h), LANCZOS_RESAMPLE)
            result = Image.new('RGB', (w, h))
            result.paste(img, ((w - new_w) // 2, (h - new_h) // 2))
            return np.array(result)
        return get_frame(t)
    return clip.fl(effect)

AVAILABLE_TRANSITIONS = [
    transition_crossfade,
    transition_slide_in_from_left,
    transition_slide_in_from_right,
    transition_slide_in_from_top,
    transition_slide_in_from_bottom,
    transition_fade_in,
    transition_zoom_in
]

def lerp(start, end, t_eased):
    return start + t_eased * (end - start)

def get_font(max_width_for_font_calc, max_height_for_font_calc, bold=False):
    """Advanced font selection with multiple fallbacks"""
    font_size = min(max_width_for_font_calc // 10, max_height_for_font_calc // 1.5, 40)
    font_size = max(font_size, 20) 

    if bold:
        font_names = [
            'arialbd.ttf', 'arialbi.ttf', 'calibrib.ttf', 'calibriz.ttf', 
            'seguisb.ttf', 'Verdana-Bold.ttf', 'DejaVuSans-Bold.ttf', 
            'Arial_Bold.ttf', 'Roboto-Bold.ttf', 'HelveticaNeue-Bold.ttf'
        ]
    else:
        font_names = [
            'arial.ttf', 'calibri.ttf', 'segoeui.ttf', 'verdana.ttf', 
            'DejaVuSans.ttf', 'Roboto-Regular.ttf', 'HelveticaNeue.ttf'
        ]

    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, font_size)
        except IOError:
            continue
    
    return ImageFont.load_default()

def layout_text(draw, text_content, font, max_allowed_width):
    """Advanced text layout with proper word wrapping and metrics calculation"""
    lines = []
    current_line_text = ''
    words = text_content.split()
    
    try:
        if hasattr(font, 'getlength'):
            get_text_width = lambda txt: font.getlength(txt)
            bbox_char_test = draw.textbbox((0,0), "Ay", font=font) 
            single_line_height = bbox_char_test[3] - bbox_char_test[1]
        elif hasattr(draw, 'textbbox'):
            get_text_width = lambda txt: draw.textbbox((0,0), txt, font=font)[2]
            bbox_char_test = draw.textbbox((0,0), "Ay", font=font)
            single_line_height = bbox_char_test[3] - bbox_char_test[1]
        else:
            font_size_attr = getattr(font, 'size', 20)
            get_text_width = lambda txt: len(txt) * (font_size_attr // 2)
            single_line_height = font_size_attr
    except Exception as e:
        font_size_attr = 20
        get_text_width = lambda txt: len(txt) * (font_size_attr // 2)
        single_line_height = font_size_attr

    for word in words:
        test_line = f'{current_line_text} {word}'.strip()
        current_line_width = get_text_width(test_line)

        if current_line_width <= max_allowed_width:
            current_line_text = test_line
        else:
            if current_line_text:
                lines.append(current_line_text)
            current_line_text = word
            
    if current_line_text:
        lines.append(current_line_text)

    if not lines:
        return [], 0, 0, single_line_height, single_line_height 

    actual_text_block_width = max(get_text_width(line) for line in lines)
    
    line_spacing_factor = 1.2
    effective_line_height_with_spacing = int(single_line_height * line_spacing_factor)
    total_text_block_height = (len(lines) - 1) * effective_line_height_with_spacing + single_line_height

    return lines, actual_text_block_width, total_text_block_height, single_line_height, effective_line_height_with_spacing

def add_text_advanced(image, text):
    """Advanced text overlay with centralized styling parameters"""
    if not text.strip():
        return image
    
    # Unpack centralized text parameters
    params = TEXT_PARAMS
    text_bold = params['text_bold']
    text_box_corner_radius = params['text_box_corner_radius']
    text_box_bg_color = params['text_box_bg_color']
    text_color_hex = params['text_color_hex']
    text_stroke_color_hex = params['text_stroke_color_hex']
    text_stroke_width = params['text_stroke_width']
    text_box_padding_x = params['text_box_padding_x']
    text_box_padding_y = params['text_box_padding_y']
    text_box_margin_horizontal = params['text_box_margin_horizontal']
    text_box_bottom_offset = params['text_box_bottom_offset']
    text_ratio = params['text_ratio']
    
    # Ensure image is in RGBA mode for transparency support
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    width, height = image.size
    
    # Calculate text box dimensions
    box_outer_x0 = text_box_margin_horizontal
    box_outer_x1 = width - text_box_margin_horizontal
    text_box_container_width = box_outer_x1 - box_outer_x0 

    if text_box_container_width <= 0:
        return image
    
    drawable_text_area_width = text_box_container_width - (2 * text_box_padding_x)

    if drawable_text_area_width <= 0:
        return image
    
    max_height_for_font_calc = int(height * 0.50) - (2 * text_box_padding_y)
    max_height_for_font_calc = max(max_height_for_font_calc, 30) 

    # Create temporary draw surface for text layout calculations
    temp_draw_surface = Image.new('RGB', (1, 1)) 
    draw_temp = ImageDraw.Draw(temp_draw_surface)
    font = get_font(drawable_text_area_width, max_height_for_font_calc, bold=text_bold)
    
    lines, text_block_actual_w, text_block_actual_h, single_line_h, eff_line_h = layout_text(
        draw_temp, text, font, drawable_text_area_width
    )

    if not lines or text_block_actual_h <= 0:
        return image
    
    final_text_box_bg_height = text_block_actual_h + (2 * text_box_padding_y)

    # Position text box at bottom
    box_outer_y1 = height - text_box_bottom_offset
    box_outer_y0 = box_outer_y1 - final_text_box_bg_height
    
    box_outer_y0 = max(0, box_outer_y0)
    box_outer_y1 = min(height, box_outer_y1)
    
    if box_outer_y0 >= box_outer_y1: 
        return image
    
    # Create text background layer
    text_bg_layer = Image.new('RGBA', image.size, (0, 0, 0, 0)) 
    draw_text_bg = ImageDraw.Draw(text_bg_layer)
    draw_text_bg.rounded_rectangle(
        (box_outer_x0, box_outer_y0, box_outer_x1, box_outer_y1),
        radius=text_box_corner_radius, 
        fill=text_box_bg_color
    )
    image = Image.alpha_composite(image, text_bg_layer) 

    # Draw text
    draw_on_img = ImageDraw.Draw(image)
    current_y_for_text = box_outer_y0 + text_box_padding_y

    for line_text in lines:
        try: 
            if hasattr(draw_on_img, 'textbbox'):
                line_bbox = draw_on_img.textbbox((0,0), line_text, font=font)
                current_line_w = line_bbox[2] - line_bbox[0]
            elif hasattr(font, 'getlength'):
                current_line_w = font.getlength(line_text)
            else: 
                current_line_w = len(line_text) * (font.size // 2)
        except Exception: 
            current_line_w = text_block_actual_w 

        line_start_x = box_outer_x0 + text_box_padding_x + (drawable_text_area_width - current_line_w) // 2
        
        # Draw text with stroke
        try: 
            draw_on_img.text((line_start_x, current_y_for_text), line_text,
                             fill=text_color_hex, font=font,
                             stroke_width=text_stroke_width,
                             stroke_fill=text_stroke_color_hex)
        except TypeError:  # Fallback
            draw_on_img.text((line_start_x, current_y_for_text), line_text, 
                             fill=text_color_hex, font=font)
        current_y_for_text += eff_line_h
    
    return image

def create_ken_burns_clip(image_path, duration, target_size, fps, text):
    """Create Ken Burns effect clip with advanced text overlay"""
    try:
        pil_image_source = Image.open(image_path).convert("RGBA")
    except Exception:
        return VideoClip(lambda t: np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8), duration=duration)

    source_img_w, source_img_h = pil_image_source.size
    target_w, target_h = target_size
    if not (source_img_w == target_w and source_img_h == target_h):
        pil_image_source = pil_image_source.resize((target_w, target_h), LANCZOS_RESAMPLE)
        source_img_w, source_img_h = pil_image_source.size

    # Generate random but smooth movement
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
    
    # Ensure meaningful movement
    pan_distance = math.sqrt((start_pan_x_factor - end_pan_x_factor)**2 + 
                             (start_pan_y_factor - end_pan_y_factor)**2)
    min_pan_distance = 0.2
    retry = 0
    while pan_distance < min_pan_distance and retry < 5:
        end_pan_x_factor = random.uniform(0.0, 1.0)
        end_pan_y_factor = random.uniform(0.0, 1.0)
        pan_distance = math.sqrt((start_pan_x_factor - end_pan_x_factor)**2 + 
                                 (start_pan_y_factor - end_pan_y_factor)**2)
        retry += 1

    def make_frame(t):
        t_normalized = t / duration
        eased_progress = ease_in_out_sine(t_normalized)
        current_zoom = lerp(start_zoom, end_zoom, eased_progress)
        src_crop_w = target_w / current_zoom
        src_crop_h = target_h / current_zoom
        max_pan_x = max(0, source_img_w - src_crop_w)
        max_pan_y = max(0, source_img_h - src_crop_h)
        current_pan_x_f = lerp(start_pan_x_factor, end_pan_x_factor, eased_progress)
        current_pan_y_f = lerp(start_pan_y_factor, end_pan_y_factor, eased_progress)
        crop_x1 = max_pan_x * current_pan_x_f
        crop_y1 = max_pan_y * current_pan_y_f
        crop_x2 = crop_x1 + src_crop_w
        crop_y2 = crop_y1 + src_crop_h
        
        frame_pil = pil_image_source.resize((target_w, target_h),
                                            resample=LANCZOS_RESAMPLE,
                                            box=(crop_x1, crop_y1, crop_x2, crop_y2))
        
        # Apply advanced text overlay
        frame_pil = add_text_advanced(frame_pil, text)
        
        return np.array(frame_pil.convert('RGB'))

    return VideoClip(make_frame, duration=duration)

def apply_transition(clip, next_clip, transition_type, duration, fps):
    """Apply rich transition between two clips"""
    if transition_type == "crossfade":
        return crossfadein(next_clip.crossfadein(duration), duration)
    elif transition_type == "slide_left":
        return slide_in(next_clip, duration, 'left')
    elif transition_type == "slide_right":
        return slide_in(next_clip, duration, 'right')
    elif transition_type == "slide_up":
        return slide_in(next_clip, duration, 'top')
    elif transition_type == "slide_down":
        return slide_in(next_clip, duration, 'bottom')
    elif transition_type == "fade":
        return fadein.fadein(next_clip, duration)
    elif transition_type == "zoom":
        return transition_zoom_in(next_clip, duration)
    else:  # Default to crossfade
        return crossfadein(next_clip.crossfadein(duration), duration)

def images_to_advanced_video(image_folder, output_video, titles, fps=30):
    """Create video with rich Ken Burns effects and transitions"""
    # Set duration for 5 images to total 25 seconds
    IMAGE_DURATION = 5.0
    TRANSITION_DURATION = 1.0
    TARGET_SIZE = (TARGET_DISPLAY_WIDTH, TARGET_DISPLAY_HEIGHT)
    
    image_files = sorted([
        os.path.join(image_folder, f)
        for f in os.listdir(image_folder)
        if f.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)
    ])[:5]  # Only use first 5 images

    if not image_files:
        return

    # Create clips for each image
    clips = []
    for i, img_path in enumerate(image_files):
        clip = create_ken_burns_clip(
            img_path,
            IMAGE_DURATION + (TRANSITION_DURATION if i < len(image_files)-1 else 0),
            TARGET_SIZE,
            fps,
            text=titles[i] if i < len(titles) else ""
        )
        clips.append(clip)

    # Apply rich transitions between clips
    transition_types = ["crossfade", "slide_left", "slide_right", "fade", "zoom"]
    final_clips = [clips[0].set_start(0)]
    
    for i in range(1, len(clips)):
        # Apply transition to next clip
        transition_type = transition_types[(i-1) % len(transition_types)]
        transitioned_clip = apply_transition(
            clips[i-1], 
            clips[i], 
            transition_type,
            TRANSITION_DURATION,
            fps
        )
        # Set start time with overlap
        start_time = i * IMAGE_DURATION - TRANSITION_DURATION
        transitioned_clip = transitioned_clip.set_start(start_time)
        final_clips.append(transitioned_clip)

    # Create final video composition
    final_video = CompositeVideoClip(final_clips, size=TARGET_SIZE)
    final_video = final_video.set_duration(len(image_files) * IMAGE_DURATION)

    # Write video file
    try:
        final_video.write_videofile(
            output_video,
            fps=fps,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='medium',
            ffmpeg_params=['-crf', '18'],
            logger='bar'
        )
    except Exception as e:
        print(f"Video writing error: {e}")