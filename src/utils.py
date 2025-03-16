import os
import openai
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
import time

def timer_decorator(func):
    """Decorator to measure execution time of functions"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        if isinstance(result, dict) and 'error' not in result:
            result['execution_time'] = execution_time
        return result, execution_time
    return wrapper

def create_session():
    """Create and configure a requests session with retry logic"""
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
    session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
    return session

def load_environment():
    """Load environment variables and initialize clients"""
    if not os.getenv("DOCKER_RUNNING"):
        load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    
    client = None
    if api_key:
        client = openai.OpenAI(api_key=api_key)
    
    return api_key, firecrawl_api_key, client