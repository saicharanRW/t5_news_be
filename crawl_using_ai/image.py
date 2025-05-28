import os
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, UnidentifiedImageError
from colorthief import ColorThief
import requests
from io import BytesIO
import uuid
import base64

try:
    from PIL.Image import Resampling
    LANCZOS_RESAMPLE = Resampling.LANCZOS
except ImportError:
    LANCZOS_RESAMPLE = Image.LANCZOS

TARGET_DISPLAY_WIDTH = 800
TARGET_DISPLAY_HEIGHT = 600

# Configure image storage
IMAGE_STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'processed_images')
os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)

def generate_unique_filename(title=None, extension='.png'):
    """Generate a unique filename with optional title"""
    unique_id = uuid.uuid4().hex[:8]
    if title:
        # Clean title for filename use
        clean_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]
        clean_title = clean_title.replace(' ', '_')
        return f"{clean_title}_{unique_id}{extension}"
    return f"image_{unique_id}{extension}"

def enhance_image(image, sharpen, contrast):
    """Enhanced image processing with alpha channel support"""
    original_mode = image.mode
    alpha_channel = None

    if image.mode == 'RGBA' or image.mode == 'LA':
        alpha_channel = image.split()[-1]
        image_rgb = image.convert('RGB')
    elif image.mode != 'RGB':
        image_rgb = image.convert('RGB')
    else:
        image_rgb = image

    enhanced_rgb = ImageEnhance.Contrast(ImageEnhance.Sharpness(image_rgb).enhance(sharpen)).enhance(contrast)

    if alpha_channel:
        enhanced_rgb.putalpha(alpha_channel)
        return enhanced_rgb
    elif original_mode == 'RGBA' or original_mode == 'LA':
        return enhanced_rgb.convert('RGBA')
    return enhanced_rgb

def get_font(max_width_for_font_calc, max_height_for_font_calc, bold=False):
    """Advanced font selection with multiple fallbacks"""
    font_size = min(max_width_for_font_calc // 15, max_height_for_font_calc // 2, 30) 
    font_size = max(font_size, 12) 

    if bold:
        font_names = [
            'arialbd.ttf', 'arialbi.ttf', 'calibrib.ttf', 'calibriz.ttf', 'seguisb.ttf', 'Verdana-Bold.ttf',
            'DejaVuSans-Bold.ttf', 'Arial_Bold.ttf', 'Roboto-Bold.ttf', 'HelveticaNeue-Bold.ttf',
            'arial.ttf', 'calibri.ttf', 'segoeui.ttf', 'verdana.ttf', 'DejaVuSans.ttf', 'Roboto-Regular.ttf', 'HelveticaNeue.ttf'
        ]
    else:
        font_names = [
            'arial.ttf', 'calibri.ttf', 'segoeui.ttf', 'verdana.ttf', 'DejaVuSans.ttf', 'Roboto-Regular.ttf', 'HelveticaNeue.ttf',
            'arialbd.ttf', 'calibrib.ttf', 'seguisb.ttf', 'Verdana-Bold.ttf', 'DejaVuSans-Bold.ttf', 'Roboto-Bold.ttf', 'HelveticaNeue-Bold.ttf'
        ]

    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, font_size)
        except IOError:
            continue
    
    print(f"Warning: Preferred fonts not found. Loading Pillow's default font.")
    try:
        return ImageFont.load_default(size=font_size) 
    except TypeError: 
        return ImageFont.load_default()
    except Exception:
        print("Critical Warning: Could not load any font.")
        return ImageFont.ImageFont()

