import asyncio
import json
import os
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

def safe_print(msg):
    try:
        safe_msg = msg.encode("ascii", "ignore").decode("ascii")
        print(safe_msg, flush=True)
    except Exception as e:
        print(f"[print error] {e}", flush=True)

OUTPUT_FILE = "scraped_data/flight_search.json"
MAX_FLIGHTS = 3

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
                "--disable-gpu"
            ]
        )

        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(original_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector("li.pIav2d", timeout=30000)
        except Exception as e:
            safe_print(f"[❌] Initial page load failed: {e}")
            await browser.close()
            return

        flight_cards = await page.locator("li.pIav2d").all()
        safe_print(f"[INFO] Found {len(flight_cards)} flights. Scraping first {min(len(flight_cards), MAX_FLIGHTS)}...")

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

        # Visit each flight for booking link
        for flight in results:
            try:
                index = flight["flight_index"]
                card = page.locator("li.pIav2d").nth(index)
                await card.scroll_into_view_if_needed()

                old_url = page.url
                await card.click()
                await page.wait_for_timeout(3000)

                for _ in range(8):
                    await page.wait_for_timeout(1000)
                    if page.url != old_url:
                        break

                flight_card_url = page.url
                flight["google_flight_card_url"] = flight_card_url
                safe_print(f"[🛬] Opened flight card for flight {index+1}")
                safe_print(f"🔗 Google Flights card URL: {flight_card_url}")

                final_booking_url = "N/A"
                clk_redirect_url = "N/A"
                new_page = None

                def on_new_page(page_obj):
                    nonlocal new_page
                    new_page = page_obj

                context.on("page", on_new_page)

                try:
                    continue_btns = page.get_by_role("button", name=re.compile(r"^Continue to book with "))
                    first_btn = continue_btns.nth(0)
                    await first_btn.wait_for(timeout=10000)
                    await first_btn.scroll_into_view_if_needed()
                    await first_btn.click(force=True)
                    safe_print("✅ Clicked 'Continue to book' button")

                    await page.wait_for_timeout(8000)

                    if new_page:
                        await new_page.wait_for_load_state("load")
                        clk_redirect_url = new_page.url
                        safe_print(f"🔁 Intermediate clk URL: {clk_redirect_url}")

                        for _ in range(10):
                            await new_page.wait_for_timeout(1000)
                            if "google.com" not in new_page.url:
                                final_booking_url = new_page.url
                                break

                        await new_page.close()
                    else:
                        if "google.com" not in page.url:
                            final_booking_url = page.url
                        else:
                            safe_print("⚠️ Booking link not found — still on Google.")

                    flight["booking_link"] = final_booking_url
                    safe_print(f"🌍 Booking link: {final_booking_url}")

                except Exception as e:
                    safe_print(f"[⚠️] Could not complete booking link flow: {e}")

                finally:
                    context.off("page", on_new_page)

                # Go back to flight list
                safe_print("🔁 Reloading original flight list page...")
                await page.goto(original_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector("li.pIav2d", timeout=20000)
                flight_cards = await page.locator("li.pIav2d").all()
                safe_print("✅ Reloaded flight list")

            except Exception as e:
                safe_print(f"[❌] Failed to process flight {flight['flight_index']+1}: {e}")
                safe_print("🔁 Attempting reload...")
                await page.goto(original_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector("li.pIav2d", timeout=20000)
                flight_cards = await page.locator("li.pIav2d").all()
                safe_print("✅ Reloaded flight list")

        await browser.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        safe_print(f"\n[✅] Saved {len(results)} flights to {OUTPUT_FILE}")

async def main():
    urls = [
        "https://www.google.com/travel/flights?q=one+way+flight+from+Delhi+to+Boston+on+July+28"
    ]
    for url in urls:
        safe_print(f"\n🔗 Scraping: {url}")
        await scrape_google_flights(url)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
