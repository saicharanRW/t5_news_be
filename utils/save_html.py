import os, re

def save_html_to_file(url, html_content):
    try:
        output_dir = 'html_output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filename = sanitize_filename(url)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
    except Exception as e:
        print(f"Failed to save HTML for {url}: {e}")
        
def sanitize_filename(url):
    filename = url.replace('https://', '').replace('http://', '')
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    filename = filename.strip('. ')
    
    if len(filename) > 200:
        filename = filename[:200]
    return filename + '.html'