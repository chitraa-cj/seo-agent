# src/__init__.py
# Package initialization
__version__ = "1.0.0"
__all__ = ["app", "config", "crawlers", "analysis", "visualization", "utils"]

# Optional: Explicit exports for cleaner imports
from .crawlers import fetch_with_beautifulsoup, fetch_with_firecrawl
from .analysis import evaluate_result_for_openai, generate_seo_analysis
from .visualization import visualize_crawler_comparison