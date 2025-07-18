import os
import json
import sys
import asyncio
import subprocess
from hotel_scraper import scrape_google_hotels
from crewai_tools import SerperDevTool


OUTPUT_DIR = "scraped_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

search_web_tool = SerperDevTool()

def fetch_and_save(query, filename):
    result = search_web_tool.run(search_query=query)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"[INFO] Saved result to {filepath}")

def run_flight_scraper_async(origin, destination):
    python_path = sys.executable
    script = os.path.abspath("run_flight_scraper.py")

    print(f"[INFO] Launching flight scraper subprocess for {origin} → {destination}")

    try:
        result = subprocess.run(
            [python_path, script, origin, destination],
            capture_output=True,
            text=True,
            check=True
        )

        print("[INFO] Flight scraping complete:")
        print("[STDOUT]\n", result.stdout)
        print("[STDERR]\n", result.stderr)

        if os.path.exists("scraped_data/flight_search.json"):
            print("✅ Flight data file created.")
        else:
            print("❌ Flight data file not created.")

    except subprocess.CalledProcessError as e:
        print(f"[SUBPROCESS ERROR]\n{e.stderr}")
    except Exception as e:
        print(f"[ERROR] Unexpected issue in scraper subprocess: {e}")


def fetch_all_needed(parsed):
    origin = parsed["origin"]
    destination = parsed["destination"]

    if parsed["needs_flight"]:
        print(f"✈️ Scraping flights from {origin} to {destination} via Playwright")
        run_flight_scraper_async(origin, destination)

    if parsed["needs_hotel"]:
        print(f"🏨 Scraping hotels for: {destination}")
        hotel_list = scrape_google_hotels(destination, max_hotels=5)
        filepath = os.path.join(OUTPUT_DIR, "hotel_search.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(hotel_list, f, indent=2)
        print(f"✅ Hotel data saved to {filepath}")

    if parsed["needs_tour"]:
        fetch_and_save(
            f"top attractions in {destination} hidden gems local tips",
            "tour_search.json"
        )
