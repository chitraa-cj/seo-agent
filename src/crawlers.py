from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp
import re
import time
from utils import timer_decorator, create_session

session = create_session()

@timer_decorator
def fetch_with_beautifulsoup(url, request_timeout):
    """Fetch website data using BeautifulSoup"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }
        
        response = session.get(
            url, 
            headers=headers, 
            timeout=request_timeout
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else "No title found"
        meta_description = (soup.find("meta", attrs={"name": "description"}) or 
                          soup.find("meta", attrs={"property": "og:description"}))
        meta_description = meta_description["content"] if meta_description else "No meta description found"
        
        headings = [h.get_text().strip() for h in soup.find_all(["h1", "h2", "h3"])]
        paragraphs = [p.get_text().strip() for p in soup.find_all("p")]
        
        # Count words in content
        content = " ".join(headings + paragraphs)
        word_count = len(content.split())
        
        # Extract links
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith(('http://', 'https://')):
                links.append(href)
        
        # Extract image info
        images = []
        for img in soup.find_all('img'):
            alt_text = img.get('alt', '')
            if alt_text:
                images.append({'alt': alt_text})
        
        return {
            "title": title,
            "meta_description": meta_description,
            "headings": headings[:5],
            "content": content[:3000],
            "word_count": word_count,
            "link_count": len(links),
            "image_count": len(images),
            "images_with_alt": len([img for img in images if img.get('alt')])
        }
    except Exception as e:
        return {"error": f"BeautifulSoup error: {str(e)}"}

@timer_decorator
def fetch_with_firecrawl(url, firecrawl_api_key, max_retries, request_timeout, use_proxy):
    """Fetch website data using Firecrawl V1 API"""
    try:
        if not firecrawl_api_key:
            return {"error": "Firecrawl API key not found"}
        
        app = FirecrawlApp(api_key=firecrawl_api_key)
        
        # Updated parameters for V1 API
        params = {
            'formats': ['markdown', 'html', 'links'],  # Request multiple formats as per V1 API
            'timeout': request_timeout * 1000,  # Convert to milliseconds
        }

        if use_proxy:
            params['proxy'] = 'basic'

        # Retry logic
        scrape_result = None
        for attempt in range(max_retries):
            try:
                # Using V1 API format
                scrape_result = app.scrape_url(url, params=params)
                
                # Since V1 SDK returns the data object directly (according to docs)
                # we don't need to check for 'data' key
                if scrape_result and isinstance(scrape_result, dict):
                    break
                    
                time.sleep(2 ** attempt)
            except Exception as e:
                print(f"Firecrawl attempt {attempt+1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)

        if not isinstance(scrape_result, dict):
            return {"error": "Firecrawl failed to retrieve content"}

        # V1 API returns data object directly through the SDK
        markdown = scrape_result.get('markdown', '')
        links = scrape_result.get('links', [])
        metadata = scrape_result.get('metadata', {})
        html_content = scrape_result.get('html', '')

        # Extract headings from markdown
        headings = []
        if markdown:
            for line in markdown.split('\n'):
                if re.match(r'^#+\s', line):
                    heading = re.sub(r'^#+\s*', '', line).strip()
                    headings.append(heading)
                    if len(headings) >= 5:
                        break
        
        # Count words in markdown content
        word_count = len(markdown.split()) if markdown else 0
        
        # Extract image information from HTML if available
        image_count = 0
        images_with_alt = 0
        if html_content:
            html_soup = BeautifulSoup(html_content, 'html.parser')
            images = html_soup.find_all('img')
            image_count = len(images)
            images_with_alt = len([img for img in images if img.get('alt')])

        return {
            "title": metadata.get('title', 'No title found'),
            "meta_description": metadata.get('description', metadata.get('ogDescription', 'No meta description found')),
            "headings": headings[:5],
            "content": markdown[:3000] if markdown else '',
            "word_count": word_count,
            "link_count": len(links) if links else 0,
            "image_count": image_count,
            "images_with_alt": images_with_alt
        }
        
    except Exception as e:
        return {"error": f"Firecrawl error: {str(e)}"}