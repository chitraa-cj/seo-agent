# Use an official lightweight Python image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy only requirements first to leverage Docker's caching
COPY requirements.txt .

# Install dependencies before copying the rest of the code
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the Streamlit default port
EXPOSE 8501

# Set environment variable to indicate Docker
ENV DOCKER_RUNNING=1

# Run the Streamlit app
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
