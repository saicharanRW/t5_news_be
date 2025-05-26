import os, sys
import asyncio
import json
from pydantic import BaseModel
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class Product(BaseModel):
    title: str


async def crawl_single_url(url: str):
    """
    Crawl a single URL and extract the news title
    """
    # 1. Define the LLM extraction strategy with Gemini
    llm_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="gemini/gemini-1.5-flash", 
            api_token="AIzaSyBmztqQ6Rmk7Rzmcx1VyCeE86KrKw4rhUw"  # or GEMINI_API_KEY
        ),
        schema=Product.model_json_schema(),  # Updated method name
        extraction_type="schema",
        instruction="""Your are provided with a news article url, get the title of the news the article talks about""",
        chunk_token_threshold=1000,
        overlap_rate=0.0,
        apply_chunking=True,
        input_format="markdown",   # or "html", "fit_markdown"
        extra_args={"temperature": 0.0, "max_tokens": 800}
    )
    
    # 2. Build the crawler config
    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        cache_mode=CacheMode.BYPASS
    )
    
    # 3. Create a browser config if needed
    browser_cfg = BrowserConfig(headless=True)
    
    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            # 4. Crawl the provided URL
            result = await crawler.arun(
                url=url,
                config=crawl_config
            )
            if result.success:
                # 5. The extracted content is presumably JSON
                try:
                    data = json.loads(result.extracted_content)
                    return {
                        "success": True,
                        "url": url,
                        "data": data,
                        "title": data.get("title", "") if isinstance(data, dict) else ""
                    }
                        
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "url": url,
                        "error": f"Failed to parse JSON: {str(e)}",
                        "raw_content": result.extracted_content
                    }
                    
            else:
                return {
                    "success": False,
                    "url": url,
                    "error": result.error_message
                }
                
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": f"Crawler exception: {str(e)}"
        }


async def crawl_multiple_urls(urls: List[str]):
    print("jhfjshiufiahfiuhf ", urls)
    """
    Crawl multiple URLs concurrently and extract news titles
    """
    tasks = [crawl_single_url(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions that occurred
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                "success": False,
                "url": urls[i],
                "error": f"Task exception: {str(result)}"
            })
        else:
            processed_results.append(result)
    
    return processed_results


async def main(url):
    """
    Original main function for testing
    """
    url = url
    result = await crawl_single_url(url)
    
    return result


if __name__ == "__main__":
    urls = sys.argv[1:]
    final_data_output = []
        
    for url in urls:
        result = asyncio.run(main(url))
        final_data_output.append(result)
    
    with open('scraped_content.json', 'w', encoding='utf-8') as f:
        json.dump(final_data_output, f, indent=4, ensure_ascii=False)
        
    print("FINISHED")
    
    