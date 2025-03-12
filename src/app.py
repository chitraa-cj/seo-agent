import streamlit as st
import openai
import os
from dotenv import load_dotenv

# Load .env only if not running in Docker
if not os.getenv("DOCKER_RUNNING"):
    load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
if api_key:
    client = openai.OpenAI(api_key=api_key)  # Correct for openai>=1.0.0
else:
    client = None

st.title("SEO AI Agent - OpenAI API Test")

prompt = st.text_area("Enter a prompt:", "Analyze SEO factors for a sample webpage.")

if st.button("Test OpenAI API"):
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an SEO expert."},
                    {"role": "user", "content": prompt},
                ]
            )
            st.success("API Key is working!")
            st.write(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.error("API key not found. Make sure to set it in the .env file.")
