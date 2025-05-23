def process_catagory_data(category, max_count=5):
    transformed_articles = []
    for article in category:
        transformed_article = {
            "source": article.get("source", "Unknown"),
            "author": article.get("author"),
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("url"),
            "urlToImage": article.get("image"),
            "publishedAt": article.get("published_at"),
            "category": article.get("category"),
            "language": article.get("language"),
            "country": article.get("country")
        }
        transformed_articles.append(transformed_article)
        if len(transformed_articles) >= max_count:
            break
        
    return transformed_articles 
    
def process_location_data(location, max_count=5):
    transformed_articles = []
    for article in location:
        transformed_article = {
            "source": article.get("source", "Unknown"),
            "author": article.get("author"),
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("url"),
            "urlToImage": article.get("urlToImage"),
            "publishedAt": article.get("publishedAt"),
            "category": article.get("category"),
            "language": article.get("language"),
            "country": article.get("country")
        }
        transformed_articles.append(transformed_article)
        if len(transformed_articles) >= max_count:
            break
        
    return transformed_articles 

def process_catagory_location_data(category, max_count=5):
    transformed_articles = []
    for article in category:
        transformed_article = {
            "source": article.get("source", "Unknown"),
            "author": article.get("author"),
            "title": article.get("title"),
            "description": article.get("summary"),
            "url": article.get("url"),
            "urlToImage": article.get("image"),
            "publishedAt": article.get("publish_date"),
            "category": article.get("category"),
            "language": article.get("language"),
            "country": article.get("source_country")
        }
        transformed_articles.append(transformed_article)
        # if len(transformed_articles) >= max_count:
        #     break
        
    return transformed_articles 