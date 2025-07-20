import os
import json
import re
import time
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

OUTPUT_FILE = "scraped_data/flight_search.json"
MAX_FLIGHTS = 3

def safe_print(msg):
    try:
        print(msg.encode("ascii", "ignore").decode("ascii"), flush=True)
    except Exception as e:
        print(f"[print error] {e}", flush=True)

def scrape_google_flights(url):
    os.makedirs("scraped_data", exist_ok=True)
    results = []

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=chrome_options)
    driver.get(url)
    safe_print(f"[INFO] Opened URL: {url}")

    time.sleep(10)  # Let the page load

    try:
        cards = driver.find_elements(By.CSS_SELECTOR, "li.pIav2d")
        safe_print(f"[INFO] Found {len(cards)} flight cards")

        for i, card in enumerate(cards[:MAX_FLIGHTS]):
            html = card.get_attribute("innerHTML")
            soup = BeautifulSoup(html, "html.parser")

            airline_tag = soup.select_one("div.sSHqwe")
            airline = airline_tag.get_text(strip=True) if airline_tag else "N/A"

            price_tag = (
                soup.select_one("div.BVAVmf span.YMlIz") or
                soup.select_one("div.U3gSDe span") or
                soup.select_one("div.FpEdX span")
            )
            price = price_tag.get_text(strip=True) if price_tag else "N/A"

            duration_tag = soup.select_one("div.gvkrdb.AdWm1c.tPgKwe.ogfYpf")
            duration = duration_tag.get_text(strip=True) if duration_tag else "N/A"

            dep_arr_label = soup.select_one("span.mv1WYe")
            departure_time = arrival_time = "N/A"
            if dep_arr_label and dep_arr_label.has_attr("aria-label"):
                full_text = dep_arr_label["aria-label"]
                dep_match = re.search(r"at (\d{1,2}:\d{2} ?[AP]M)", full_text)
                arr_match = re.search(r"arrives at .*? at (\d{1,2}:\d{2} ?[AP]M)", full_text)
                if dep_match:
                    departure_time = dep_match.group(1)
                if arr_match:
                    arrival_time = arr_match.group(1)

            results.append({
                "flight_index": i,
                "airline": airline,
                "price": price,
                "duration": duration,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "google_flight_card_url": url,
                "booking_link": "N/A"
            })

            safe_print(f"✅ [{i+1}] {airline}, {departure_time} → {arrival_time}, {duration}, {price}")

    except Exception as e:
        safe_print(f"[❌] Failed to scrape flights: {e}")
    finally:
        driver.quit()

    if results:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        safe_print(f"\n✅ Saved {len(results)} flights to {OUTPUT_FILE}")
    else:
        safe_print("\n❌ No flights extracted.")

if __name__ == "__main__":
    test_url = "https://www.google.com/travel/flights?q=one+way+flight+from+Delhi+to+London"
    safe_print(f"\n✈ Starting flight scrape: Delhi → London")
    scrape_google_flights(test_url)
