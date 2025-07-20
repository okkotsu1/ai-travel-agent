import asyncio
import json
import os
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError

OUTPUT_FILE = "scraped_data/flight_search.json"
MAX_FLIGHTS = 3

def safe_print(msg):
    try:
        print(msg.encode("ascii", "ignore").decode("ascii"), flush=True)
    except Exception as e:
        print(f"[print error] {e}", flush=True)

async def scrape_google_flights(url):
    results = []
    os.makedirs("scraped_data", exist_ok=True)
    original_url = url

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        context = await browser.new_context()
        page = await context.new_page()

        try:
            safe_print(f"\n[DEBUG] Navigating to: {original_url}")
            await page.goto(original_url, wait_until="domcontentloaded", timeout=60000)

            # Dump HTML + screenshot before waiting
            html = await page.content()
            with open("scraped_data/debug_flight_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            await page.screenshot(path="scraped_data/debug_flight_page.png")
            safe_print("[DEBUG] Dumped page HTML and screenshot.")

            # Wait for flight cards (or change selector based on dumped file)
            await page.wait_for_selector("li.pIav2d", timeout=30000)
            flight_cards = await page.locator("li.pIav2d").all()
            safe_print(f"[INFO] Found {len(flight_cards)} flights.")

            for i in range(min(len(flight_cards), MAX_FLIGHTS)):
                try:
                    card = flight_cards[i]
                    await card.scroll_into_view_if_needed()
                    html = await card.inner_html()
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
                        "google_flight_card_url": "N/A",
                        "booking_link": "N/A"
                    })

                    safe_print(f"✅ [{i+1}] {airline}, {departure_time} → {arrival_time}, {duration}, {price}")
                except Exception as e:
                    safe_print(f"[⚠️] Failed to parse flight {i+1}: {e}")

        except TimeoutError as e:
            safe_print(f"\n❌ Initial page load failed: {e}\n")
        except Exception as e:
            safe_print(f"\n❌ Unexpected error: {e}\n")
        finally:
            await browser.close()

    # Save only if results were fetched
    if results:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        safe_print(f"\n✅ Saved {len(results)} flights to {OUTPUT_FILE}")
    else:
        safe_print("\n❌ No flight data collected — check debug_flight_page.html and .png")

async def main():
    urls = [
        "https://www.google.com/travel/flights?q=one+way+flight+from+Delhi+to+London"
    ]
    for url in urls:
        safe_print(f"\n✈ Starting flight scrape: {url}")
        await scrape_google_flights(url)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
