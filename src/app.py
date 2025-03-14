import streamlit as st
import openai
import os
import requests
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import re
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns

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

if api_key:
    client = openai.OpenAI(api_key=api_key)
else:
    client = None

st.title("SEO AI Agent")
st.subheader("Get an AI-generated On-Page SEO report for your website")

# Sidebar settings
st.sidebar.header("Advanced Settings")
max_retries = st.sidebar.slider("Max Retry Attempts", 1, 5, 2)
request_timeout = st.sidebar.slider("Request Timeout (seconds)", 10, 60, 30)
use_proxy = st.sidebar.checkbox("Use Proxy Server")
test_mode = st.sidebar.checkbox("Developer Test Mode", value=False, help="Compare both crawlers with the same content")

niche = st.text_input("Enter your website's niche:")
tagline = st.text_input("Enter your website's tagline:")
website_url = st.text_input("Enter your website URL:")

# Define timer decorator for performance measurement
def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        if isinstance(result, dict) and 'error' not in result:
            result['execution_time'] = execution_time
        return result, execution_time
    return wrapper

@timer_decorator
def fetch_with_beautifulsoup(url):
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
def fetch_with_firecrawl(url):
    try:
        if not firecrawl_api_key:
            return {"error": "Firecrawl API key not found"}
        
        app = FirecrawlApp(api_key=firecrawl_api_key)
        
        # Updated parameters for V1 API
        params = {
            'formats': ['markdown', 'html', 'links'],  # Request multiple formats
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
                
                # Check for data in V1 API response structure
                if (isinstance(scrape_result, dict) and 
                    'data' in scrape_result and 
                    'markdown' in scrape_result['data']):
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
        links = data.get('links', [])

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
            "link_count": len(links) if links else 0,
            "image_count": image_count,
            "images_with_alt": images_with_alt
        }
        
    except Exception as e:
        return {"error": f"Firecrawl error: {str(e)}"}

def evaluate_result_for_openai(data):
    """Evaluate how well the data is suited for OpenAI SEO analysis"""
    if 'error' in data:
        return 0, {"error": data['error']}
    
    scores = {}
    
    # Title quality (0-20 points)
    title = data.get('title', '')
    if title and title != "No title found":
        title_length = len(title)
        if 10 <= title_length <= 60:
            scores['title'] = 20
        elif 5 <= title_length < 10 or 60 < title_length <= 80:
            scores['title'] = 15
        else:
            scores['title'] = 10
    else:
        scores['title'] = 0
    
    # Meta description quality (0-15 points)
    meta = data.get('meta_description', '')
    if meta and meta != "No meta description found":
        meta_length = len(meta)
        if 50 <= meta_length <= 160:
            scores['meta_description'] = 15
        elif 30 <= meta_length < 50 or 160 < meta_length <= 200:
            scores['meta_description'] = 10
        else:
            scores['meta_description'] = 5
    else:
        scores['meta_description'] = 0
    
    # Headings quality (0-15 points)
    headings = data.get('headings', [])
    if headings:
        if len(headings) >= 3:
            scores['headings'] = 15
        elif len(headings) >= 1:
            scores['headings'] = 10
        else:
            scores['headings'] = 5
    else:
        scores['headings'] = 0
    
    # Content quality (0-30 points)
    content = data.get('content', '')
    word_count = data.get('word_count', 0)
    if word_count or content:
        actual_word_count = word_count or len(content.split())
        if actual_word_count >= 500:
            scores['content'] = 30
        elif actual_word_count >= 300:
            scores['content'] = 25
        elif actual_word_count >= 100:
            scores['content'] = 15
        else:
            scores['content'] = 10
    else:
        scores['content'] = 0
    
    # Additional SEO elements (0-20 points)
    additional_score = 0
    if data.get('link_count', 0) > 0:
        additional_score += 10
    if data.get('image_count', 0) > 0:
        additional_score += 5
    if data.get('images_with_alt', 0) > 0:
        additional_score += 5
    scores['additional_elements'] = additional_score
    
    # Performance score based on execution time (0-10 points)
    execution_time = data.get('execution_time', 10)
    if execution_time <= 2:
        scores['performance'] = 10
    elif execution_time <= 5:
        scores['performance'] = 8
    elif execution_time <= 10:
        scores['performance'] = 6
    else:
        scores['performance'] = 4
    
    total_score = sum(scores.values())
    
    # Calculate quality for OpenAI prompt
    openai_quality = {
        "completeness": min(100, total_score / 1.1),  # Scale to 100%
        "detail_scores": scores,
        "strengths": [],
        "weaknesses": []
    }
    
    # Determine strengths and weaknesses
    if scores['title'] >= 15:
        openai_quality["strengths"].append("Strong title extraction")
    elif scores['title'] <= 10:
        openai_quality["weaknesses"].append("Poor title extraction")
        
    if scores['meta_description'] >= 10:
        openai_quality["strengths"].append("Good meta description")
    elif scores['meta_description'] <= 5:
        openai_quality["weaknesses"].append("Weak meta description")
        
    if scores['content'] >= 25:
        openai_quality["strengths"].append("Rich content extraction")
    elif scores['content'] <= 15:
        openai_quality["weaknesses"].append("Limited content extraction")
        
    if scores['headings'] >= 10:
        openai_quality["strengths"].append("Good heading structure")
    else:
        openai_quality["weaknesses"].append("Poor heading extraction")
        
    if scores['additional_elements'] >= 15:
        openai_quality["strengths"].append("Comprehensive additional elements")
    elif scores['additional_elements'] <= 5:
        openai_quality["weaknesses"].append("Missing important SEO elements")
        
    if scores['performance'] >= 8:
        openai_quality["strengths"].append("Excellent performance")
    elif scores['performance'] <= 5:
        openai_quality["weaknesses"].append("Slow extraction time")
    
    return total_score, openai_quality

