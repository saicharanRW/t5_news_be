import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from crawl_using_ai.image import process_image_from_url

model = SentenceTransformer("all-MiniLM-L6-v2")

def format_data(data):
    formatted_data = []
    
    for entry in data:
        if entry.get("success"):
            valid_articles = [
                {
                    "title": article["title"],
                    "image_src": article["image_src"],
                    "image_alt": article["img_alt_attribute"]
                }
                
                for article in entry.get("data", [])
                if article.get("image_src")
            ]
            
            if valid_articles:
                formatted_data.append({
                    "url": entry["url"],
                    "title": entry['title'],
                    "articles": valid_articles
                })
    
    return formatted_data

def do_similarity(url_title_tag, articles):
    main_title = url_title_tag['title']
    max_similarity = -1
    best_img_src = None

    for article in articles:
        article_title = article.get('title', '')
        similarity = calculate_similarity(main_title, article_title)

        if similarity > max_similarity:
            max_similarity = similarity
            best_img_src = article.get('image_src')
            best_img_title = article.get('title')

    return best_img_src, best_img_title

def calculate_similarity(text1: str, text2: str) -> float:
    embedding1 = model.encode([text1])[0]
    embedding2 = model.encode([text2])[0]
    similarity = cosine_similarity([embedding1], [embedding2])[0][0]
    return float(similarity)


