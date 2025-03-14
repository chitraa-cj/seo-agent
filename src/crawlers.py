import time
import re
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp
from config import session, firecrawl_api_key
from utils import timer_decorator

# In analysis.py change:
from config import client

@timer_decorator
def fetch_with_beautifulsoup(url, request_timeout):
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
        
        content = " ".join(headings + paragraphs)
        word_count = len(content.split())
        
        links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith(('http://', 'https://'))]
        images = [{'alt': img.get('alt', '')} for img in soup.find_all('img')]
        
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
def fetch_with_firecrawl(url, request_timeout, max_retries, use_proxy):
    try:
        if not firecrawl_api_key:
            return {"error": "Firecrawl API key not found"}
        
        app = FirecrawlApp(api_key=firecrawl_api_key)
        params = {
            'formats': ['markdown', 'html', 'links'],
            'timeout': request_timeout * 1000,
            'proxy': 'basic' if use_proxy else None
        }

        scrape_result = None
        for attempt in range(max_retries):
            try:
                scrape_result = app.scrape_url(url, params=params)
                if scrape_result and 'data' in scrape_result and 'markdown' in scrape_result['data']:
                    break
                time.sleep(2 ** attempt)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)

        if not isinstance(scrape_result, dict) or 'data' not in scrape_result:
            return {"error": "Firecrawl failed to retrieve content"}

        data = scrape_result['data']
        metadata = data.get('metadata', {})
        markdown = data.get('markdown', '')
        
        headings = []
        if markdown:
            for line in markdown.split('\n'):
                if re.match(r'^#+\s', line):
                    headings.append(re.sub(r'^#+\s*', '', line).strip())
                    if len(headings) >= 5:
                        break
        
        word_count = len(markdown.split()) if markdown else 0
        image_count = 0
        images_with_alt = 0
        
        if 'html' in data:
            html_soup = BeautifulSoup(data['html'], 'html.parser')
            images = html_soup.find_all('img')
            image_count = len(images)
            images_with_alt = len([img for img in images if img.get('alt')])

        return {
            "title": metadata.get('title', 'No title found'),
            "meta_description": metadata.get('description', metadata.get('ogDescription', 'No meta description found')),
            "headings": headings[:5],
            "content": markdown[:3000] if markdown else '',
            "word_count": word_count,
            "link_count": len(data.get('links', [])),
            "image_count": image_count,
            "images_with_alt": images_with_alt
        }
        
    except Exception as e:
        return {"error": f"Firecrawl error: {str(e)}"}