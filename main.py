from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import subprocess, os, uuid, json, base64
from pathlib import Path
from dotenv import load_dotenv

from util.format_data import format_data, do_similarity
from util.save_db import save_news, get_date
from scrape_content.google_scrape import google_search
from google_search.google_search_api import google_search_api
from crawl_using_ai.crawl_images import crawl_4_ai, extract_title_from_url
from crawl_using_ai.image import process_image_from_url
from crawl_using_ai.video import images_to_advanced_video
from crawl_using_ai.music import add_music_to_video_with_defaults
from request.requests import KeywordRequest, GetNewsRequest
from request.SearchResult import SearchResult

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
def crawl_ai(payload: KeywordRequest):
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
    
    return {"status": "success", "urls": urls, "uuid": unique_uuid}

def generate_news_data(data, news_uuid):
    """Generator function to yield news data and create video"""
    formated_output = format_data(data)
    
    # Create unique folder for this request's images
    image_folder = os.path.join("processed_images", news_uuid)
    os.makedirs(image_folder, exist_ok=True)
    image_paths = []
    titles = []  # Store titles for video text overlays
    final_result = []

    # Process first 5 images for 25-second video (or all if less than 5)
    items_to_process = min(5, len(formated_output))
    
    for i, data_item in enumerate(formated_output[:items_to_process]):
        url = data_item['url']
        url_title_tag = extract_title_from_url(url)
        articles = data_item['articles']
        
        best_url, best_title = do_similarity(url_title_tag, articles)
        img_base64 = process_image_from_url(best_url)
        
        # Save image to disk for video generation
        if img_base64 and img_base64.startswith("data:image"):
            try:
                img_data = img_base64.split(",")[1]
                img_bytes = base64.b64decode(img_data)
                img_path = os.path.join(image_folder, f"{i:03d}.png")
                with open(img_path, "wb") as img_file:
                    img_file.write(img_bytes)
                image_paths.append(img_path)
                titles.append(best_title)
            except Exception as e:
                print(f"Error saving image {i}: {e}")
        
        final_data = {
            "url": url,
            "title": url_title_tag['title'],
            "image_title": best_title,
            "image_base_64": img_base64,
            "img_url": best_url
        }
        final_result.append(final_data)
        
        # Yield individual news item
        yield json.dumps(final_data) + "\n"
    
    # Generate video from images with text overlays
    if image_paths:
        try:
            output_video = os.path.join(image_folder, "video.mp4")
            images_to_advanced_video(image_folder, output_video, titles, fps=24)
            
            # Add music to the generated video using music.py utility
            final_video_path = os.path.join(image_folder, "final_video.mp4")
            add_music_to_video_with_defaults(output_video, final_video_path)
            
            # Yield video information
            yield json.dumps({"video_path": final_video_path, "status": "video_complete"}) + "\n"
        except Exception as e:
            print(f"Error generating video: {e}")
            yield json.dumps({"video_path": None, "error": f"Video generation failed: {str(e)}"}) + "\n"
    else:
        yield json.dumps({"video_path": None, "error": "No images available for video generation"}) + "\n"

@app.post("/api/get-news")
def get_news(payload: GetNewsRequest):
    news_uuid = payload.news_uuid
    inout_dir = 'generated_data'
    file_path = os.path.join(inout_dir, news_uuid + '.json')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Return streaming response for real-time updates
            return StreamingResponse(
                generate_news_data(data, news_uuid), 
                media_type="application/json"
            )

    except FileNotFoundError:
        return {"error": "File not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}

@app.post("/api/get-news-sync")
def get_news_sync(payload: GetNewsRequest):
    """Synchronous version that returns all results at once (like original file 1)"""
    news_uuid = payload.news_uuid
    inout_dir = 'generated_data'
    file_path = os.path.join(inout_dir, news_uuid + '.json')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            final_result = []
            formated_output = format_data(data)
            
            for data_item in formated_output:
                url = data_item['url']
                url_title_tag = extract_title_from_url(url)
                articles = data_item['articles']
                
                best_url, best_title = do_similarity(url_title_tag, articles)
                img_base64 = process_image_from_url(best_url)
                
                final_data = {
                    "url": url,
                    "title": url_title_tag['title'],
                    "image_title": best_title,
                    "image_base_64": img_base64,
                    "img_url": best_url
                }
                final_result.append(final_data)
                    
            return final_result

    except FileNotFoundError:
        return {"error": "File not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}