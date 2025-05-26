from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.save_db import save_news, get_date
from scrape.google_scrape import google_search
from googleSearchApi.google_search_api import google_search_api
from crawl4Ai.crawl_4_ai import crawl_4_ai
from model.request import KeywordRequest

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