import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64

from crawl_using_ai.image import process_image_from_url

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
    base64_image = process_image_from_url(img_url, title)
    return base64_image


