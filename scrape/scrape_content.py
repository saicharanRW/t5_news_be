from model.SearchResult import SearchResult
import requests, io, gzip
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

base_url = 'https://www.google.com'

def scrape_website_contents(extract_url):
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.10) Gecko/20060927 Firefox/1.0.4 (Debian package 1.0.4-2sarge12)',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip',
        'Referer': base_url
    }
    
    try:
        response = requests.get(SearchResult.getUrl(extract_url), headers=headers, timeout=10)
        if response.headers.get('Content-Encoding') == 'gzip':
            try:
                buf = io.BytesIO(response.content)
                with gzip.GzipFile(fileobj=buf) as gz:
                    html = gz.read().decode('utf-8')
            except (OSError, gzip.BadGzipFile):
                html = response.text
        else:
            html = response.text
            
        text = get_text_content(html)
        images = get_image_content(extract_url, html)
    
    except requests.RequestException as e:
        print('Request failed:', e)
    
    return { "url" : SearchResult.getUrl(extract_url), "title" : SearchResult.getTitle(extract_url), "text" : text, "images" : images }

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
        src = img.get("src") or img.get("data-src")
        alt = img.get("alt", "")
                
        if src and not src.startswith("data:image") and "blank.gif" not in src:
            if not bool(urlparse(src).netloc):
                src = urljoin(SearchResult.getUrl(search_result), src)
            image = { "url": src, "alt": alt }
            images.append(image)
    
    return images

if __name__ == '__main__':
    url = SearchResult()
    url.url = "https://www.atlasobscura.com/places/perarignar-anna-memorial"
    scrape_website_contents(url)