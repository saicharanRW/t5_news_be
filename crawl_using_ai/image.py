import os
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from colorthief import ColorThief

def get_contrast_color(rgb):
    r, g, b = rgb
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return '#000000' if luminance > 128 else '#FFFFFF'

def enhance_image(image, sharpen, contrast):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    return ImageEnhance.Contrast(ImageEnhance.Sharpness(image).enhance(sharpen)).enhance(contrast)

def get_font(text, max_width, max_height, bold=False):
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

def add_text(image, text, ratio=0.75, color='black', bold=False):
    if not text.strip():
        return image
    
    draw = ImageDraw.Draw(image)
    width, height = image.size
    y = int(height * ratio) + 5
    max_width = width - 10
    max_height = height - y - 10
    
    font = get_font(text, max_width, max_height, bold)
    
    lines = []
    current_line = ''
    
    for word in text.split():
        test_line = f'{current_line} {word}'.strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    y_pos = y + (max_height - len(lines)*font.size) // 2
    for line in lines:
        draw.text((5, y_pos), line, fill=color, font=font)
        y_pos += font.size
    
    return image

def crop_image(image, crop_width=800, crop_height=600):
    # Get current dimensions
    width, height = image.size
    
    # Calculate center crop coordinates
    left = (width - crop_width) // 2 if width > crop_width else 0
    top = (height - crop_height) // 2 if height > crop_height else 0
    right = left + min(width, crop_width)
    bottom = top + min(height, crop_height)
    
    # Crop and return
    return image.crop((left, top, right, bottom))

def process_image(input_path, output_path, text, sharpen, contrast, crop_width=800, crop_height=600):
    try:
        # Get dominant color
        color_thief = ColorThief(input_path)
        dominant_color = color_thief.get_color(quality=1)
        text_color = get_contrast_color(dominant_color)
    except:
        text_color = '#000000'
    
    try:
        with Image.open(input_path) as img:
            # Convert to RGB
            img = img.convert('RGB')
            
            # Crop the image
            img = crop_image(img, crop_width, crop_height)
            
            # Enhance image
            img = enhance_image(img, sharpen, contrast)
            
            # Add visual elements
            img = add_text(img, text, color=text_color)
            
            # Save result
            img.save(output_path)
            print(f"Image saved to {output_path}")
            
    except Exception as e:
        print(f"Error processing image: {e}")

if __name__ == "__main__":
    # Configuration
    INPUT_IMAGE = "name5.webp"
    OUTPUT_IMAGE = "name5_output.png"
    TEXT = "MTC bus accident claims one life; investigation underway."
    SHARPEN = 1.5
    CONTRAST = 1.1
    CROP_WIDTH = 1000  # Default crop width
    CROP_HEIGHT = 800  # Default crop height
    
    process_image(INPUT_IMAGE, OUTPUT_IMAGE, TEXT, SHARPEN, CONTRAST, CROP_WIDTH, CROP_HEIGHT)