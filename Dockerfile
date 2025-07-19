# ✅ Use Playwright base image with Chromium and all dependencies pre-installed
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# ✅ Set environment variables (including API keys)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GROQ_API_KEY=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 \
    SERPER_API_KEY=b4bc84312082b76ab4d784781be205a2d975b73 \
    OPENAI_API_KEY=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 \
    OPENROUTER_API_KEY=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

# ✅ Set working directory
WORKDIR /app

# ✅ Copy project files
COPY . /app

# ✅ Create necessary folders
RUN mkdir -p /app/scraped_data

# ✅ Install Python dependencies
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install streamlit

# ✅ Install Playwright browser binaries
RUN playwright install --with-deps

# ✅ Expose Streamlit port
EXPOSE 8501

# ✅ Run the Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
