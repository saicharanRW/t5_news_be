import requests, io, gzip, re, os
from bs4 import BeautifulSoup

from scrape.scrape_content import scrape_website_contents
from model.SearchResult import SearchResult

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
SCRAPE_TOP_COUNT = int(os.getenv("SCRAPE_TOP_COUNT"))
            
def extractUrl(href):
    match = re.search(r'(https?://[^&]+)&', href)
    return match.group(1) if match else ''

def extractSearchResults(html):
    extracted_urls = []
    soup = BeautifulSoup(html, 'html.parser')
    div = soup.find('div', id='main') or soup.find('div', id='center_col') or soup.find('body')
    
    if div:
        links = div.find_all('a', href=True)
        for link in links:
            raw_href = link['href']
            if ".google." in raw_href:
                continue
            url = extractUrl(raw_href)
            if not url:
                continue
            title = link.get_text(strip=True)
            result = SearchResult()
            result.url = url
            result.title = title
            span = link.find('div')
            result.content = span.get_text(strip=True) if span else ''
            extracted_urls.append(result)
    
    return extracted_urls

def google_search(query):
    query_encoded = requests.utils.quote(query)
    url = f"{BASE_URL}/search?q={query_encoded}"
    print("google search url ", url)
    
    url_contents = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.10) Gecko/20060927 Firefox/1.0.4 (Debian package 1.0.4-2sarge12)',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip',
        'Referer': BASE_URL
    }
    
    try:
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
            
        extracted_urls = extractSearchResults(html)
        
        for extract_url in extracted_urls[:SCRAPE_TOP_COUNT]:
            url_content = scrape_website_contents(extract_url)
            url_contents.append(url_content)
            
    except requests.RequestException as e:
        print('Request failed:', e)
        
    return url_contents

if __name__ == '__main__':
    google_search("politics in hyderbad latest information")