import os, requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

def google_search_api(query):
    
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q={query}"
    print(url)
    response = requests.get(url, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"MediaStack API returned status code {response.status_code}")
    data = response.json()
    
    result = data.get("items")
    search_result = format_items(result)
    
    return search_result

def format_items(items):
    
    formated_items= []
    
    for item in items:
        pagemap = item.get("pagemap", {})
        metatags = pagemap.get("metatags", [])
        image = metatags[0].get("og:image") if metatags else None
        
        transformated_item = {
            "title": item.get("title"),
            "url": item.get("link"),
            "description": item.get("snippet"),
            "urlToImage": image
        }
        
        formated_items.append(transformated_item)
        
    return formated_items
