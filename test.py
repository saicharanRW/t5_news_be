from model.SearchResult import SearchResult
import requests, io, gzip
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_image_content(html):
    images = []
    soup = BeautifulSoup(html, "html.parser")
    
    for img in soup.select("img"):
        src = img.get("src") or img.get("data-src")
        alt = img.get("alt", "")
        
        print(src)

if __name__ == '__main__':
    html = ""
    with open("sample.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    get_image_content(html)