import os
from dotenv import load_dotenv
import openai
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"]
)

# Create session with retries
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
session.mount("http://", HTTPAdapter(max_retries=retry_strategy))

if not os.getenv("DOCKER_RUNNING"):
    load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")

client = openai.OpenAI(api_key=api_key) if api_key else None