def layout_text(draw, text_content, font, max_allowed_width):
    """Advanced text layout with proper word wrapping and metrics calculation"""
    lines = []
    current_line_text = ''
    words = text_content.split()
    
    try:
        if hasattr(font, 'getlength') and callable(getattr(font, 'getlength')): 
            def get_text_width(txt): return font.getlength(txt)
            bbox_char_test = draw.textbbox((0,0), "Ay", font=font) 
            single_line_height = bbox_char_test[3] - bbox_char_test[1]
        elif hasattr(draw, 'textbbox') and callable(getattr(draw, 'textbbox')): 
            def get_text_width(txt):
                bbox = draw.textbbox((0, 0), txt, font=font)
                return bbox[2] - bbox[0]
            bbox_char_test = draw.textbbox((0,0), "Ay", font=font)
            single_line_height = bbox_char_test[3] - bbox_char_test[1]
        elif hasattr(font, 'getsize') and callable(getattr(font, 'getsize')): 
            def get_text_width(txt): return font.getsize(txt)[0]
            single_line_height = font.getsize("Ay")[1]
        else: 
            font_size_attr = getattr(font, 'size', 20) 
            def get_text_width(txt): return len(txt) * (font_size_attr // 2)
            single_line_height = font_size_attr
            print("Warning: Using basic font metrics. Text layout might be suboptimal.")

        if single_line_height <= 0: 
            single_line_height = getattr(font, 'size', 20) 
    except Exception as e:
        print(f"Error in font metrics for text '{text_content[:30]}...': {e}. Using fallback.")
        font_size_attr = getattr(font, 'size', 20)
        def get_text_width(txt): return len(txt) * (font_size_attr // 2)
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
            word_w = get_text_width(current_line_text)
            if word_w > max_allowed_width:
                 print(f"Warning: Word '{current_line_text}' ({word_w}px) is wider than allowed ({max_allowed_width}px). It might be clipped or overflow.")
    if current_line_text:
        lines.append(current_line_text)

    if not lines:
        return [], 0, 0, single_line_height, single_line_height 

    actual_text_block_width = 0
    for line in lines:
        line_w = get_text_width(line)
        if line_w > actual_text_block_width:
            actual_text_block_width = line_w
    
    line_spacing_factor = 1.2
    effective_line_height_with_spacing = int(single_line_height * line_spacing_factor)
    if effective_line_height_with_spacing <=0 : effective_line_height_with_spacing = int(single_line_height * 1.2) if single_line_height > 0 else 20 
    if single_line_height <=0: single_line_height = effective_line_height_with_spacing 

    total_text_block_height = (len(lines) - 1) * effective_line_height_with_spacing + single_line_height
    if total_text_block_height <=0 and lines: total_text_block_height = single_line_height 

    return lines, actual_text_block_width, total_text_block_height, single_line_height, effective_line_height_with_spacing

def add_rounded_corners_to_image(image, radius):
    """Add rounded corners to image"""
    if radius <= 0: 
        return image
    if image.mode != 'RGBA':
        image = image.convert("RGBA")
    
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, image.width, image.height), radius=radius, fill=255)
    image.putalpha(mask)
    return image

