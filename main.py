from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess, os, uuid

from util.save_db import save_news, get_date
from scrape_content.google_scrape import google_search
from google_search.google_search_api import google_search_api
from crawl_using_ai.crawl_images import crawl_4_ai
from crawl_using_ai.image import process_image_from_url
from request.requests import KeywordRequest
from request.SearchResult import SearchResult
from pathlib import Path
from dotenv import load_dotenv

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
    query = "latest news about " + payload.category + " in " + payload.location
    print("GOOGLE SEARCH API : " + query)
    result = google_search(query, "crawl-ai")
    
    urls = []
    unique_euuid = str(uuid.uuid4())
    
    for res in result[:SCRAPE_TOP_COUNT]:
        url = SearchResult.getUrl(res)
        urls.append(url)
            
    result_script = str(Path(__file__).parent / "crawl_using_ai/crawl_ai_main.py")
    command = ["python", result_script] + urls + [unique_euuid]
    
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running result.py: {e}")
    
    return {"status": "success", "urls": urls}
        