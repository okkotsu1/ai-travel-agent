# ✅ Use Playwright base image with Chromium and all dependencies pre-installed
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# ✅ Environment setup (keys injected via Railway dashboard)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ✅ Set working directory
WORKDIR /app

# ✅ Copy project files into the container
COPY . /app

# ✅ Create required folders
RUN mkdir -p /app/scraped_data

# ✅ Install Python dependencies
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install streamlit

# ✅ Install Playwright browser binaries
RUN playwright install --with-deps

# ✅ Expose Streamlit port
EXPOSE 8501

# ✅ Start Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
