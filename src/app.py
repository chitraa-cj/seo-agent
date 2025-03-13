import streamlit as st
import openai
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

if not os.getenv("DOCKER_RUNNING"):
    load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    client = openai.OpenAI(api_key=api_key)
else:
    client = None

st.title("SEO AI Agent")
st.subheader("Get an AI-generated On-Page SEO report for your website")

niche = st.text_input("Enter your website's niche:")
tagline = st.text_input("Enter your website's tagline:")
website_url = st.text_input("Enter your website URL:")

def fetch_website_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        title = soup.title.string if soup.title else "No title found"
        meta_description = (
            soup.find("meta", attrs={"name": "description"})
            or soup.find("meta", attrs={"property": "og:description"})
        )
        meta_description = meta_description["content"] if meta_description else "No meta description found"

        headings = [h.get_text() for h in soup.find_all(["h1", "h2", "h3"])]
        paragraphs = [p.get_text() for p in soup.find_all("p")]
        content = " ".join(headings + paragraphs)[:3000]  # Limit text size

        return {
            "title": title,
            "meta_description": meta_description,
            "headings": headings[:5],  # Limit number of headings
            "content": content
        }

    except Exception as e:
        return {"error": f"Error fetching website content: {e}"}

if st.button("Generate On-Page SEO Report"):
    if not website_url.startswith("http"):
        st.error("Please enter a valid URL starting with http or https")
    else:
        website_data = fetch_website_content(website_url)
        
        if "error" in website_data:
            st.error(website_data["error"])
        elif client:
            try:
                prompt = (
                    f"Analyze the On-Page SEO of a website with the following details:\n"
                    f"Niche: {niche}\nTagline: {tagline}\n\n"
                    f"Title: {website_data['title']}\n"
                    f"Meta Description: {website_data['meta_description']}\n"
                    f"Headings: {', '.join(website_data['headings'])}\n"
                    f"Content Snippet: {website_data['content'][:1000]}\n\n"
                    f"Provide a detailed On-Page SEO analysis including:\n"
                    f"- Title tag optimization\n"
                    f"- Meta description effectiveness\n"
                    f"- Heading structure (H1, H2, H3 usage)\n"
                    f"- Keyword density and relevance\n"
                    f"- Internal linking suggestions."
                )
                
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an advanced SEO expert."},
                        {"role": "user", "content": prompt},
                    ]
                )

                st.subheader("On-Page SEO Report:")
                st.write(response.choices[0].message.content)

            except Exception as e:
                st.error(f"Error generating On-Page SEO report: {e}")
        else:
            st.error("API key not found. Make sure to set it in the .env file.")
