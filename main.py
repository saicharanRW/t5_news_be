from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess, os, uuid, json
from pathlib import Path
from dotenv import load_dotenv

from util.format_data import format_data, do_similarity
from crawl_using_ai.crawl_images import extract_title_from_url
from crawl_using_ai.image import process_image_from_url
from crawl_using_ai.video import images_to_advanced_video
from request.requests import KeywordRequest, GetNewsRequest

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.post("/api/crawl-ai")
def crawl_ai(payload: KeywordRequest):
    if not payload.location:
        query = f"latest news about {payload.category}"
    else:
        query = f"latest news about {payload.category} in {payload.location}"

    # This would call your actual search function
    # result = google_search(query, "crawl-ai")
    result = []  # Placeholder
    
    urls = []
    unique_uuid = str(uuid.uuid4())
    
    # This would process actual search results
    # for res in result:
    #     urls.append(SearchResult.getUrl(res))
    urls = ["https://example.com"]  # Placeholder
            
    result_script = str(Path(__file__).parent / "crawl_using_ai/crawl_ai_main.py")
    command = ["python", result_script] + urls + [unique_uuid]
    
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running result.py: {e}")
    
    return {"status": "success", "uuid": unique_uuid}

@app.post("/api/get-news")
def get_news(payload: GetNewsRequest):
    news_uuid = payload.news_uuid
    inout_dir = 'generated_data'
    file_path = os.path.join(inout_dir, news_uuid + '.json')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            formated_output = format_data(data)
            
            # Create unique folder for this request's images
            image_folder = os.path.join("processed_images", news_uuid)
            os.makedirs(image_folder, exist_ok=True)
            image_paths = []
            titles = []  # Store titles for video text overlays

            # Process first 5 images for 25-second video
            for i, data in enumerate(formated_output[:5]):
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
                    img_path = os.path.join(image_folder, f"{i:03d}.png")
                    with open(img_path, "wb") as img_file:
                        img_file.write(img_bytes)
                    image_paths.append(img_path)
                    titles.append(best_title)
                
                yield {
                    "url": url,
                    "title": url_title_tag['title'],
                    "image_title": best_title,
                    "image_base_64": img_base64,
                    "img_url": best_url
                }
            
            # Generate video from images with text overlays
            if image_paths:
                output_video = os.path.join(image_folder, "video.mp4")
                images_to_advanced_video(image_folder, output_video, titles, fps=24)
                yield {"video_path": output_video}
            else:
                yield {"video_path": None}

    except FileNotFoundError:
        yield {"error": "File not found"}
    except json.JSONDecodeError:
        yield {"error": "Invalid JSON format"}