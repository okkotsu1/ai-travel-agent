# ✈️ AI Travel Agent

An intelligent multi-agent travel planning system powered by **CrewAI**, **LangChain**, and **Groq's LLaMA 3**. Just describe your trip in plain English — the system handles flights, hotels, and sightseeing itineraries autonomously.

---

## 🧠 How It Works

The system uses a **multi-agent architecture** where three specialized AI agents collaborate to plan your trip end-to-end:

| Agent | Role |
|---|---|
| ✈️ **Flight Planner** | Finds and recommends best flight options based on cost, duration, and layovers |
| 🏨 **Hotel Advisor** | Suggests hotels with competitive pricing, good reviews, and proximity to attractions |
| 🗺️ **Tour Guide** | Designs a day-wise sightseeing itinerary with local tips and hidden gems |

### Pipeline

```
User Prompt (natural language)
        │
        ▼
  NLP Parser (LLaMA 3 via Groq)
  → Extracts: origin, destination, dates, needs
        │
        ▼
  Data Fetchers
  ├── Flight Scraper (Playwright + Google Flights)
  ├── Hotel Scraper (Selenium + BeautifulSoup + Google Hotels)
  └── Tour Search (Serper API)
        │
        ▼
  CrewAI Agents process the scraped data
        │
        ▼
  Streamlit UI displays the full travel plan
```

---

## 🚀 Features

- **Natural language input** — describe your trip the way you'd tell a friend
- **Real-time flight scraping** from Google Flights via Playwright
- **Live hotel data** scraped from Google Hotels via Selenium + BeautifulSoup
- **Web search** for attractions and local tips via Serper API
- **Multi-agent reasoning** — each agent is domain-specialized and works with real scraped data
- **Streamlit UI** for an interactive, user-friendly experience
- **Dockerized** for easy deployment

---

## 🛠️ Tech Stack

- **AI / Agents:** CrewAI, LangChain, LangChain-Groq
- **LLM:** LLaMA 3 70B (via Groq API)
- **Web Scraping:** Playwright, Selenium, BeautifulSoup4, lxml
- **Search:** Serper API (via `crewai-tools`)
- **Frontend:** Streamlit
- **Infra:** Docker, Python-dotenv

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- Docker (optional)
- API keys for Groq and Serper

### 1. Clone the repo

```bash
git clone https://github.com/okkotsu1/ai-travel-agent.git
cd ai-travel-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Set up environment variables

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key
SERPER_API_KEY=your_serper_api_key
```

### 4. Run the app

```bash
streamlit run streamlit_app.py
```

---

## 🐳 Docker

```bash
docker build -t ai-travel-agent .
docker run -p 8501:8501 --env-file .env ai-travel-agent
```

---

## 💬 Example Usage

> *"I want to fly from Delhi to Paris between August 10–15, need a hotel near the Eiffel Tower, and want a 3-day sightseeing plan."*

The system will:
1. Parse your intent (flight + hotel + tour needed)
2. Scrape real flight options from Google Flights
3. Scrape hotel listings from Google Hotels
4. Search for top Paris attractions
5. Run all three agents and return a complete travel plan

---

## 📁 Project Structure

```
ai-travel-agent/
├── streamlit_app.py       # Main UI
├── agents.py              # CrewAI agent definitions
├── tasks.py               # Task definitions for each agent
├── tools.py               # Scraper orchestration & Serper tool
├── nlp_parser.py          # LLM-based intent extraction
├── flight_scraper.py      # Playwright-based Google Flights scraper
├── hotel_scraper.py       # Selenium-based Google Hotels scraper
├── run_flight_scraper.py  # Subprocess entry point for flight scraping
├── universal_llm.py       # LLM provider abstraction
├── Dockerfile
├── Pipfile
└── requirements.txt
```

---

## 🔑 API Keys

| Key | Where to get it |
|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev) |

---

## 📄 License

MIT License — feel free to use, modify, and build on this.