def run_test_analysis(bs_data, fc_data):
    """Generate test prompts and analyze how OpenAI would respond"""
    if not client:
        return {
            "message": "OpenAI client not available. Please set your API key to run test analysis."
        }
    
    if 'error' in bs_data and 'error' in fc_data:
        return {
            "message": "Both crawlers failed. No test analysis possible."
        }
    
    # Create sample prompts from both crawlers
    bs_prompt = f"""Analyze SEO for a website.
    Title: {bs_data.get('title', 'Not available')}
    Meta Description: {bs_data.get('meta_description', 'Not available')}
    Headings: {bs_data.get('headings', [])}
    Content preview: {bs_data.get('content', 'Not available')[:500]}"""
    
    fc_prompt = f"""Analyze SEO for a website.
    Title: {fc_data.get('title', 'Not available')}
    Meta Description: {fc_data.get('meta_description', 'Not available')}
    Headings: {fc_data.get('headings', [])}
    Content preview: {fc_data.get('content', 'Not available')[:500]}"""
    
    # Evaluate prompt quality with OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in SEO and data quality analysis. Your task is to compare two different sets of website data and determine which would be more effective for SEO analysis. Provide a detailed technical comparison."},
                {"role": "user", "content": f"""Compare these two data extractions from the same website and determine which would be more effective for SEO analysis.
                
                BeautifulSoup Extraction:
                {json.dumps({k: v for k, v in bs_data.items() if k != 'content'}, indent=2)}
                Content length: {len(bs_data.get('content', ''))} characters
                
                Firecrawl Extraction:
                {json.dumps({k: v for k, v in fc_data.items() if k != 'content'}, indent=2)}
                Content length: {len(fc_data.get('content', ''))} characters
                
                Compare them on:
                1. Data completeness and accuracy for SEO analysis
                2. Content extraction quality
                3. Structured data capture
                4. Technical advantages/disadvantages
                5. Which would produce better SEO analysis results and why
                
                Provide your conclusion about which tool a developer should choose for SEO analysis purposes.
                """}
            ],
            max_tokens=1000
        )
        return {
            "message": "Analysis completed successfully",
            "comparison": response.choices[0].message.content,
            "bs_prompt_length": len(bs_prompt),
            "fc_prompt_length": len(fc_prompt)
        }
    except Exception as e:
        return {
            "message": f"Error analyzing data: {str(e)}"
        }

