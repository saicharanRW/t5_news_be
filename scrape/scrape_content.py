from model.SearchResult import SearchResult
import requests, io, gzip, os, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from utils.save_html import save_html_to_file
from utils.main_img_finder import find_main_img 
from scrape.comprehensiveImage_scraper import ComprehensiveImageScraper

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
SAVE_HTML = os.getenv("SAVE_HTML")

def scrape_website_contents(extract_url):
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.10) Gecko/20060927 Firefox/1.0.4 (Debian package 1.0.4-2sarge12)',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip',
        'Referer': BASE_URL
    }
    
    text = ""
    images = []
    html = ""
    
    try:
        url = SearchResult.getUrl(extract_url)
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.headers.get('Content-Encoding') == 'gzip':
            try:
                buf = io.BytesIO(response.content)
                with gzip.GzipFile(fileobj=buf) as gz:
                    html = gz.read().decode('utf-8')
            except (OSError, gzip.BadGzipFile):
                html = response.text
        else:
            html = response.text
        
        if SAVE_HTML == "true":
            save_html_to_file(url, html)
            
        text = get_text_content(html)
        #images = get_image_content(extract_url, html)
        
        scrapper = ComprehensiveImageScraper(headless=True)
        images = scrapper.scrape_images(url)
        
        #scraped_content = { "url" : SearchResult.getUrl(extract_url), "title" : SearchResult.getTitle(extract_url), "text" : text, "images" : images }
        #final_scraped_content = find_main_img(scraped_content)
        
    except requests.RequestException as e:
        print('Request failed:', e)
    
    return { "url" : SearchResult.getUrl(extract_url), "title" : SearchResult.getTitle(extract_url), "text" : text , "images" : images["images"] }

def get_text_content(html):
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.select("article p, .article-body p, .entry-content p, .post-content p")
    
    if not paragraphs:
        paragraphs = []
        for p in soup.find_all("p"):
            if not p.find_parents(["nav", "footer", "header", "aside"]):
                paragraphs.append(p)
                        
    return "\n\n".join(p.get_text().strip() for p in paragraphs if p.get_text().strip())

def get_image_content(search_result ,html):
    images = []
    soup = BeautifulSoup(html, "html.parser")
    
    for img in soup.select("img"):
        src = img.get("src", "")
        data_src = img.get("data-src", "")
        alt = img.get("alt", "")
                
        if src and not src.startswith("data:image") and "blank.gif" not in src and not src.endswith(".cms"):
            if not bool(urlparse(src).netloc):
                src = urljoin(SearchResult.getUrl(search_result), src)
            image = { "url": src, "data_src": data_src, "alt": alt }
            images.append(image)
    
    return images

if __name__ == '__main__':
    url = SearchResult()
    url.url = "https://cio.economictimes.indiatimes.com/tag/chennai"
    scrape_website_contents(url)