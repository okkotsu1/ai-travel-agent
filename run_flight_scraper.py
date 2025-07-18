

import sys
import asyncio
from datetime import datetime
import os
from flight_scraper import scrape_google_flights


# ----------------------------------------------------------------------
def print_flush(msg: str) -> None:
    """Print immediately, stripping non‑ASCII to avoid Windows console issues."""
    try:
        print(msg.encode("ascii", "ignore").decode("ascii"), flush=True)
    except Exception as e:
        print(f"[print error] {e}", flush=True)


def normalise_date_to_month_day(raw: str) -> str:
    """
    Convert many common date strings to 'July+28' (no year) so the final
    URL looks like:
         …flights?q=one+way+flight+from+Delhi+to+Boston+on+July+28
    Google Flights interprets that as the next occurrence of that date.
    """
    raw = raw.replace(",", "").strip()
    patterns = [
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y",
        "%d-%b-%Y", "%d %b %Y", "%d-%B-%Y", "%d %B %Y",
        "%d-%b", "%d %b", "%d-%B", "%d %B",
        "%b %d", "%B %d",
    ]

    for fmt in patterns:
        try:
            dt = datetime.strptime(raw, fmt)
            return f"{dt.strftime('%B')}+{dt.day}"   # drop the year
        except ValueError:
            continue

    # Last‑ditch: replace spaces so the query doesn’t break
    return raw.replace(" ", "+")


# ----------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print_flush(
            "Usage: python run_flight_scraper.py <origin> <destination> [<flight‑date>]"
        )
        sys.exit(1)

    origin, destination = sys.argv[1], sys.argv[2]
    raw_date = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""

    # Build the Google‑Flights query URL
    if raw_date:
        date_token = normalise_date_to_month_day(raw_date)
        url = (
            "https://www.google.com/travel/flights?"
            f"q=one+way+flight+from+{origin}+to+{destination}+on+{date_token}"
        )
        print_flush(f"[INFO] Date token used in URL: {date_token}")
    else:
        url = (
            "https://www.google.com/travel/flights?"
            f"q=one+way+flight+from+{origin}+to+{destination}"
        )

    print_flush(f"Starting flight scrape: {origin} → {destination}")
    print_flush(f"[DEBUG] Using URL: {url}")

    # ------------------------------------------------------------------
    try:
        asyncio.run(scrape_google_flights(url))
        print_flush("✅ scrape_google_flights() returned successfully")

        if os.path.exists("scraped_data/flight_search.json"):
            print_flush("✅ Flight data file created.")
        else:
            print_flush("❌ scrape_google_flights() did not write output file!")

    except Exception as e:
        print_flush(f"❌ Exception occurred during scraping: {e}")
