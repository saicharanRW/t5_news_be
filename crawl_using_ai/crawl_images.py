import json
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import List
from scrape_content.google_scrape import google_search
from request.SearchResult import SearchResult
import time
import random
from urllib.parse import urljoin

class Product(BaseModel):
    title: str

def extract_title_and_image_from_html(html_content, url):
    """Extract title and image URL from HTML content using BeautifulSoup"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # --- Extract Title ---
        title = None
        title_tag = soup.find('title')
        if title_tag and title_tag.text.strip():
            title = title_tag.text.strip()

        if not title:
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                title = og_title.get('content').strip()

        if not title:
            h1_tag = soup.find('h1')
            if h1_tag and h1_tag.text.strip():
                title = h1_tag.text.strip()

        if not title:
            article_title_selectors = [
                '.article-title', '.post-title', '.entry-title',
                '.headline', '.title', '[class*="title"]', '[class*="headline"]'
            ]
            for selector in article_title_selectors:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    title = element.text.strip()
                    break

        if not title:
            title = "Title not found"

        # --- Extract Image URL ---
        image_url = None

        # Method 1: og:image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = og_image.get('content').strip()

        # Method 2: first <img> tag
        if not image_url:
            img_tag = soup.find('img')
            if img_tag and img_tag.get('src'):
                image_url = img_tag.get('src').strip()

        # Normalize relative image URLs
        if image_url and image_url.startswith('/'):
            image_url = urljoin(url, image_url)

        return {
            "title": title,
            "image": image_url if image_url else "Image not found"
        }

    except Exception as e:
        print(f"Error parsing HTML for {url}: {e}")
        return {
            "title": f"Error parsing content: {str(e)}",
            "image": "Error"
        }

def fetch_url_content(url, timeout=10):
    """Fetch content from URL with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_title_from_url(url):
    """Extract title and image from a single URL"""
    print(f"Processing: {url}")
    time.sleep(random.uniform(0.5, 1.5))  # polite scraping delay

    try:
        html_content = fetch_url_content(url)
        if html_content:
            result = extract_title_and_image_from_html(html_content, url)
            return result
        else:
            return {"title": "Failed to fetch content", "image": "N/A"}
    except Exception as e:
        print(f"Exception occurred for {url}: {e}")
        return {"title": f"Exception: {str(e)}", "image": "N/A"}

def process_urls_sync(urls):
    results = []
    for i, url in enumerate(urls):
        print(f"\n--- Processing URL {i+1}/{len(urls)} ---")
        print(f"URL: {url}")

        result = extract_title_from_url(url)
        title = result["title"]
        image = result["image"]

        print(f"Title: {title}")
        print(f"Image URL: {image}")
        print("-" * 50)

        results.append({
            "url": url,
            "title": title,
            "image": image,
            "status": "success" if "Error" not in title and "Failed" not in title and "Exception" not in title else "error"
        })

    return results

def crawl_4_ai(query):
    """Main function to search and extract titles and images from URLs"""
    print(f"Searching for: {query}")
    print("=" * 60)

    try:
        # Get URLs from Google search
        extracted_urls = google_search(query, "crawl-ai")
        urls = []

        for extracted_url in extracted_urls:
            url = SearchResult.getUrl(extracted_url)
            urls.append(url)
            print(f"Found URL: {url}")

        if not urls:
            print("No URLs found to process.")
            return {
                "query": query,
                "urls_found": 0,
                "results": [],
                "message": "No URLs found"
            }

        print(f"\nProcessing {len(urls)} URLs...")
        print("=" * 60)

        # Process URLs synchronously
        results = process_urls_sync(urls)

        # Summary
        successful = len([r for r in results if r["status"] == "success"])
        failed = len(results) - successful

        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"Total URLs processed: {len(results)}")
        print(f"Successful extractions: {successful}")
        print(f"Failed extractions: {failed}")
        print(f"{'='*60}")

        return {
            "query": query,
            "urls_found": len(urls),
            "urls_processed": len(results),
            "successful_extractions": successful,
            "failed_extractions": failed,
            "results": results
        }

    except Exception as e:
        error_msg = f"Error in crawl_4_ai: {str(e)}"
        print(error_msg)
        return {
            "query": query,
            "urls_found": 0,
            "results": [],
            "error": error_msg
        }

# Async version for FastAPI (if needed)
async def crawl_4_ai_async(query):
    """Async wrapper that runs sync function in thread pool"""
    import asyncio
    import concurrent.futures

    # Run the sync function in a thread pool
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, crawl_4_ai, query)

    return result

# Example usage
if __name__ == "__main__":
    result = crawl_4_ai("latest technology news")
    print("\nFinal Result:")
    print(json.dumps(result, indent=2))