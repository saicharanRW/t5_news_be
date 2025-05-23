from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from news_apis_call import news
from utils.process_data import process_catagory_data, process_location_data
from utils.save_db import save_news, get_date

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class NewsRequest(BaseModel):
    category: str
    location: str

@app.post("/api/getnews")
def get_news(payload: NewsRequest):
    print("Getting news")
    
    catagory = news.fetch_news_catagory(payload.category)
    location = news.fetch_news_location(payload.location)
    
    catagory = catagory.get("data")
    location = location.get("articles")
    
    print("processing data........")
    processed_catagory = process_catagory_data(catagory)   
    processed_location = process_location_data(location)
    
    print("saving to convex........")
    for news_item in processed_catagory:
        save_news(news_item)
        
    for news_item in processed_location:
        save_news(news_item)
    
    return {
        "allnews" : processed_catagory + processed_location,
    }