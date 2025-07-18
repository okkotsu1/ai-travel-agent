# hotel_scraper.py

import time
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

def _apply_four_plus_rating_filter(driver):
    """Click the '4+ rating' chip and wait until hotel list refreshes."""
    try:
        old_results = driver.find_elements(By.CLASS_NAME, "K1smNd")
        old_count = len(old_results)

        rating_chip = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//span[text()="4+ rating" and contains(@class, "m1GHmf")]/ancestor::button'
            ))
        )
        driver.execute_script("arguments[0].click();", rating_chip)
        print("[INFO] Clicked on '4+ rating' filter chip.")

        # Wait until the hotel list refreshes with new results
        WebDriverWait(driver, 15).until(
            lambda d: len(d.find_elements(By.CLASS_NAME, "K1smNd")) != old_count
        )
        print("[INFO] Hotel list updated after applying filter.")
        time.sleep(1)
    except Exception as e:
        print(f"[WARN] Could not apply '4+ rating' filter: {e}")

def scrape_google_hotels(location_name: str, max_hotels: int = 5, currency: str = "USD"):
    options = ChromeOptions()
    # options.add_argument("--headless=new")  # Uncomment for headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    base_url = f"https://www.google.com/travel/hotels/{location_name}?q={location_name}&currency={currency}"
    print(f"[INFO] Loading URL: {base_url}")
    driver.get(base_url)

    try:
        driver.find_element(By.XPATH, '//button[contains(@aria-label, "Accept")]').click()
    except NoSuchElementException:
        pass

    # Apply the "4+ rating" filter BEFORE we start scraping.
    _apply_four_plus_rating_filter(driver)

    # Wait until at least one hotel card is visible after applying the filter.
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "K1smNd")))

    hotel_data = []
    unique_hotels = set()
    page_index = 0
    next_page_available = True

    while next_page_available and len(hotel_data) < max_hotels and page_index < 3:
        soup = BeautifulSoup(driver.page_source, "lxml")
        hotel_cards = soup.find_all("div", class_="BcKagd")
        print(f"🧪 Found {len(hotel_cards)} hotel cards on page {page_index + 1}")

        for hotel in hotel_cards:
            if len(hotel_data) >= max_hotels:
                next_page_available = False
                break

            name_tag = hotel.find("h2", class_="BgYkof")
            price_tag = hotel.find("span", class_="qQOQpe prxS3d")
            rating_tag = hotel.find("span", class_="KFi5wf lA0BZ")
            link_tag = hotel.find("a", class_="PVOOXe")
            if not link_tag:
                continue

            name = name_tag.text if name_tag else "N/A"
            price = price_tag.text if price_tag else "N/A"
            rating = rating_tag.text if rating_tag else "N/A"
            detail_relative_link = link_tag.get("href")

            driver.get("https://www.google.com" + detail_relative_link)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "gJGKuf")))

            try:
                location = driver.find_element(By.XPATH, '//div[@class="K4nuhf"]/span[1]').text
                contact  = driver.find_element(By.XPATH, '//div[@class="K4nuhf"]/span[3]').text
            except NoSuchElementException:
                location = "N/A"
                contact  = "N/A"

            checkin_time  = "N/A"
            checkout_time = "N/A"
            try:
                details_block = driver.find_element(By.CLASS_NAME, "gJGKuf").text
                for line in details_block.split("\n"):
                    if "Check-in" in line:
                        checkin_time = line.strip()
                    if "Check-out" in line:
                        checkout_time = line.strip()
            except Exception:
                pass

            external_link = "N/A"
            try:
                site_btn = driver.find_element(
                    By.XPATH,
                    '//a[contains(@aria-label, "Visit site") and @href]'
                )
                external_link = site_btn.get_attribute("href")
            except NoSuchElementException:
                detail_soup = BeautifulSoup(driver.page_source, "lxml")
                ext_tag = detail_soup.find("a", class_="WpHeLc")
                if ext_tag and ext_tag.get("href"):
                    external_link = ext_tag["href"]

            driver.back()
            time.sleep(1)

            hotel_id = (name, price, rating, location, contact)
            if hotel_id not in unique_hotels:
                unique_hotels.add(hotel_id)
                hotel_data.append({
                    "Name":      name,
                    "Price":     price,
                    "Rating":    rating,
                    "Location":  location,
                    "Contact":   contact,
                    "Checkin":   checkin_time,
                    "Checkout":  checkout_time,
                    "Website":   external_link,
                })
                print(f"✅ Scraped hotel: {name}")

        if next_page_available and len(hotel_data) < max_hotels:
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "K1smNd")))
                next_btn = driver.find_element(
                    By.XPATH,
                    '//div[@class="eGUU7b"]/button[2]' if page_index > 0 else '//div[@class="eGUU7b"]/button'
                )
                next_btn.click()
                page_index += 1
            except NoSuchElementException:
                print("ℹ️ No next button found.")
                next_page_available = False

    driver.quit()
    return hotel_data

if __name__ == "__main__":
    results = scrape_google_hotels("london", max_hotels=5)
    for h in results:
        print(h)
