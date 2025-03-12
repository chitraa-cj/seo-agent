

# SEO Agent MVP

## Overview
SEO Agent MVP is a simple SEO analysis tool built with Streamlit. It allows users to analyze web pages for basic on-page SEO factors and provides recommendations. The project uses OpenAI's API to enhance SEO analysis.

## Features
- **User Authentication**: Simple login/registration system (future implementation)
- **URL Input & Processing**: Validates and extracts web page content
- **On-Page SEO Analysis**:
  - Title tag analysis
  - Meta description evaluation
  - Heading structure assessment
  - Content keyword density and readability
  - Image optimization checks
  - URL structure evaluation
- **Results Storage**: Save and retrieve past analysis reports
- **Integration**: Uses OpenAI API for AI-powered insights

## Tech Stack
- **Frontend**: Streamlit
- **Backend**: Python (FastAPI for future implementation)
- **External Services**: OpenAI API, Google PageSpeed Insights (future integration)
- **Containerization**: Docker & Docker Compose

---

## Setup Instructions

### 1. Clone the Repository
```sh
git clone https://github.com/your-repo/seo-agent.git
cd seo-agent
```

### 2. Set Up the Environment

#### Using Conda (Recommended)
```sh
conda create -p venv python=3.10 -y
conda activate venv
pip install -r requirements.txt
```

#### Using Virtualenv
```sh
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

### 3. Configure Environment Variables
Create a `.env` file in the **project root** and add your OpenAI API key:
```ini
OPENAI_API_KEY=your_openai_api_key_here
```
Alternatively, copy the `.env.example` file and modify it:
```sh
cp .env.example .env
```

---

### 4. Run the Application Locally
```sh
streamlit run src/app.py
```
- The app runs at `http://localhost:8501`.

---

## Docker Instructions

### **1. Run Using Docker Compose (Recommended)**
```sh
docker-compose up --build
```
- **Builds the container**
- **Loads the `.env` file**
- **Runs the app on `http://localhost:8501`**

To stop the container:
```sh
docker-compose down
```

---

### **2. Manually Build & Run the Docker Image (Alternative)**
```sh
docker build -t seo-agent .
docker run --env-file .env -p 8501:8501 seo-agent
```

---

## Common Issues & Fixes

### 1. **API Key Not Found Error**
- Ensure you have a `.env` file with the correct `OPENAI_API_KEY`
- Pass the `.env` file when running Docker:
  ```sh
  docker run --env-file .env -p 8501:8501 seo-agent
  ```

### 2. **OpenAI API Error (`ChatCompletion` Not Found)**
- Update your code to use the latest OpenAI API syntax:
```python
import openai
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```
```

