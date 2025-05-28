import os
from PIL import Image, ImageEnhance, UnidentifiedImageError, ImageDraw
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

def download_image(image_url):
    """Download image from URL and return as BytesIO object"""
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None

def image_to_base64(image, format='PNG'):
    """Convert PIL Image to base64 string"""
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/{format.lower()};base64,{image_base64}"

def process_image_from_url(image_url, **kwargs):
    """Process image from URL and return base64 string (no text overlay)"""
    try:
        img_data = download_image(image_url)
        if not img_data:
            return None
        return process_image(img_data, **kwargs)
    except Exception as e:
        print(f"Error processing image from URL: {e}")
        return None

def process_image(img_data, sharpen=1.5, contrast=1.1,
                 main_image_corner_radius=15):
    """Enhanced image processing (resize, enhance, rounded corners), return base64 string (no text overlay)"""
    try:
        img = Image.open(img_data)

        # Resize to target dimensions
        img = img.resize((TARGET_DISPLAY_WIDTH, TARGET_DISPLAY_HEIGHT), resample=LANCZOS_RESAMPLE)

        # Convert to RGBA for transparency support
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Enhance image
        img = enhance_image(img, sharpen, contrast)

        # Add rounded corners to main image if specified
        if main_image_corner_radius > 0:
            img = add_rounded_corners_to_image(img, main_image_corner_radius)

        # Convert to base64 and return
        return image_to_base64(img)

    except Exception as e:
        print(f"Error processing image: {e}")
        import traceback
        traceback.print_exc()
        return None