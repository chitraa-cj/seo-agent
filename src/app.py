import streamlit as st
from crawlers import fetch_with_beautifulsoup, fetch_with_firecrawl
from analysis import evaluate_result_for_openai
from visualization import visualize_crawler_comparison
from utils import load_environment
import json

# Load environment variables
api_key, firecrawl_api_key, client = load_environment()

st.title("Web Crawler Performance Comparison")
st.subheader("Evaluate BeautifulSoup vs Firecrawl for SEO data extraction")

# Sidebar settings
st.sidebar.header("Settings")
max_retries = st.sidebar.slider("Max Retry Attempts", 1, 5, 2)
request_timeout = st.sidebar.slider("Request Timeout (seconds)", 10, 60, 30)
use_proxy = st.sidebar.checkbox("Use Proxy Server")

website_url = st.text_input("Enter your website URL to compare crawlers:")

if st.button("Compare Crawlers"):
    if not website_url:
        st.error("Please enter a website URL")
    else:
        with st.spinner("Comparing crawlers..."):
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Fetch data with BeautifulSoup
            status_text.text("Fetching data with BeautifulSoup...")
            bs_result, bs_time = fetch_with_beautifulsoup(website_url, request_timeout)
            progress_bar.progress(30)
            
            # Show BeautifulSoup results
            st.subheader("BeautifulSoup Results")
            if "error" in bs_result:
                st.error(f"BeautifulSoup error: {bs_result['error']}")
            else:
                st.success(f"BeautifulSoup completed in {bs_time:.2f} seconds")
                st.json({k: v for k, v in bs_result.items() if k != 'content'})
                
                with st.expander("Content Preview"):
                    st.text(bs_result.get('content', '')[:500])
            
            # Step 2: Fetch data with Firecrawl
            status_text.text("Fetching data with Firecrawl...")
            if not firecrawl_api_key:
                st.warning("Firecrawl API key not found. Skipping Firecrawl test.")
                fc_result = {"error": "Firecrawl API key not found"}
                fc_time = 0
            else:
                fc_result, fc_time = fetch_with_firecrawl(website_url, firecrawl_api_key, max_retries, 
                                                      request_timeout, use_proxy)
            progress_bar.progress(60)
            
            # Show Firecrawl results
            st.subheader("Firecrawl Results")
            if "error" in fc_result:
                st.error(f"Firecrawl error: {fc_result['error']}")
            else:
                st.success(f"Firecrawl completed in {fc_time:.2f} seconds")
                st.json({k: v for k, v in fc_result.items() if k != 'content'})
                
                with st.expander("Content Preview"):
                    st.text(fc_result.get('content', '')[:500])
            
            # Step 3: Evaluate and compare results
            status_text.text("Evaluating crawler results...")
            
            if "error" not in bs_result or "error" not in fc_result:
                bs_score, bs_quality = evaluate_result_for_openai(bs_result)
                fc_score, fc_quality = evaluate_result_for_openai(fc_result)
                
                # Create visualization
                fig, time_fig = visualize_crawler_comparison(bs_result, fc_result)
                if fig:
                    st.subheader("Data Extraction Comparison")
                    st.pyplot(fig)
                if time_fig:
                    st.subheader("Performance Comparison")
                    st.pyplot(time_fig)
                
                # Show evaluation scores
                st.subheader("Crawler Evaluation")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("BeautifulSoup Quality Score", f"{bs_score}/110")
                    with st.expander("BeautifulSoup Quality Details"):
                        st.json(bs_quality)
                
                with col2:
                    st.metric("Firecrawl Quality Score", f"{fc_score}/110")
                    with st.expander("Firecrawl Quality Details"):
                        st.json(fc_quality)
                
                # Final recommendation
                st.subheader("Recommendation")
                if bs_score > fc_score:
                    st.info(f"BeautifulSoup performed better with a score of {bs_score}/110 compared to Firecrawl's {fc_score}/110.")
                    if bs_time > fc_time:
                        st.warning(f"However, BeautifulSoup was slower ({bs_time:.2f}s vs {fc_time:.2f}s).")
                elif fc_score > bs_score:
                    st.info(f"Firecrawl performed better with a score of {fc_score}/110 compared to BeautifulSoup's {bs_score}/110.")
                    if fc_time > bs_time:
                        st.warning(f"However, Firecrawl was slower ({fc_time:.2f}s vs {bs_time:.2f}s).")
                else:
                    if bs_time < fc_time:
                        st.info(f"Both crawlers performed equally well with a score of {bs_score}/110, but BeautifulSoup was faster.")
                    elif fc_time < bs_time:
                        st.info(f"Both crawlers performed equally well with a score of {bs_score}/110, but Firecrawl was faster.")
                    else:
                        st.info(f"Both crawlers performed equally well with a score of {bs_score}/110 and similar timing.")
            
            progress_bar.progress(100)
            status_text.text("Comparison complete!")

# Add helpful information in the sidebar
with st.sidebar:
    st.subheader("How to Use")
    st.markdown("""
    1. Enter a website URL above
    2. Click "Compare Crawlers" to analyze
    3. Review the performance metrics for each crawler
    4. Use the recommendation to decide which crawler to use for your SEO analysis
    """)
    
    st.subheader("Evaluation Metrics")
    st.markdown("""
    - **Title Quality**: How well the title is extracted
    - **Meta Description**: Quality of meta description extraction
    - **Headings**: Number and quality of headings
    - **Content**: Amount and quality of content extracted
    - **Additional Elements**: Links, images, and alt text
    - **Performance**: Speed of extraction
    """)