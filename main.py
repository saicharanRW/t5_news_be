from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess, os, uuid, json
from fastapi.responses import StreamingResponse

from util.format_data import format_data, do_similarity
from util.save_db import save_news, get_date
from scrape_content.google_scrape import google_search
from google_search.google_search_api import google_search_api
from crawl_using_ai.crawl_images import crawl_4_ai
from crawl_using_ai.image import process_image_from_url
from request.requests import KeywordRequest, GetNewsRequest
from request.SearchResult import SearchResult
from crawl_using_ai.crawl_images import extract_title_from_url
from pathlib import Path
from dotenv import load_dotenv
from crawl_using_ai.video import images_to_advanced_video

load_dotenv()

SCRAPE_TOP_COUNT = int(os.getenv("SCRAPE_TOP_COUNT"))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
    
@app.post("/api/cata-loco")
def get_news(payload: KeywordRequest):
    query = "latest news about " + payload.category + " in " + payload.location
    print("QUERYING GOOGLE on : " + query)
    result = google_search(query, "basic")
    
    return { "result" : result }

@app.post("/api/google-search-api")
def get_news(payload: KeywordRequest):
    query = "today latest news about " + payload.category + " in " + payload.location
    print("GOOGLE SEARCH API : " + query)
    result = google_search_api(query)
    
    return { "result" : result }

@app.post("/api/crawl-4-ai")
def get_news(payload: KeywordRequest):
    query = "latest news about " + payload.category + " in " + payload.location
    print("GOOGLE SEARCH API : " + query)
    result = crawl_4_ai(query)
    return { "result" : result }

@app.post("/api/crawl-ai")
def get_news(payload: KeywordRequest):
    if len(payload.location) == 0:
        query = "latest news about " + payload.category
    else:
        query = "latest news about " + payload.category + " in " + payload.location

    print("GOOGLE SEARCH API : " + query)
    result = google_search(query, "crawl-ai")
    
    urls = []
    unique_uuid = str(uuid.uuid4())
    print("UUID :", unique_uuid)
    
    for res in result:
        url = SearchResult.getUrl(res)
        urls.append(url)
            
    result_script = str(Path(__file__).parent / "crawl_using_ai/crawl_ai_main.py")
    command = ["python", result_script] + urls + [unique_uuid]
    
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running result.py: {e}")
    
    return {"status": "success", "urls": urls, "uuid" : unique_uuid}

@app.post("/api/get-news")
def get_news(payload: GetNewsRequest):
    news_uuid = payload.news_uuid
    
    inout_dir = 'generated_data'
    file_path = os.path.join(inout_dir, news_uuid + '.json')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            final_result = []
            formated_output = format_data(data)
            
            image_folder = "processed_images"
            os.makedirs(image_folder, exist_ok=True)
            image_paths = []

            for data in formated_output:
                url = data['url']
                url_title_tag = extract_title_from_url(url)
                articles = data['articles']
                
                best_url, best_title = do_similarity(url_title_tag, articles)
                img_base64 = process_image_from_url(best_url)
                
                # Save image to disk for video generation
                if img_base64 and img_base64.startswith("data:image"):
                    import base64
                    img_data = img_base64.split(",")[1]
                    img_bytes = base64.b64decode(img_data)
                    img_path = os.path.join(image_folder, f"{len(image_paths):03d}.png")
                    with open(img_path, "wb") as img_file:
                        img_file.write(img_bytes)
                    image_paths.append(img_path)
                
                final_data = {
                    "url" : url,
                    "title" : url_title_tag['title'],
                    "image_title" : best_title,
                    "image_base_64" : img_base64,
                    "img_url" : best_url
                }
                final_result.append(final_data)
            
            # Generate video from images
            if image_paths:
                output_video = os.path.join(image_folder, f"{news_uuid}.mp4")
                images_to_advanced_video(image_folder, output_video, fps=24)
            else:
                output_video = None

            return {
                "news": final_result,
                "video_path": output_video
            }

    except FileNotFoundError:
        return {"error": "File not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}

