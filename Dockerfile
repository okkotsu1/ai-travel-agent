# Base image
FROM python:3.10-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y \
    curl wget unzip gnupg xvfb \
    libnss3 libxss1 libappindicator3-1 libasound2 \
    libatk-bridge2.0-0 libgtk-3-0 libgbm-dev chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app
COPY . /app

# Create required folder explicitly
RUN mkdir -p /app/scraped_data

# Install Python dependencies
RUN pip install --upgrade pip \
 && pip install streamlit \
 && pip install -r requirements.txt \
 && pip install playwright && playwright install --with-deps

# Expose Streamlit default port
EXPOSE 8501

# CMD
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
