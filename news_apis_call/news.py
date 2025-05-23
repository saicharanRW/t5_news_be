import requests

def fetch_news_catagory(category):
    
    #CATEGORY_NEWS_API_KEY="c6cc13ae7dee751def8b74bfffb5e8ef"
    CATEGORY_NEWS_API_KEY = "33be38c7b8aa9403f5e327301762f97d"
    
    url = f"https://api.mediastack.com/v1/news?access_key={CATEGORY_NEWS_API_KEY}&keywords={category}&countries=in"
    response = requests.get(url, timeout=30)
        
    if response.status_code != 200:
        raise Exception(f"MediaStack API returned status code {response.status_code}")
    data = response.json()
       
    return data

def fetch_news_location(location):
    
    #LOCATION_NEWS_API_KEY="449b755df6c249188566416de202b0c8"
    LOCATION_NEWS_API_KEY = "a837104deb8f41ef899080df562f119d"
    
    url = f"https://newsapi.org/v2/everything?q={location}&sortBy=popularity&apiKey={LOCATION_NEWS_API_KEY}"
    response = requests.get(url, timeout=30)
        
    if response.status_code != 200:
        raise Exception(f"News API returned status code {response.status_code}")
    data = response.json()
    
    return data