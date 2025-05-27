import os
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from colorthief import ColorThief
import requests
from io import BytesIO
import uuid
import base64

TARGET_DISPLAY_WIDTH = 800
TARGET_DISPLAY_HEIGHT = 600

def get_contrast_color(rgb):
    """Get contrasting text color based on background color"""
    r, g, b = rgb
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return '#000000' if luminance > 128 else '#FFFFFF'

def enhance_image(image, sharpen, contrast):
    """Enhance image with sharpening and contrast adjustments"""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    return ImageEnhance.Contrast(ImageEnhance.Sharpness(image).enhance(sharpen)).enhance(contrast)

def get_font(text, max_width, max_height):
    """Get appropriate font size for the given text and dimensions"""
    font_size = min(max_width // 15, max_height // 2, 48)
    font_size = max(font_size, 10)
    
    fonts = [
        'arialbd.ttf', 'calibrib.ttf', 'Arial_Bold.ttf',
        'arial.ttf', 'calibri.ttf', 'Arial.ttf'
    ]
    
    for font_name in fonts:
        try:
            return ImageFont.truetype(font_name, font_size)
        except:
            continue
    
    return ImageFont.load_default()

def add_text(image, text, ratio=0.75, color='black'):
    """Add text overlay to image with word wrapping"""
    if not text.strip():
        return image
    
    draw = ImageDraw.Draw(image)
    width, height = image.size
    y = int(height * ratio) + 5
    max_width = width - 10
    max_height = height - y - 10
    
    font = get_font(text, max_width, max_height)
    
    lines = []
    current_line = ''
    
    for word in text.split():
        test_line = f'{current_line} {word}'.strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        if text_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    line_height = font.getbbox("A")[3] - font.getbbox("A")[1] if hasattr(font, 'getbbox') else font.size
    total_text_height = len(lines) * line_height
    y_pos = y + (max_height - total_text_height) // 2
    
    for line in lines:
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_width = line_bbox[2] - line_bbox[0]
        x_pos = (width - line_width) // 2
        
        draw.text((x_pos, y_pos), line, fill=color, font=font)
        y_pos += line_height
    
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

def process_image_from_url(image_url, title):
    """Process image from URL and return base64 string"""
    try:
        img_data = download_image(image_url)
        if not img_data:
            return None
            
        return process_image(img_data, title)
        
    except Exception as e:
        print(f"Error processing image from URL: {e}")
        return None

def process_image(img_data, text, sharpen=1.5, contrast=1.1):
    """Process image with enhancements and text overlay, return base64 string"""
    try:
        img = Image.open(img_data)
        
        # Resize to target dimensions
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.LANCZOS
        img = img.resize((TARGET_DISPLAY_WIDTH, TARGET_DISPLAY_HEIGHT), resample_filter)
        
        # Get dominant color for text contrast
        try:
            img_data.seek(0)
            color_thief = ColorThief(img_data)
            dominant_color = color_thief.get_color(quality=1)
            text_color = get_contrast_color(dominant_color)
        except:
            text_color = '#000000'
        
        # Convert to RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Enhance image
        img = enhance_image(img, sharpen, contrast)
        
        # Add text overlay
        img = add_text(img, text, color=text_color)
        
        # Convert to base64 and return
        return image_to_base64(img)
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return None