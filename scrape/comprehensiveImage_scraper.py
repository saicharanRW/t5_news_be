import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin, urlparse
import re
import json
import os
import time
from typing import Set, List, Dict
import logging

class ComprehensiveImageScraper:
    def __init__(self, headless=True, wait_time=10):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.headless = headless
        self.wait_time = wait_time
        self.image_urls = set()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self):
        """Setup Selenium WebDriver with optimal settings"""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Enable image loading
        prefs = {
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_setting_values.notifications": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            self.logger.error(f"Failed to setup Chrome driver: {e}")
            return None

    def extract_images_from_html(self, html_content: str, base_url: str) -> Set[str]:
        """Extract images from static HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        images = set()
        
        # Find all img tags
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                images.add(urljoin(base_url, src))
            
            # Check data-src for lazy loading
            data_src = img.get('data-src')
            if data_src:
                images.add(urljoin(base_url, data_src))
                
            # Check other common lazy loading attributes
            for attr in ['data-lazy-src', 'data-original', 'data-url', 'data-img-src']:
                lazy_src = img.get(attr)
                if lazy_src:
                    images.add(urljoin(base_url, lazy_src))
        
        # Find images in CSS background-image
        for element in soup.find_all(attrs={'style': re.compile(r'background-image')}):
            style = element.get('style', '')
            matches = re.findall(r'background-image:\s*url\(["\']?(.*?)["\']?\)', style)
            for match in matches:
                images.add(urljoin(base_url, match))
        
        # Find images in srcset attribute
        for element in soup.find_all(attrs={'srcset': True}):
            srcset = element.get('srcset', '')
            urls = re.findall(r'(https?://[^\s,]+)', srcset)
            for url in urls:
                images.add(url)
        
        return images

    def extract_images_from_css(self, css_content: str, base_url: str) -> Set[str]:
        """Extract images from CSS content"""
        images = set()
        
        # Find all URL references in CSS
        url_pattern = r'url\(["\']?(.*?)["\']?\)'
        matches = re.findall(url_pattern, css_content)
        
        for match in matches:
            if any(ext in match.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp']):
                images.add(urljoin(base_url, match))
        
        return images

    def extract_images_from_js(self, js_content: str, base_url: str) -> Set[str]:
        """Extract images from JavaScript content"""
        images = set()
        
        # Common patterns for images in JavaScript
        patterns = [
            r'["\']([^"\']*\.(?:jpg|jpeg|png|gif|webp|svg|bmp)(?:\?[^"\']*)?)["\']',
            r'src\s*[:=]\s*["\']([^"\']+)["\']',
            r'image\s*[:=]\s*["\']([^"\']+)["\']',
            r'url\s*[:=]\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            for match in matches:
                if any(ext in match.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp']):
                    images.add(urljoin(base_url, match))
        
        return images

    def get_selenium_images(self, url: str) -> Set[str]:
        """Use Selenium to get images including those loaded by JavaScript"""
        driver = self.setup_driver()
        if not driver:
            return set()
        
        images = set()
        
        try:
            self.logger.info(f"Loading page with Selenium: {url}")
            driver.get(url)
            
            # Wait for initial page load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll to load lazy images
            self.scroll_and_wait(driver)
            
            # Extract all image URLs
            img_elements = driver.find_elements(By.TAG_NAME, "img")
            for img in img_elements:
                src = img.get_attribute('src')
                if src and src.startswith('http'):
                    images.add(src)
                
                # Check data attributes
                for attr in ['data-src', 'data-lazy-src', 'data-original', 'data-url']:
                    data_src = img.get_attribute(attr)
                    if data_src and data_src.startswith('http'):
                        images.add(data_src)
            
            # Extract background images
            elements_with_bg = driver.find_elements(By.XPATH, "//*[@style]")
            for element in elements_with_bg:
                style = element.get_attribute('style')
                if style and 'background-image' in style:
                    matches = re.findall(r'url\(["\']?(.*?)["\']?\)', style)
                    for match in matches:
                        if match.startswith('http'):
                            images.add(match)
            
            # Execute JavaScript to find dynamically loaded images
            js_images = driver.execute_script("""
                var images = [];
                var imgElements = document.querySelectorAll('img');
                imgElements.forEach(function(img) {
                    if (img.src) images.push(img.src);
                    if (img.dataset.src) images.push(img.dataset.src);
                });
                
                // Check for images in canvas elements
                var canvases = document.querySelectorAll('canvas');
                canvases.forEach(function(canvas) {
                    try {
                        var dataURL = canvas.toDataURL();
                        if (dataURL) images.push(dataURL);
                    } catch(e) {}
                });
                
                return images;
            """)
            
            for img_url in js_images:
                if img_url and img_url.startswith('http'):
                    images.add(img_url)
        
        except Exception as e:
            self.logger.error(f"Error with Selenium extraction: {e}")
        
        finally:
            driver.quit()
        
        return images

    def scroll_and_wait(self, driver, scroll_pause_time=2):
        """Scroll through the page to trigger lazy loading"""
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            time.sleep(scroll_pause_time)
            
            # Calculate new scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

    def get_static_images(self, url: str) -> Set[str]:
        """Get images using requests and BeautifulSoup"""
        images = set()
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Extract images from HTML
            images.update(self.extract_images_from_html(response.text, url))
            
            # Parse HTML to find CSS and JS files
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract images from linked CSS files
            for link in soup.find_all('link', rel='stylesheet'):
                css_url = link.get('href')
                if css_url:
                    css_url = urljoin(url, css_url)
                    try:
                        css_response = self.session.get(css_url, timeout=10)
                        images.update(self.extract_images_from_css(css_response.text, url))
                    except:
                        pass
            
            # Extract images from inline CSS
            for style in soup.find_all('style'):
                if style.string:
                    images.update(self.extract_images_from_css(style.string, url))
            
            # Extract images from JavaScript files
            for script in soup.find_all('script', src=True):
                js_url = script.get('src')
                if js_url:
                    js_url = urljoin(url, js_url)
                    try:
                        js_response = self.session.get(js_url, timeout=10)
                        images.update(self.extract_images_from_js(js_response.text, url))
                    except:
                        pass
            
            # Extract images from inline JavaScript
            for script in soup.find_all('script'):
                if script.string:
                    images.update(self.extract_images_from_js(script.string, url))
        
        except Exception as e:
            self.logger.error(f"Error with static extraction: {e}")
        
        return images

    def filter_valid_images(self, image_urls: Set[str]) -> List[str]:
        """Filter and validate image URLs"""
        valid_images = []
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico'}
        
        for url in image_urls:
            try:
                # Skip data URLs for now (base64 encoded images)
                if url.startswith('data:'):
                    continue
                
                # Check if URL has image extension or looks like an image
                parsed = urlparse(url)
                path = parsed.path.lower()
                
                # Check extension
                has_extension = any(path.endswith(ext) for ext in image_extensions)
                
                # Check if URL contains image-related keywords
                has_image_keyword = any(keyword in url.lower() for keyword in 
                                     ['image', 'img', 'photo', 'picture', 'thumbnail', 'avatar'])
                
                if has_extension or has_image_keyword:
                    valid_images.append(url)
                else:
                    # Try to verify by checking content-type
                    try:
                        head_response = self.session.head(url, timeout=5)
                        content_type = head_response.headers.get('content-type', '').lower()
                        if 'image' in content_type:
                            valid_images.append(url)
                    except:
                        pass
            
            except Exception as e:
                continue
        
        return list(set(valid_images))

    def scrape_images(self, url: str, use_selenium=True) -> Dict:
        """Main method to scrape all images from a URL"""
        self.logger.info(f"Starting image scraping for: {url}")
        
        all_images = set()
        
        # Get images using static methods
        self.logger.info("Extracting images using static methods...")
        static_images = self.get_static_images(url)
        all_images.update(static_images)
        self.logger.info(f"Found {len(static_images)} images using static methods")
        
        # Get images using Selenium (for JavaScript-loaded content)
        if use_selenium:
            self.logger.info("Extracting images using Selenium...")
            selenium_images = self.get_selenium_images(url)
            all_images.update(selenium_images)
            self.logger.info(f"Found {len(selenium_images)} additional images using Selenium")
        
        # Filter and validate images
        valid_images = self.filter_valid_images(all_images)
        
        result = {
            'url': url,
            'total_images_found': len(valid_images),
            'images': valid_images,
            'static_method_count': len(static_images),
            'selenium_method_count': len(selenium_images) if use_selenium else 0
        }
        
        self.logger.info(f"Scraping completed. Total valid images found: {len(valid_images)}")
        return result

    def download_images(self, image_urls: List[str], download_folder: str = "downloaded_images"):
        """Download images to local folder"""
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        
        downloaded = []
        failed = []
        
        for i, img_url in enumerate(image_urls):
            try:
                response = self.session.get(img_url, timeout=15)
                response.raise_for_status()
                
                # Get file extension
                parsed = urlparse(img_url)
                ext = os.path.splitext(parsed.path)[1]
                if not ext:
                    ext = '.jpg'  # Default extension
                
                filename = f"image_{i+1:04d}{ext}"
                filepath = os.path.join(download_folder, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                downloaded.append({'url': img_url, 'filename': filename})
                self.logger.info(f"Downloaded: {filename}")
                
            except Exception as e:
                failed.append({'url': img_url, 'error': str(e)})
                self.logger.error(f"Failed to download {img_url}: {e}")
        
        return {'downloaded': downloaded, 'failed': failed}


# Usage example
def scrape_content_start(url):
    # Example usage
    scraper = ComprehensiveImageScraper(headless=True)
    
    # Scrape images
    result = scraper.scrape_images(url)
    
    # Print results
    print(f"\n{'='*50}")
    print(f"SCRAPING RESULTS")
    print(f"{'='*50}")
    print(f"URL: {result['url']}")
    print(f"Total images found: {result['total_images_found']}")
    print(f"Static method found: {result['static_method_count']}")
    print(f"Selenium method found: {result['selenium_method_count']}")
    print(f"\nImage URLs:")
    for i, img_url in enumerate(result['images'], 1):
        print(f"{i:3d}. {img_url}")
    
    # # Ask if user wants to download images
    # download = input(f"\nDo you want to download all {len(result['images'])} images? (y/n): ")
    # if download.lower() == 'y':
    #     download_result = scraper.download_images(result['images'])
    #     print(f"\nDownloaded: {len(download_result['downloaded'])} images")
    #     print(f"Failed: {len(download_result['failed'])} images")


if __name__ == "__main__":
    scrape_content_start("https://www.dmk.in/en/resources/events/")