def generate_seo_analysis(data, website_url, niche, tagline):
    """Generate SEO analysis with OpenAI"""
    if not client:
        return {
            "error": "OpenAI API key not found. Please set your API key to generate SEO analysis."
        }
    
    if 'error' in data:
        return {
            "error": f"Cannot generate SEO analysis: {data['error']}"
        }
    
    try:
        # Create a prompt for OpenAI
        prompt = f"""You are an expert SEO consultant analyzing a website for on-page optimization. 
        
        Website URL: {website_url}
        Niche: {niche}
        Tagline: {tagline}
        
        Website data:
        Title: {data.get('title', 'Not available')}
        Meta Description: {data.get('meta_description', 'Not available')}
        Headings: {json.dumps(data.get('headings', []))}
        Word Count: {data.get('word_count', 0)}
        Links: {data.get('link_count', 0)}
        Images: {data.get('image_count', 0)} (with alt text: {data.get('images_with_alt', 0)})
        
        Content excerpt:
        {data.get('content', 'Not available')[:1500]}
        
        Provide a comprehensive SEO analysis including:
        1. Title tag evaluation and suggestions for improvement
        2. Meta description assessment and recommendations
        3. Heading structure analysis
        4. Content quality assessment (uniqueness, relevance, readability)
        5. Internal linking recommendations
        6. Image optimization suggestions
        7. Overall SEO score (out of 100)
        8. Top 3 prioritized action items to improve SEO
        
        Format the response as detailed markdown sections with clear headings.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert SEO consultant providing actionable advice for website optimization."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        
        return {
            "analysis": response.choices[0].message.content,
            "success": True
        }
    except Exception as e:
        return {
            "error": f"Error generating SEO analysis: {str(e)}"
        }

def visualize_crawler_comparison(bs_result, fc_result):
    """Create visualization comparing the two crawlers"""
    if 'error' in bs_result and 'error' in fc_result:
        return None
    
    # Prepare data for visualization
    metrics = ['word_count', 'link_count', 'image_count', 'images_with_alt']
    bs_values = [bs_result.get(metric, 0) for metric in metrics]
    fc_values = [fc_result.get(metric, 0) for metric in metrics]
    
    # Create DataFrame for the visualization
    df = pd.DataFrame({
        'Metric': ['Word Count', 'Link Count', 'Image Count', 'Images with Alt'],
        'BeautifulSoup': bs_values,
        'Firecrawl': fc_values
    })
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(metrics))
    width = 0.35
    
    # Create the bars
    ax.bar([i - width/2 for i in x], bs_values, width, label='BeautifulSoup')
    ax.bar([i + width/2 for i in x], fc_values, width, label='Firecrawl')
    
    # Add labels and title
    ax.set_ylabel('Count')
    ax.set_title('Crawler Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(['Word Count', 'Link Count', 'Image Count', 'Images with Alt'])
    ax.legend()
    
    # Add execution time comparison if available
    bs_time = getattr(bs_result, 'execution_time', 0) if hasattr(bs_result, 'execution_time') else bs_result.get('execution_time', 0)
    fc_time = getattr(fc_result, 'execution_time', 0) if hasattr(fc_result, 'execution_time') else fc_result.get('execution_time', 0)
    
    if bs_time and fc_time:
        time_fig, time_ax = plt.subplots(figsize=(8, 4))
        time_ax.bar(['BeautifulSoup', 'Firecrawl'], [bs_time, fc_time])
        time_ax.set_ylabel('Execution Time (seconds)')
        time_ax.set_title('Crawler Performance Comparison')
        
        return fig, time_fig
    
    return fig, None

# Main function to handle the app workflow
if st.button("Analyze Website"):
    if not website_url:
        st.error("Please enter a website URL")
    else:
        with st.spinner("Analyzing website..."):
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Fetch data with BeautifulSoup
            status_text.text("Fetching data with BeautifulSoup...")
            bs_result, bs_time = fetch_with_beautifulsoup(website_url)
            progress_bar.progress(25)
            
            # Step 2: Fetch data with Firecrawl if in test mode
            fc_result = {"error": "Firecrawl not used"}
            fc_time = 0
            if test_mode:
                status_text.text("Fetching data with Firecrawl...")
                fc_result, fc_time = fetch_with_firecrawl(website_url)
                progress_bar.progress(50)
            else:
                progress_bar.progress(50)
            
            # Step 3: Determine which crawler produced better results
            if test_mode:
                status_text.text("Evaluating crawler results...")
                bs_score, bs_quality = evaluate_result_for_openai(bs_result)
                fc_score, fc_quality = evaluate_result_for_openai(fc_result)
                
                # Create visualization
                fig, time_fig = visualize_crawler_comparison(bs_result, fc_result)
                if fig:
                    st.subheader("Crawler Comparison")
                    st.pyplot(fig)
                if time_fig:
                    st.pyplot(time_fig)
                
                # Show detailed comparison in test mode
                test_analysis = run_test_analysis(bs_result, fc_result)
                
                st.subheader("Crawler Evaluation")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("BeautifulSoup Score", f"{bs_score}/110")
                    st.json(bs_quality)
                
                with col2:
                    st.metric("Firecrawl Score", f"{fc_score}/110")
                    st.json(fc_quality)
                
                if "comparison" in test_analysis:
                    st.subheader("Expert Comparison")
                    st.markdown(test_analysis["comparison"])
                
                # Select the better crawler
                crawler_data = bs_result if bs_score >= fc_score else fc_result
                crawler_name = "BeautifulSoup" if bs_score >= fc_score else "Firecrawl"
                st.info(f"Selected {crawler_name} for SEO analysis based on data quality score.")
            else:
                crawler_data = bs_result
                crawler_name = "BeautifulSoup"
            
            progress_bar.progress(75)
            
            # Step 4: Generate SEO analysis with OpenAI
            status_text.text("Generating SEO analysis...")
            seo_report = generate_seo_analysis(crawler_data, website_url, niche, tagline)
            progress_bar.progress(100)
            
            # Step 5: Display results
            if "error" in seo_report:
                st.error(seo_report["error"])
            else:
                status_text.text("Analysis complete!")
                st.subheader("SEO Analysis Report")
                st.markdown(seo_report["analysis"])
                
                # Export options
                st.subheader("Export Options")
                export_format = st.selectbox("Select Format", ["PDF", "Markdown", "JSON"])
                
                if st.button("Export Report"):
                    if export_format == "Markdown":
                        st.download_button(
                            label="Download Markdown",
                            data=seo_report["analysis"],
                            file_name=f"seo_report_{website_url.replace('https://', '').replace('http://', '').replace('/', '_')}.md",
                            mime="text/markdown"
                        )
                    elif export_format == "JSON":
                        export_data = {
                            "website": website_url,
                            "niche": niche,
                            "tagline": tagline,
                            "raw_data": crawler_data,
                            "seo_analysis": seo_report["analysis"],
                            "generated_date": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.download_button(
                            label="Download JSON",
                            data=json.dumps(export_data, indent=2),
                            file_name=f"seo_report_{website_url.replace('https://', '').replace('http://', '').replace('/', '_')}.json",
                            mime="application/json"
                        )
                    else:
                        st.info("PDF export functionality will be added in a future update.")

# Add helpful information in the sidebar
with st.sidebar:
    st.subheader("How It Works")
    st.markdown("""
    1. Enter your website URL and details above
    2. Our crawler extracts SEO-relevant data
    3. AI analyzes the data and generates recommendations
    4. Review and export your personalized SEO report
    """)
    
    st.subheader("Tips")
    st.markdown("""
    - Provide accurate niche information for better analysis
    - Use Developer Test Mode to compare crawler performance
    - For best results, analyze one page at a time
    """)
    
    # Add a feedback form
    st.subheader("Feedback")
    feedback = st.text_area("Share your thoughts on this tool:")
    if st.button("Submit Feedback"):
        st.success("Thank you for your feedback!")