import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
 
model = SentenceTransformer("all-MiniLM-L6-v2")
 
def scrape_function(data):
    print(data[0])
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
   
    for item in data:
        images = []
        for img in soup.select("article img, .article-body img, .entry-content img, .post-content img"):
            src = img.get("src") or img.get("data-src")
            alt = img.get("alt", "")
            images.append({"src": src, "alt": alt})
           
       
       
def calculate_similarity(text1: str, text2: str) -> float:
    print(f"Calculating similarity between:\n- Text1: {text1[:50]}...\n- Text2: {text2[:50]}...")
    embedding1 = model.encode([text1])[0]
    embedding2 = model.encode([text2])[0]
    similarity = cosine_similarity([embedding1], [embedding2])[0][0]
    return float(similarity)
           
if __name__ == "__main__":
    url = "https://www.theverge.com/news/655371/google-pixel-7a-extended-repair-program-battery-swelling"
    scrape_function(url)