def add_text_advanced(image, text, ratio=0.75, text_bold=False,
                     text_box_corner_radius=0,   
                     text_box_bg_color=(40, 40, 40, 200),
                     text_color_hex='#FFFFFF',
                     text_stroke_color_hex='#000000',
                     text_stroke_width=1,
                     text_box_padding_x=25,
                     text_box_padding_y=15,
                     text_box_margin_horizontal=30,
                     text_box_bottom_offset=0):
    """Advanced text overlay with background box, stroke support, and flexible positioning"""
    if not text.strip():
        return image
    
    # Ensure image is in RGBA mode for transparency support
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    width, height = image.size
    
    # Calculate text box dimensions
    box_outer_x0 = text_box_margin_horizontal
    box_outer_x1 = width - text_box_margin_horizontal
    text_box_container_width = box_outer_x1 - box_outer_x0 

    if text_box_container_width <= 0:
        print(f"Warning: Text box container width is too small ({text_box_container_width}px). Skipping text overlay.")
        return image
    
    drawable_text_area_width = text_box_container_width - (2 * text_box_padding_x)

    if drawable_text_area_width <= 0:
        print(f"Warning: Drawable text area width is too small after padding ({drawable_text_area_width}px). Skipping text.")
        return image
    
    max_height_for_font_calc = int(height * 0.40) - (2 * text_box_padding_y)
    max_height_for_font_calc = max(max_height_for_font_calc, 20) 

    # Create temporary draw surface for text layout calculations
    temp_draw_surface = Image.new('RGB', (1, 1)) 
    draw_temp = ImageDraw.Draw(temp_draw_surface)
    font = get_font(drawable_text_area_width, max_height_for_font_calc, bold=text_bold)
    
    lines, text_block_actual_w, text_block_actual_h, single_line_h, eff_line_h = layout_text(
        draw_temp, text, font, drawable_text_area_width
    )

    if not lines or text_block_actual_h <= 0:
        print(f"Warning: No text to add or text layout failed (height: {text_block_actual_h}).")
        return image
    
    final_text_box_bg_height = text_block_actual_h + (2 * text_box_padding_y)

    # Position text box based on ratio
    if ratio >= 1.0:
        # Bottom positioning
        box_outer_y1 = height - text_box_bottom_offset
        box_outer_y0 = box_outer_y1 - final_text_box_bg_height
    else:
        # Ratio-based positioning
        y_start = int(height * ratio)
        box_outer_y0 = y_start
        box_outer_y1 = box_outer_y0 + final_text_box_bg_height
    
    box_outer_y0 = max(0, box_outer_y0)
    box_outer_y1 = min(height, box_outer_y1)
    
    if box_outer_y0 >= box_outer_y1: 
        print(f"Warning: Text box background height is zero or negative after calculations (y0:{box_outer_y0}, y1:{box_outer_y1}). Skipping text overlay.")
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

    for line_idx, line_text in enumerate(lines):
        try: 
            if hasattr(draw_on_img, 'textbbox'):
                line_bbox = draw_on_img.textbbox((0,0), line_text, font=font)
                current_line_w = line_bbox[2] - line_bbox[0]
            elif hasattr(font, 'getlength'):
                current_line_w = font.getlength(line_text)
            elif hasattr(font, 'getsize'):
                current_line_w = font.getsize(line_text)[0]
            else: 
                current_line_w = len(line_text) * (font.size // 2 if hasattr(font, 'size') else 10)
        except Exception: 
            current_line_w = text_block_actual_w 

        line_start_x = box_outer_x0 + text_box_padding_x + (drawable_text_area_width - current_line_w) // 2
        
        # Draw text with stroke (or without if Pillow version is old)
        try: 
            draw_on_img.text((line_start_x, current_y_for_text), line_text,
                             fill=text_color_hex, font=font,
                             stroke_width=text_stroke_width,
                             stroke_fill=text_stroke_color_hex)
        except TypeError: # Fallback for older Pillow versions (no stroke)
            print(f"Warning: Pillow version too old for text stroke. Drawing without stroke.")
            draw_on_img.text((line_start_x, current_y_for_text), line_text, fill=text_color_hex, font=font)
        current_y_for_text += eff_line_h
    
    return image

def download_image(image_url):
    """Download image from URL and return as BytesIO object"""
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None

def save_image(image, title=None):
    """Save image to local storage and return the file path"""
    filename = generate_unique_filename(title)
    filepath = os.path.join(IMAGE_STORAGE_DIR, filename)
    image.save(filepath, "PNG", quality=95)
    return filepath

def process_image_from_url(image_url, title, **kwargs):
    """Process image from URL and save locally"""
    try:
        img_data = download_image(image_url)
        if not img_data:
            return None
            
        return process_image(img_data, title, **kwargs)
        
    except Exception as e:
        print(f"Error processing image from URL: {e}")
        return None

def process_image(img_data, text, sharpen=1.5, contrast=1.1,
                 text_bold=False,
                 main_image_corner_radius=15,
                 text_box_corner_radius=10,
                 text_box_bg_color=(40, 40, 40, 200),
                 text_color_hex=None,
                 text_stroke_color_hex='#000000',
                 text_stroke_width=1,
                 text_box_padding_x=15,
                 text_box_padding_y=10,
                 text_box_margin_horizontal=10,
                 text_box_bottom_offset=0,
                 text_ratio=0.80):
    """Enhanced image processing with advanced text overlay, saves locally and returns file path"""
    try:
        img = Image.open(img_data)

        # Resize to target dimensions
        img = img.resize((TARGET_DISPLAY_WIDTH, TARGET_DISPLAY_HEIGHT), resample=LANCZOS_RESAMPLE)

        # Set text color: always white if not specified
        final_text_color_hex = text_color_hex if text_color_hex is not None else '#FFFFFF'
        print(f"Using text color: {final_text_color_hex}")


        # Convert to RGBA for transparency support
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Enhance image
        img = enhance_image(img, sharpen, contrast)

        # Add advanced text overlay
        img = add_text_advanced(
            img, text,
            ratio=text_ratio,
            text_bold=text_bold,
            text_box_corner_radius=text_box_corner_radius,
            text_box_bg_color=text_box_bg_color,
            text_color_hex=final_text_color_hex, # Use the determined white (or specified) text color
            text_stroke_color_hex=text_stroke_color_hex,
            text_stroke_width=text_stroke_width,
            text_box_padding_x=text_box_padding_x,
            text_box_padding_y=text_box_padding_y,
            text_box_margin_horizontal=text_box_margin_horizontal,
            text_box_bottom_offset=text_box_bottom_offset
        )

        # Add rounded corners to main image if specified
        if main_image_corner_radius > 0:
            img = add_rounded_corners_to_image(img, main_image_corner_radius)        # Save locally and return file path
        return save_image(img, text)

    except Exception as e:
        print(f"Error processing image: {e}")
        import traceback
        traceback.print_exc()
        return None