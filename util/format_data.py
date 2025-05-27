import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64

def format_data(data):
    formatted_data = []
    
    for entry in data:
        if entry.get("success"):
            valid_articles = [
                {
                    "title": article["title"],
                    "image_src": article["image_src"]
                }
                
                for article in entry.get("data", [])
                if article.get("image_src")
            ]
            
            if valid_articles:
                formatted_data.append({
                    "url": entry["url"],
                    "articles": valid_articles
                    })
    
    return formatted_data

def generate_image(img_url, title):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(img_url, headers=headers, timeout=10)
        response.raise_for_status()

        img_data = BytesIO(response.content)
        encoded_string = base64.b64encode(img_data.read()).decode('utf-8')

        content_type = response.headers.get('Content-Type', 'image/jpeg')
        base64_image = f"data:{content_type};base64,{encoded_string}"
        return base64_image
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch image from URL {img_url}: {e}")
        return ""

