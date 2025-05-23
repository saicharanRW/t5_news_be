import requests
import os
from dotenv import load_dotenv

load_dotenv()

def fetch_news_catagory(category):
    CATEGORY_NEWS_API_KEY = os.getenv("CATEGORY_NEWS_API_KEY")
    if not CATEGORY_NEWS_API_KEY:
        raise Exception("CATEGORY_NEWS_API_KEY environment variable is not set")
    
    url = f"https://api.mediastack.com/v1/news?access_key={CATEGORY_NEWS_API_KEY}&keywords={category}&countries=in"
    response = requests.get(url, timeout=30)
        
    if response.status_code != 200:
        raise Exception(f"MediaStack API returned status code {response.status_code}")
    data = response.json()
       
    return data

def fetch_news_location(location):
    LOCATION_NEWS_API_KEY = os.getenv("LOCATION_NEWS_API_KEY")
    if not LOCATION_NEWS_API_KEY:
        raise Exception("LOCATION_NEWS_API_KEY environment variable is not set")
    
    url = f"https://newsapi.org/v2/everything?q={location}&sortBy=popularity&apiKey={LOCATION_NEWS_API_KEY}"
    response = requests.get(url, timeout=30)
        
    if response.status_code != 200:
        raise Exception(f"News API returned status code {response.status_code}")
    data = response.json()
    
    return data