from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.save_db import save_news, get_date
from scrape.google_scrape import google_search
from googleSearchApi.google_search_api import google_search_api
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
    query = payload.category + " in " + payload.location + " " + "today latest information"
    print("QUERYING GOOGLE on : " + query)
    result = google_search(query)
    
    return { "result" : result }

@app.post("/api/google-search-api")
def get_news(payload: KeywordRequest):
    query = payload.category + " in " + payload.location + " " + "today latest information"
    result = google_search_api(query)
    
    return { "result" : result }