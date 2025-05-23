from convex import ConvexClient

CONVEX_URL = "https://accomplished-bullfrog-477.convex.cloud"
client = ConvexClient(CONVEX_URL)

def save_news(news_data):
    """Save a single news item to Convex database"""
    client.mutation('news_table:saveNews', news_data)
    
def get_date():
    
    allnews = client.query('news_table:get')
    print(allnews) 

if __name__ == "__main__":
    
    news_items = [
    {
        "author": "John Doe",
        "category": "Technology",
        "country": "US",
        "description": "Latest tech news description",
        "urlToImage": "https://example.com/image1.jpg",
        "language": "en",
        "publishedAt": "2024-01-15T10:30:00Z",
        "source": "Tech News",
        "title": "AI Revolution in 2024",
        "url": "https://example.com/news1"
    }
    ]
    
    for news in news_items:
        print("start")
        get_date()
        save_news(news)